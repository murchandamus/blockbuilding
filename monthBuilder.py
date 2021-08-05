import blockbuilder as bb
import os
from os.path import isfile, join

# TODO:
## load AllowList - done
## Identify the lowest block-id (i.e. height) - done
## load mempool of for the first block
## filter to txs in whitelist
## build block respecting the coinbase size
## Add the transactions "confirmed" in our block to the "confirmedList", which must be global
## Second block (increment height, find file with that prefix):
## Keep the mempool from the first block, add the mempool from the second block
### Deduplicate
### Remove confirmed transactions and only allow whitelisted transactions
### Remove dependencies from transactions that are in the confirmed list
## build 2nd block respecting the coinbase size
## i-th block: same.

class Monthbuilder():
    def __init__(self, monthPath):
        self.pathToMonth = monthPath
        self.globalMempool = bb.Mempool()
        self.allowSet = set()
        self.usedTxSet = set()
        self.height = -1

    def loadAllowList(self):
        files = os.listdir(self.pathToMonth)
        for f in files:
            if f.endswith('.allow'):
                with open(os.path.join(self.pathToMonth, f), 'r') as import_allow_list:
                    for line in import_allow_list:
                        self.allowSet.add(line.rstrip('\n'))
                import_allow_list.close()
        if len(self.allowSet) == 0:
            raise ValueError('Allowed list empty')


    def updateUsedList(self, txList):
        newTxSet = set(txList)
        self.usedTxSet = self.usedTxSet.union(newTxSet)

    def removeSetOfTxsFromMempool(self, txsSet, mempool):
        try:
            for k in txsSet:
                del mempool.txs[k]
        except KeyError:
            print("tx to delete not found" + k)
        return mempool

    def loadBlockMempool(self, blockId):
        fileFound = 0
        for file in os.listdir(self.pathToMonth):
            if file.endswith(blockId+'.mempool'):
                fileFound = 1
                blockMempool = bb.Mempool()
                blockMempool.fromTXT(os.path.join(self.pathToMonth, file))
                blockTxsSet = set([k for k in blockMempool.txs.keys()]) # TODO: should this just be 'set(keys())'?
                txsToRemove = blockTxsSet.difference(self.allowSet)
                cleanNewMempoolTxs = self.removeSetOfTxsFromMempool(txsToRemove, blockMempool)
                for k in cleanNewMempoolTxs.txs.keys():
                    self.globalMempool.txs[k] = blockMempool.txs[k]
                for k in list(self.globalMempool.txs.keys()):
                    if k in self.usedTxSet:
                        self.globalMempool.txs.pop(k)

        if fileFound == 0:
            raise FileNotFoundError("Mempool not found")

    def runBlockWithGlobalMempool(self):
        builder = bb.Blockbuilder(self.globalMempool) # TODO: use coinbase size here
        selectedTxs = builder.buildBlockTemplate()
        self.usedTxSet = self.usedTxSet.union(set(selectedTxs))
        builder.outputBlockTemplate(height) # TODO: Height+blockhash?

    def getNextBlockHeight(self):
        ## Assume that there are mempool files in folder and they are prefixed with a _seven_ digit block height
        if self.height > 0:
            self.height = self.height+1
            return self.height
        else:
            dirContent = os.listdir(self.pathToMonth)
            onlymempool =  [f for f in dirContent if f.endswith('.mempool')]
            onlymempool.sort()
            self.height = onlymempool[0][0:7]
            return self.height

if __name__ == '__main__':
    mb = Monthbuilder("./data/data_example/test")
    mb.loadAllowList()
    mb.loadCoinbaseSizes() # TODO
    while(True):
        mb.getNextBlockHeight()
        blockfileName = ''
        files = os.listdir(self.pathToMonth)
        for f in files:
            if f.startswith(str(height)):
                blockfileName = f.split('.')[0]
                break
        if blockfileName == '':
            print('Height not found, done')
            break
        mb.loadBlockMempool(blockfileName)
        mb.runBlockWithGlobalMempool()
