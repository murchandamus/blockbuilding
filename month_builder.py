import candidate_builder as csb
import ancestor_builder as asb
import utils

import argparse
import datetime
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
    6) Build block, add selected transactions to the `confirmedTxs`
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

    date_now = datetime.datetime.now()
    result_dir = 'results_' + utils.get_timestamp() + '_asb_' + str(asb_proportion) + '_csb_' + str(csb_proportion) + '/'
    os.mkdir(result_dir)
    logfile = result_dir + utils.get_timestamp() + '_monthbuilder.log'
    logging.basicConfig(filename=logfile, level=logging.INFO)
    logging.info("Starttime: " + date_now.isoformat())

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
        mb.loadBlockMempool(blockfileName)
        mb.runBlockWithGlobalMempool(asb_proportion, csb_proportion)

class Monthbuilder():
    def __init__(self, monthPath, result_dir="results/"):
        self.pathToMonth = monthPath
        self.globalMempool = csb.Mempool()
        self.confirmedTxs = set()
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
                    self.globalMempool.txs[k] = blockMempool.txs[k]
                self.globalMempool.backfill_relatives(self.confirmedTxs) # ensure that all ancestors, children and descendants are set after merging global and block mempool

                for k in list(self.globalMempool.txs.keys()):
                    if k in self.confirmedTxs:
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
        coinbaseSizeForCurrentBlock = self.coinbaseSizes[self.height]
        logging.info("Current height: " + str(self.height))
        weightAllowance = 4000000 - int(coinbaseSizeForCurrentBlock)
        logging.debug("Current weightAllowance: " + str(weightAllowance))
        logging.debug("Global Mempool before BB(): " + str(self.globalMempool.txs.keys()))
        bbMempool = csb.Mempool()
        bbMempool.fromDict(self.globalMempool.txs)
        # After loading block mempool, store ancestors for each transaction in permanent field
        bbMempool.store_same_block_ancestry()
        builder_chooser = random.randint(1, asb_proportion - 0 + (csb_proportion-0))
        builder = None
        if (builder_chooser <= asb_proportion):
            builder = asb.AncestorSetBlockbuilder(bbMempool, weightAllowance)
        else:
            builder = csb.CandidateSetBlockbuilder(bbMempool, weightAllowance)
        logging.debug("Block Mempool after BB(): " + str(builder.mempool.txs.keys()))
        selectedTxs = builder.buildBlockTemplate()
        logging.debug("selectedTxs: " + str(selectedTxs))
        self.confirmedTxs = set(selectedTxs).union(self.confirmedTxs)
        builder.outputBlockTemplate(self.height, self.result_dir) # TODO: Height+blockhash?
        self.globalMempool.fromDict(bbMempool.txs)

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
