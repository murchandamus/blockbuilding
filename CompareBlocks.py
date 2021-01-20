import blockbuilder
import networkx
import matplotlib.pyplot as plt

class Block():
    def __init__(self, blockNumer):
        self.blockContent = {}
        self.blockNumber = blockNumer
        self.srcCompare = {}
        self.mempool = blockbuilder.Mempool()

    def getMempool(self, mempoolLocation):
        self.mempool.fromTXT(mempoolLocation)

    def addSource(self, source, fileLocation):
        self.blockContent[source] = readBlock(fileLocation)

    def getDiff(self):
        for scr in self.blockContent.keys():
            for scr2 in self.blockContent.keys():
                if scr != scr2:
                    self.srcCompare['in ' + scr + ' and not in ' + scr2] = \
                        set(self.blockContent[scr]) - set(self.blockContent[scr2])

    def buildDiffGraphs(self):
        Graphs = {}
        for srces in self.srcCompare.keys():
            G = networkx.DiGraph()
            for tx in self.srcCompare[srces]:
                G.add_node(self.mempool.txs[tx].txid)
                for parent in self.mempool.txs[tx].parents:
                    if parent in self.srcCompare[srces]:
                        G.add_node(self.mempool.txs[parent].txid)
                        G.add_edge(self.mempool.txs[tx].txid, self.mempool.txs[parent].txid)
            Graphs[srces] = G
        return Graphs

    def drawDiffGraphs(self):
        graphs = block.buildDiffGraphs()
        i = 1
        for src in graphs.keys():
            plt.subplot(1, 2, i)
            plt.title(str(src))
            networkx.draw(graphs[src], with_labels=False)
            i += 1
        plt.show()






def readBlock(fileLocation):
    try:
        file = open(fileLocation, 'r')
        file.readline() #skip the header
        transactions = set(l.strip() for l in file.readlines())
        return transactions
    except FileNotFoundError:
        print('no file found '+str(fileLocation))


if __name__ == '__main__':
    blockNumber = 123
    block = Block(blockNumber)
    block.addSource('txt', r"./data/data example/000000000000000000269e0949579bd98366bef1ca308d134182dbf28dc6fdef_LP.txt")
    block.addSource('gbt', r"./data/data example/000000000000000000269e0949579bd98366bef1ca308d134182dbf28dc6fdef.gbt")
    print(str(block.blockContent))
    block.getDiff()
    print(block.srcCompare)
    block.getMempool(r"./data/data example/000000000000000000269e0949579bd98366bef1ca308d134182dbf28dc6fdef_with_extra_tx.mempool")
    block.drawDiffGraphs()