import candidate_builder as csb
import ancestor_builder as asb
import utils

import argparse
import datetime
import time
import logging
import os
import random
import sys


"""
The Monthbuilder class manages the global context across blocks.

The flow of this class is roughly:
    1) Identify the starting height, set as current height
    ---
    2) Load the diffpool for the current height
    3) Merge txs from current mempool with the `globalMempool`, combining ancestry information
    4) Remove confirmed transactions from the `globalMempool`
    5) Instantiate a blockbuilder with a copy of the `globalMempool`
    6) Build block, add selected transactions to the `confirmed_txs`
    7) Increment height, repeat from 3)
"""
def main(argv):
    parser = argparse.ArgumentParser(description='Build an alternative blockchain from a sequence of mempools and blocks.')
    parser.add_argument('-a', '--asb', type=int, help='proportion of AncestorSetBlockbuilder being randomly chosen from sum of asb+csb', default=0, required=False)
    parser.add_argument('-c', '--csb', type=int, help='proportion of CandidateSetBlockbuilder being randomly chosen from sum of asb+csb', default=0, required=False)
    args = parser.parse_args()

    asb_proportion = 0
    csb_proportion = 0
    if (args.asb == 0 and args.csb == 0):
        print("Defaulting to ancestorset-based blockbuilding (`asb=1, csb=0`) since proportions were not specified")
        asb_proportion = 1
        csb_proportion = 0
    else:
        asb_proportion = args.asb
        csb_proportion = args.csb
        print("Blocks will be randomly drawn from (`asb= " + str(asb_proportion) + ", csb= " + str(csb_proportion) + "`)")

    month_builder_start_time = datetime.datetime.now()
    result_dir = 'results_' + utils.get_timestamp() + '_asb_' + str(asb_proportion) + '_csb_' + str(csb_proportion) + '/'
    os.mkdir(result_dir)
    logfile = result_dir + utils.get_timestamp() + '_monthbuilder.log'
    logging.basicConfig(filename=logfile, level=logging.INFO)
    logging.info("Starttime: " + month_builder_start_time.isoformat())

    logging.info("Making " + str(asb_proportion) + " ancestorset blocks per " + str(csb_proportion) + " candidateset blocks.")

    mb = Monthbuilder(".", result_dir)
    mb.loadCoinbaseSizes()

    while(True):
        mb.getNextBlockHeight()
        blockfileName = ''
        files = os.listdir(mb.pathToMonth)
        for f in files:
            if f.startswith(str(mb.height)):
                blockfileName = f.split('.')[0]
                break
        if blockfileName == '':
            logging.info('Height ' + str(mb.height) + ' not found, done')
            break
        logging.info("Starting block: " + blockfileName)
        startTime = time.time()
        mb.loadBlockMempool(blockfileName)
        mb.runBlockWithGlobalMempool(asb_proportion, csb_proportion)
        endTime = time.time()
        logging.info('building ' + blockfileName + ' elapsed time: ' + str(endTime - startTime))
    month_builder_end_time = datetime.datetime.now()
    logging.info("Endtime: " + month_builder_end_time + ', total elapsed time: ' + str(month_builder_start_time - month_builder_end_time))


class Monthbuilder():
    def __init__(self, monthPath, result_dir="results/"):
        self.pathToMonth = monthPath
        self.globalMempool = csb.Mempool()
        self.confirmed_txs = set()
        self.height = -1
        self.coinbaseSizes = {}
        self.result_dir = result_dir


    def removeSetOfTxsFromMempool(self, txsSet, mempool):
        try:
            for k in txsSet:
                mempool.dropTx(k)
        except KeyError:
            logging.error("tx to delete not found" + k)
        return mempool


    def loadBlockMempool(self, blockId):
        fileFound = 0
        for file in os.listdir(self.pathToMonth):
            if file.endswith(blockId+'.diffpool'):
                fileFound = 1
                blockMempool = csb.Mempool()
                blockMempool.fromTXT(os.path.join(self.pathToMonth, file))
                blockTxsSet = set(blockMempool.txs.keys())
                for k in blockMempool.txs.keys():
                    if (k in self.globalMempool.txs):
                        raise Exception(k + ' loaded from .diffpool, but already in globalMempool')
                    self.globalMempool.txs[k] = blockMempool.txs[k]
                self.globalMempool.backfill_relatives(self.confirmed_txs) # ensure that all ancestors, children and descendants are set after merging global and block mempool

                for k in set(self.globalMempool.txs.keys()).intersection(self.confirmed_txs):
                    self.globalMempool.removeConfirmedTx(k)
                self.globalMempool.fromDict(self.globalMempool.txs, blockId)

        logging.debug("Global Mempool after loading block: " + str(self.globalMempool.txs.keys()))

        if fileFound == 0:
            raise Exception("Diffpool for " + blockId + " not found")


    def loadCoinbaseSizes(self):
        for file in os.listdir(self.pathToMonth):
            if file.endswith('.coinbases'):
                with open(os.path.join(self.pathToMonth, file), 'r') as coinbaseSizes:
                    for line in coinbaseSizes:
                        lineItems = line.split(' ')
                        self.coinbaseSizes[int(lineItems[0])] = lineItems[1].rstrip('\n')
                coinbaseSizes.close()
        logging.debug("CoinbaseSizes: " + str(self.coinbaseSizes))
        if len(self.coinbaseSizes) == 0:
            raise Exception('Coinbase file not found, please run `preprocessing.py`')


    def runBlockWithGlobalMempool(self, asb_proportion=0, csb_proportion=1):
        startTime = time.time()
        coinbaseSizeForCurrentBlock = self.coinbaseSizes[self.height]
        logging.info("Current height: " + str(self.height))
        weightAllowance = 4000000 - int(coinbaseSizeForCurrentBlock)
        logging.debug("Current weightAllowance: " + str(weightAllowance))
        logging.debug("Global Mempool before BB(): " + str(self.globalMempool.txs.keys()))
        bbMempool = csb.Mempool()
        bbMempool.fromDict(self.globalMempool.txs)
        # After loading block mempool, store ancestors for each transaction in permanent field
        bbMempool.backfill_relatives(self.confirmed_txs)
        builder_type = ''
        builder = None
        if (random.randint(1, asb_proportion + csb_proportion) <= asb_proportion):
            builder_type = 'ASB'
            builder = asb.AncestorSetBlockbuilder(bbMempool, weightAllowance)
        else:
            builder_type = 'CSB'
            builder = csb.CandidateSetBlockbuilder(bbMempool, weightAllowance)
        logging.debug("Block Mempool after BB(): " + str(builder.mempool.txs.keys()))
        selectedTxs = builder.buildBlockTemplate()
        logging.debug("selectedTxs: " + str(selectedTxs))
        self.confirmed_txs = set(selectedTxs).union(self.confirmed_txs)
        builder.outputBlockTemplate(self.height, self.result_dir) # TODO: Height+blockhash?
        self.globalMempool.fromDict(bbMempool.txs)
        endTime = time.time()
        logging.info('runBlockWithGlobalMempool() [' + builder_type + '] elapsed time: ' + str(endTime - startTime))


    def getNextBlockHeight(self):
        ## Assume that there are mempool files in folder and they are prefixed with a _seven_ digit block height
        if self.height > 0:
            self.height = int(self.height) + 1
            return self.height
        else:
            dirContent = os.listdir(self.pathToMonth)
            onlymempool =  [f for f in dirContent if f.endswith('.mempool')]
            onlymempool.sort()
            if 0 == len(onlymempool):
                raise Exception("No mempool files found")
            self.height = int(onlymempool[0][0:6])
            return self.height

if __name__ == '__main__':
    main(sys.argv[1:])
