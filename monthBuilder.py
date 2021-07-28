import blockbuilder
import os
import os.path import isfile, join

# TODO:
## Identify the lowest block-id (i.e. height)
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
        self.globalMempool = Mempool()
        self.confirmedList = set()
        self.allowList = AllowList()
        self.height = -1

    def loadAllowList(self):
        ## Assume that there is exactly one in the folder
        ## TODO: Allowlist is just a text file with one transaction id on every line, e.g. '2020-08.allow'

    def getNextBlockHeight(self):
        ## Assume that there are mempool files in folder and they are prefixed with a _seven_ digit block height
        if self.height > 0:
            height = height+1
            return height
        else:
            dirContent = os.listdir(self.pathToMonth)
            onlymempool =  [f for f in dirContent if f.endswith('.mempool')]
            onlymempool.sort()
            height = onlymempool[0][0:7]
            return height

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
    print('Elapsed time: ' + str(endTime - startTime))

if __name__ == '__main__':
    main(sys.argv[1:])
