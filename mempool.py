import heapq
import json
import math
from pathlib import Path
import logging

from transaction import Transaction
from cluster import Cluster

# The Mempool class represents a transient state of what is available to be used in a blocktemplate
class Mempool():
    def __init__(self):
        self.txs = {}
        self.txsToBeClustered = {} # Bucket for transactions from used cluster
        self.clusters = {}  # Maps representative txid to cluster
        self.clusterHeap = [] # Heapifies clusters by bestCandidateSet
        self.txClusterMap = {}  # Maps txid to its cluster
        self.blockId = ''

    def fromDict(self, txDict, blockId = 'dictionary'):
        self.blockId = blockId
        for txid, tx in txDict.items():
            self.txs[txid] = tx
            self.txsToBeClustered[txid] = tx

    def fromJSON(self, filePath):
        txsJSON = {}
        with open(filePath, 'r') as import_file:
            self.blockId = Path(filePath).stem
            txsJSON = json.load(import_file)

            for txid in txsJSON.keys():
                tx = Transaction(
                    txid,
                    txsJSON[txid]["fee"] * math.pow(10,8),
                    txsJSON[txid]["weight"],
                    txsJSON[txid]["depends"],
                    txsJSON[txid]["spentby"]
                )
                self.txs[txid] = tx
                self.txsToBeClustered[txid] = tx
        import_file.close()

    def fromTXT(self, filePath, SplitBy=" "):
        logging.info("Loading mempool from " + filePath)
        with open(filePath, 'r') as import_file:
            self.blockId = Path(filePath).stem
            for line in import_file:
                if 'txid' in line:
                    continue
                line = line.rstrip('\n')
                elements = line.split(SplitBy)
                txid = elements[0]
                # children are not stored in this file type
                tx = Transaction(txid, int(elements[1]), int(elements[2]), elements[3:])
                self.txs[txid] = tx
                self.txsToBeClustered[txid] = tx
        import_file.close()
        logging.debug("Mempool loaded")
        # backfill children from parents
        logging.debug("Backfill children from parents...")
        actualParents = {}
        for tx in self.txs.values():
            nonParentAncestors = set()
            ancestors = tx.parents
            for p in tx.parents:
                nonParentAncestors.update(set(self.txs[p].parents).intersection(set(tx.parents)))
            actualParents[tx.txid] = list(set(tx.parents) - nonParentAncestors)
        logging.debug("Calculated all actual parents")

        for tx in self.txs.values():
            tx.parents = actualParents[tx.txid]
            for p in tx.parents:
                self.txs[p].children.append(tx.txid)
        logging.debug("children backfilled")
        logging.info(str(len(self.txs))+ " txs loaded")

    def getTx(self, txid):
        return self.txs[txid]

    def getTxs(self):
        return self.txs

    def cluster(self, weightLimit):
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
                nextTx = self.getTx(nextTxid)
                localCluster.addTx(nextTx)
                localClusterTxids += nextTx.getLocalClusterTxids()
            # Only calculate bestCandidateSet if the best feerate in clusters that bubbles to the top
            self.clusters[localCluster.representative] = localCluster
            for lct in localCluster.txs.keys():
                self.txClusterMap[lct] = localCluster.representative
            heapq.heappush(self.clusterHeap, localCluster)

        logging.debug('finished cluster building')
        self.txsToBeClustered = {}
        return self.clusters

    def popBestCandidateSet(self, weightLimit):
        logging.debug("Called popBestCandidateSet with weightLimit " + str(weightLimit))
        self.cluster(weightLimit)
        bestCluster = heapq.heappop(self.clusterHeap) if len(self.clusterHeap) else None
        bestCandidateSet = bestCluster.bestCandidate if bestCluster is not None else None
        if 0 == len(self.clusterHeap):
            # ensures bestCandidate of last cluster gets evaluated and included
            bestCandidateSet = bestCluster.getBestCandidateSet(weightLimit) if bestCluster is not None else None
        # If bestCandidateSet exceeds weightLimit, refresh bestCluster and get next best cluster
        while (bestCandidateSet is None or bestCandidateSet.getWeight() > weightLimit) and len(self.clusterHeap) > 0:
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

        if bestCandidateSet is not None and bestCandidateSet.getWeight() > weightLimit:
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
                    self.txs.pop(txid)
                else:
                    # stage other txs for clustering in mempool
                    self.txsToBeClustered[txid] = tx

            # delete modified cluster for recreation next round
            self.clusters.pop(bestCluster.representative)

        return bestCandidateSet

    def removeConfirmedTx(self, txid):
        for d in self.txs[txid].children:
            if d in self.txs.keys():
                if txid in self.txs[d].parents:
                    self.txs[d].parents.remove(txid)
        self.txs.pop(txid)

    def dropTx(self, txid):
        for p in self.txs[txid].parents:
            if p in self.txs.keys():
                if txid in self.txs[p].children:
                    self.txs[p].children.remove(txid)
        self.txs.pop(txid)
