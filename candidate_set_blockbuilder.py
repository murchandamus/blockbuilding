from itertools import chain, combinations
import datetime
import getopt
import heapq
import json
import math
from pathlib import Path
import sys
import time
import logging

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

    if mempoolfilepath is '':
        print ('Missing mempool file path: blockbuilder.py -m <mempoolfile>')
        sys.exit(2)

    startTime = time.time()
    mempool = Mempool()
    mempool.fromTXT(mempoolfilepath)
    bb = Blockbuilder(mempool)
    bb.buildBlockTemplate()
    bb.outputBlockTemplate(mempool.blockId)
    endTime = time.time()
    logging.info('Elapsed time: ' + str(endTime - startTime))

class CandidateSetBlockbuilder():
    def __init__(self, mempool, weightLimit=3992820):
        self.mempool = mempool
        self.refMempool = Mempool()
        self.refMempool.fromDict(mempool.txs)
        self.selectedTxs = []
        # block limit is 4M weight units minus header of 80 bytes and coinbase of 700 wu
        # blockheaderSize = 4*80
        # coinbaseReserve = 700
        # It turns out that biggest .gbt is only 399280
        self.weightLimit = weightLimit
        self.availableWeight = self.weightLimit

    def buildBlockTemplate(self):
        logging.info("Building blocktemplate...")
        while len(self.mempool.txs) > 0 and self.availableWeight > 0:
            logging.debug("Weight left: " + str(self.availableWeight))
            bestCandidateSet = self.mempool.popBestCandidateSet(self.availableWeight)
            if bestCandidateSet is None or len(bestCandidateSet.txs) == 0:
                break
            txsIdsToAdd = list(bestCandidateSet.txs.keys())
            while len(txsIdsToAdd) != 0:
                for txid in txsIdsToAdd:
                    if set(self.refMempool.txs[txid].parents).issubset(set(self.selectedTxs)):
                        self.selectedTxs.append(bestCandidateSet.txs[txid].txid)
                        txsIdsToAdd.remove(txid)
            self.availableWeight -= bestCandidateSet.getWeight()

        return self.selectedTxs

    def outputBlockTemplate(self, blockId=""):
        filePath = "results/"
        if blockId is not None and blockId != "":
            filePath += str(blockId) + '-'
        date_now = datetime.datetime.now()
        filePath += date_now.isoformat()

        filePath += '.byclusters'
        with open(filePath, 'w') as output_file:
            logging.debug(self.selectedTxs)
            if len(self.selectedTxs) > 0:
                selected = CandidateSet({txid: self.refMempool.txs[txid] for txid in self.selectedTxs})
                output_file.write('CreateNewBlockByClusters(): fees ' + str(selected.getFees()) +
                                  ' weight ' + str(selected.getWeight()) + ' size limit ' +
                                  str(self.weightLimit) +'\n')
            else:
                output_file.write('CreateNewBlockByClusters(): fees ' + '0' +
                                  ' weight ' + '0' + ' size limit ' +
                                  str(self.weightLimit) +'\n')

            for tx in self.selectedTxs:
                output_file.write(tx + '\n')
        output_file.close()



# A set of transactions that forms a unit and may be added to a block as is

def getRepresentativeTxid(txids):
    txids.sort()
    return txids[0]


if __name__ == '__main__':
    main(sys.argv[1:])
