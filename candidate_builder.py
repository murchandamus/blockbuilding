from itertools import chain, combinations

import utils
import getopt
import heapq
import json
import logging
import math
import sys
import time

from abstract_builder import Blockbuilder
from mempool import Mempool
from transaction import Transaction
from cluster import Cluster
from candidateset import CandidateSet


def main(argv):
    mempoolfilepath = ''
    try:
        opts, args = getopt.getopt(argv, "hm:", ["mempoolfile="])
    except getopt.GetoptError:
        print ('blockbuilder.py -m <mempoolfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('blockbuilder.py -m <mempoolfile>')
            sys.exit()
        elif opt in ("-m", "--mempoolfile"):
            mempoolfilepath = arg
        print ('Mempool file is "', mempoolfilepath)

    if mempoolfilepath == '':
        print ('Missing mempool file path: blockbuilder.py -m <mempoolfile>')
        sys.exit(2)

    startTime = time.time()
    mempool = Mempool()
    mempool.fromTXT(mempoolfilepath)
    bb = CandidateSetBlockbuilder(mempool)
    bb.buildBlockTemplate()
    bb.outputBlockTemplate(mempool.blockId)
    endTime = time.time()
    logging.info('main() elapsed time: ' + str(endTime - startTime))


class CandidateSetBlockbuilder(Blockbuilder):


    def __init__(self, mempool, weightLimit=3992820):
        self.mempool = mempool
        self.refMempool = Mempool()
        self.refMempool.fromDict(mempool.txs, False) # No need to backfill
        self.selectedTxs = []
        self.txsToBeClustered = {} # Bucket for transactions from used cluster
        self.clusters = {}  # Maps representative txid to cluster
        self.clusterHeap = [] # Heapifies clusters by bestCandidateSet
        self.txClusterMap = {}  # Maps txid to its cluster
        # block limit is 4M weight units minus header of 80 bytes and coinbase of 700 wu
        # blockheaderSize = 4*80
        # coinbaseReserve = 700
        # It turns out that biggest .gbt is only 399280
        self.weightLimit = weightLimit
        self.availableWeight = self.weightLimit


    def cluster(self, weightLimit):
        startTime = time.time()
        if len(self.clusters) == 0:
            for txid, tx in self.mempool.txs.items():
                self.txsToBeClustered[txid] = tx
        for txid, tx in self.txsToBeClustered.items():
            if txid in self.txClusterMap.keys():
                continue
            logging.debug("Cluster tx: " + txid)
            localCluster = Cluster(tx, weightLimit)
            localClusterTxids = tx.getLocalClusterTxids()
            while len(localClusterTxids) > 0:
                nextTxid = localClusterTxids.pop()
                if nextTxid in localCluster.txs.keys():
                    continue
                nextTx = self.mempool.getTx(nextTxid)
                localCluster.addTx(nextTx)
                localClusterTxids += nextTx.getLocalClusterTxids()
            # Only calculate bestCandidateSet if the best feerate in clusters that bubbles to the top
            self.clusters[localCluster.representative] = localCluster
            for lct in localCluster.txs.keys():
                self.txClusterMap[lct] = localCluster.representative
            heapq.heappush(self.clusterHeap, localCluster)

        self.txsToBeClustered = {}
        endTime = time.time()
        logging.debug('cluster() elapsed time: ' + str(endTime - startTime))
        return self.clusters


    def popBestCandidateSet(self, weightLimit):
        # TODO: Don't cluster until an unclustered transaction bubbles up to highest feerate, then find that cluster and the corresponding champion
        logging.debug("Called popBestCandidateSet with weightLimit " + str(weightLimit))
        startTime = time.time()
        self.cluster(weightLimit)
        bestCluster = heapq.heappop(self.clusterHeap) if len(self.clusterHeap) else None
        bestCandidateSet = bestCluster.bestCandidate if bestCluster is not None else None
        if 0 == len(self.clusterHeap):
            # ensures bestCandidate of last cluster gets evaluated and included
            bestCandidateSet = bestCluster.getBestCandidateSet(weightLimit) if bestCluster is not None else None
        # If bestCandidateSet exceeds weightLimit, refresh bestCluster and get next best cluster
        while (bestCandidateSet is None or bestCandidateSet.get_weight() > weightLimit) and len(self.clusterHeap) > 0:
            # Update best candidate set in cluster with weight limit
            if bestCandidateSet is not None:
                logging.debug("bestCandidateSet " + str(bestCandidateSet) + " is over weight limit: " + str(weightLimit))
            if bestCluster.getBestCandidateSet(weightLimit) is None:
                # don't add bestCluster without candidateSet back to heap
                bestCluster = heapq.heappop(self.clusterHeap)
            else:
                # add refreshed bestCluster back to heap then get best
                bestCluster = heapq.heappushpop(self.clusterHeap, bestCluster)
            bestCandidateSet = bestCluster.bestCandidate

        if bestCandidateSet is not None and bestCandidateSet.get_weight() > weightLimit:
            bestCandidateSet = None

        logging.debug("best candidate from all clusters: " + str(bestCandidateSet))

        if bestCandidateSet is None:
            logging.debug("Block finished")
        else:
            # delink bestCandidateSet from remaining cluster
            bestCluster.removeCandidateSetLinks(bestCandidateSet)
            # remove cluster mapping for transactions in cluster
            for txid, tx in bestCluster.txs.items():
                self.txClusterMap.pop(txid)
                if txid in bestCandidateSet.txs.keys():
                    # remove bestCandidateSet from mempool
                    self.mempool.txs.pop(txid)
                else:
                    # stage other txs for clustering in mempool
                    self.txsToBeClustered[txid] = tx

            # delete modified cluster for recreation next round
            self.clusters.pop(bestCluster.representative)

        endTime = time.time()
        logging.debug('popBestCandidateSet() elapsed time: ' + str(endTime - startTime))
        return bestCandidateSet


    def buildBlockTemplate(self):
        startTime = time.time()
        logging.info("Building blocktemplate...")
        for txid, tx in self.mempool.txs.items():
            self.txsToBeClustered[txid] = tx
        self.cluster(self.weightLimit)

        while len(self.mempool.txs) > 0 and self.availableWeight > 0:
            logging.debug("Weight left: " + str(self.availableWeight))
            bestCandidateSet = self.popBestCandidateSet(self.availableWeight)
            if bestCandidateSet is None or len(bestCandidateSet.txs) == 0:
                break
            txsIdsToAdd = bestCandidateSet.get_topologically_sorted_txids() 
            logging.debug("txsIdsToAdd: " + str(txsIdsToAdd))
            self.selectedTxs.extend(txsIdsToAdd)
            self.availableWeight -= bestCandidateSet.get_weight()

        endTime = time.time()
        logging.info('buildBlockTemplate() elapsed time: ' + str(endTime - startTime))
        return self.selectedTxs


    def outputBlockTemplate(self, blockId="", result_dir="results/"):
        filePath = result_dir
        if blockId is not None and blockId != "":
            filePath += str(blockId) + '-'
        filePath += utils.get_timestamp()

        filePath += '.byclusters'
        with open(filePath, 'w') as output_file:
            logging.debug(self.selectedTxs)
            if len(self.selectedTxs) > 0:
                selected = CandidateSet({txid: self.refMempool.txs[txid] for txid in self.selectedTxs})
                output_file.write('CreateNewBlockByClusters(): fees ' + str(selected.get_fees()) +
                                  ' weight ' + str(selected.get_weight()) + ' size limit ' +
                                  str(self.weightLimit) +'\n')
            else:
                output_file.write('CreateNewBlockByClusters(): fees ' + '0' +
                                  ' weight ' + '0' + ' size limit ' +
                                  str(self.weightLimit) +'\n')

            for tx in self.selectedTxs:
                output_file.write(tx + '\n')
        output_file.close()


def getRepresentativeTxid(txids):
    txids.sort()
    return txids[0]


if __name__ == '__main__':
    main(sys.argv[1:])
