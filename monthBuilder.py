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
            raise ValueError('Allowed list empty')
        print('allowSet: ' + str(self.allowSet))

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
                print("txsToRemove: " + str(txsToRemove))
                if len(txsToRemove) > 0:
                    print("block txs before pruning for allow set " + str(blockTxsSet))
                    blockMempool = self.removeSetOfTxsFromMempool(txsToRemove, blockMempool)
                    print("block txs after pruning for allow set " + str(blockMempool.txs.keys()))
                for k in blockMempool.txs.keys():
                    self.globalMempool.txs[k] = blockMempool.txs[k]
                for k in list(self.globalMempool.txs.keys()):
                    if k in self.usedTxSet:
                        self.globalMempool.txs.pop(k)

        print("Global Mempool after loading block: " + str(self.globalMempool.txs.keys()))

        if fileFound == 0:
            raise Exception("Mempool not found")

    def loadCoinbaseSizes(self):
        for file in os.listdir(self.pathToMonth):
            if file.endswith('.coinbases'):
                with open(os.path.join(self.pathToMonth, file), 'r') as coinbaseSizes:
                    for line in coinbaseSizes:
                        lineItems = line.split(' ')
                        self.coinbaseSizes[lineItems[0]] = lineItems[1]
                coinbaseSizes.close()
        if len(self.coinbaseSizes) == 0:
            raise Exception('Coinbase file not found')

    def runBlockWithGlobalMempool(self):
        coinbaseSizeForCurrentBlock = self.coinbaseSizes[self.height]
        weightAllowance = 4000000 - int(coinbaseSizeForCurrentBlock)
        builder = bb.Blockbuilder(self.globalMempool, weightAllowance) # TODO: use coinbase size here
        selectedTxs = builder.buildBlockTemplate()
        print("selectedTxs: " + str(selectedTxs))
        self.usedTxSet = self.usedTxSet.union(set(selectedTxs))
        builder.outputBlockTemplate(self.height) # TODO: Height+blockhash?

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
            print('Height not found, done')
            break
        print("Starting block: " + blockfileName)
        mb.loadBlockMempool(blockfileName)
        mb.runBlockWithGlobalMempool()
