import blockbuilder as bb
import os
from os.path import isfile, join

# TODO:
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
        self.confirmedList = set()
        self.allowList = set()
        self.usedTxList = set()
        self.height = -1

    def loadAllowList(self):
        files = os.listdir(self.pathToMonth)
        for f in files:
            if f.endswith('.allow'):
                with open(os.path.join(self.pathToMonth, f), 'r') as import_allow_list:
                    for line in import_allow_list:
                        self.allowList.add(line.rstrip('\n'))
                import_allow_list.close()
        if len(self.allowList) == 0:
            raise ValueError('Allowed list empty')


    def updateUsedList(self, txList):
        newTxSet = set(txList)
        self.usedTxList = self.usedTxList.union(newTxSet)

    def loadBlockMempool(self, blockId):
        FileFound = 0
        for file in os.listdir(self.pathToMonth):
            if file.endswith(blockId+'.mempool'):
                FileFound = 1
                tempMempool = bb.Mempool()
                print(os.path.join(self.pathToMonth, file))
                tempMempool.fromTXT(os.path.join(self.pathToMonth, file))
                print('size of mempool is: '+str([k for k in tempMempool.txs.keys()]))
                tempMempoolSet = set([k for k in tempMempool.txs.keys()])
                print(tempMempoolSet)
                tempMempoolSet.update([k for k in self.globalMempool.txs.keys()])
                print(tempMempoolSet)
                tempMempoolSet.difference_update(self.usedTxList)
                print(tempMempoolSet)
                tempMempoolSet.intersection_update(self.allowList)
                print("tamp mempool set is: ")
                print(tempMempoolSet)
        if FileFound == 0:
            raise FileNotFoundError("Mempool not found")


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
    mempool = blockbuilder.Mempool()
    mempool.fromTXT(mempoolfilepath)
    bb = Blockbuilder(mempool)
    bb.buildBlockTemplate()
    bb.outputBlockTemplate(mempool.blockId)
    endTime = time.time()
    print('Elapsed time: ' + str(endTime - startTime))

if __name__ == '__main__':
    mb = Monthbuilder("./data/data_example/test")
    mb.loadAllowList()
    mb.loadBlockMempool('123456')