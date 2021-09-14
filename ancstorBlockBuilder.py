import blockbuilder as bb
from collections import OrderedDict


class BlockbuilderByAnces():
    def __init__(self, mempool, weightLimit=3992820):
        self.mempool = mempool
        self.refMempool = bb.Mempool()
        #self.refMempool.fromDict(mempool.txs)
        self.selectedTxs = []
        self.weightLimit = weightLimit
        self.availableWeight = self.weightLimit

    def getAncestors(self, tx, depth=0):
        """ Fron Johns Solution
        Returns: list of (ancestor, depth) tuples.
        Ancestors may appear more than once in an ancestor tree, including with different depths.
        Sorting by descending depth and deduping implies no descendant appears before its ancestor."""
        ancestors = [(self.mempool.txs[tx.txid], depth)]
        for parent in self.mempool.txs[tx.txid].parents:
            ancestors += self.getAncestors(self.mempool.txs[parent], depth + 1)
        if depth > 0:
            return ancestors
        ret = []
        for ancestor, _ in sorted(ancestors, key=lambda ad: ad[1], reverse=True):
            if ancestor not in ret:
                ret.append(self.mempool.txs[ancestor.txid].txid)
        print(ret)
        return ret


    def buildBlockTemplat(self, weightlimit):
        for tx in self.refMempool.txs:
            # Calculate ancestors for each tx
            tx.ancestors = self.getAncestors(tx, 0)
            tx.ancestor_fee = sum([self.refMempool.txs[ancestor_txid].fee for ancestor_txid in tx.ancestors])
            tx.ancestor_weight = sum([self.refMempool.txs[ancestor_txid].weight for ancestor_txid in tx.ancestors])
            tx.ancestor_feerate = tx.ancestor_fee / tx.ancestor_weight
            for anc in [a.txid for a in tx.ancestors if a.txid != tx.txid]:
                txs[anc].descendants.append(tx.txid)

            # Reorder transactions by ancestor_feerate
        txs = OrderedDict(sorted(txs.items(), key=lambda tx: tx[1].ancestor_feerate, reverse=True))

if __name__ == '__main__':
    mempool = bb.Mempool()
    mempool.fromTXT("/Users/clara/Documents/GitHub/blockbuilding/test/test_block.mempool")
    print(mempool.txs.keys())
    builder = BlockbuilderByAnces(mempool)
    builder.getAncestors(mempool.txs["2"])








