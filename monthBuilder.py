import candidate_builder as bb
import os
import logging
from os.path import isfile, join

"""
The Monthbuilder class manages the global context across blocks.

The flow of this class is roughly:
    1) Load the `allowSet` which prevents that we include transactions that were superseded via RBF
    2) Identify the starting height, set as current height
    ---
    3) Add the mempool for the current height to the `globalMempool`, combining ancestry information
    4) Filter the `globalMempool` to unconfirmed transactions from the `allowSet`
    5) Instantiate one of the blockbuilders with a copy of the `globalMempool`, build block
    6) Add transactions selected for the block to the `confirmedTxs`
    7) Increment height, repeat from 3)
"""
class Monthbuilder():
    def __init__(self, monthPath):
        self.pathToMonth = monthPath
        self.globalMempool = bb.Mempool()
        self.allowSet = set()
        self.confirmedTxs = set()
        self.height = -1
        self.coinbaseSizes = {}

    def loadAllowSet(self):
        files = os.listdir(self.pathToMonth)
        for f in files:
            if f.endswith('.allow'):
                with open(os.path.join(self.pathToMonth, f), 'r') as import_allow_list:
                    for line in import_allow_list:
                        self.allowSet.add(line.rstrip('\n'))
                import_allow_list.close()
        if len(self.allowSet) == 0:
            raise ValueError('Allowed list empty, please run `preprocessing.py`')
        logging.debug('allowSet: ' + str(self.allowSet))

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
            if file.endswith(blockId+'.mempool'):
                fileFound = 1
                blockMempool = bb.Mempool()
                blockMempool.fromTXT(os.path.join(self.pathToMonth, file))
                blockTxsSet = set(blockMempool.txs.keys())
                txsToRemove = blockTxsSet.difference(self.allowSet)
                logging.debug("txsToRemove: " + str(txsToRemove))
                if len(txsToRemove) > 0:
                    logging.debug("block txs before pruning for allow set " + str(blockTxsSet))
                    blockMempool = self.removeSetOfTxsFromMempool(txsToRemove, blockMempool)
                    logging.debug("block txs after pruning for allow set " + str(blockMempool.txs.keys()))
                for k in blockMempool.txs.keys():
                    if k in self.globalMempool.txs:
                        blockMempool.txs[k].parents = set(self.globalMempool.txs[k].parents) | set(blockMempool.txs[k].parents)
                        blockMempool.txs[k].descendants = set(self.globalMempool.txs[k].descendants) | set(blockMempool.txs[k].descendants)

                    self.globalMempool.txs[k] = blockMempool.txs[k]
                for k in list(self.globalMempool.txs.keys()):
                    if k in self.confirmedTxs:
                        self.globalMempool.removeConfirmedTx(k)
                self.globalMempool.fromDict(self.globalMempool.txs, blockId)

        logging.debug("Global Mempool after loading block: " + str(self.globalMempool.txs.keys()))

        if fileFound == 0:
            raise Exception("Mempool not found")

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

    def runBlockWithGlobalMempool(self):
        coinbaseSizeForCurrentBlock = self.coinbaseSizes[self.height]
        logging.info("Current height: " + str(self.height))
        weightAllowance = 4000000 - int(coinbaseSizeForCurrentBlock)
        logging.debug("Current weightAllowance: " + str(weightAllowance))
        logging.debug("Global Mempool before BB(): " + str(self.globalMempool.txs.keys()))
        bbMempool = bb.Mempool()
        bbMempool.fromDict(self.globalMempool.txs)
        builder = bb.CandidateSetBlockbuilder(bbMempool, weightAllowance) # TODO: use coinbase size here
        logging.debug("Block Mempool after BB(): " + str(builder.mempool.txs.keys()))
        selectedTxs = builder.buildBlockTemplate()
        logging.debug("selectedTxs: " + str(selectedTxs))
        self.confirmedTxs = set(selectedTxs).union(self.confirmedTxs)
        builder.outputBlockTemplate(self.height) # TODO: Height+blockhash?
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
    logging.basicConfig(filename='monthbuilder-latest.log', level=logging.INFO)
    mb = Monthbuilder(".")
    mb.loadAllowSet()
    mb.loadCoinbaseSizes() # TODO
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
        mb.runBlockWithGlobalMempool()
