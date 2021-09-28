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
        return ret


    def OrderTxs(self, txs):
        for tx in txs:
            # Calculate ancestors for each tx
            self.mempool.txs[tx].ancestors = self.getAncestors(self.mempool.txs[tx], 0)
            self.mempool.txs[tx].ancestor_fee = sum([self.mempool.txs[ancestor_txid].fee for ancestor_txid in self.mempool.txs[tx].ancestors])
            self.mempool.txs[tx].ancestor_weight = sum([self.mempool.txs[ancestor_txid].weight for ancestor_txid in self.mempool.txs[tx].ancestors])
            self.mempool.txs[tx].ancestor_feerate = self.mempool.txs[tx].ancestor_fee / self.mempool.txs[tx].ancestor_weight
            for anc in [self.mempool.txs[a].txid for a in self.mempool.txs[tx].ancestors if self.mempool.txs[a].txid != self.mempool.txs[tx].txid]:
                txs[anc].descendants.append(tx)

            # Reorder transactions by ancestor_feerate
        return OrderedDict(sorted(txs.items(), key=lambda tx: tx[1].ancestor_feerate, reverse=True))


    def buildBlockTemplat(self, weightlimit):
        txs = self.OrderTxs(self.mempool.txs)

        block = []
        block_weight = 0

        def remove_from_pool(tx):
            # print("including tx {}".format(tx.txid))
            for desc in set(self.mempool.txs[tx].descendants):
                self.mempool.txs[desc].ancestor_fee -= self.mempool.txs[tx].fee
                self.mempool.txs[desc].ancestor_weight -= self.mempool.txs[tx].weight
                self.mempool.txs[desc].ancestor_feerate = txs[desc].ancestor_fee / txs[desc].ancestor_weight
                self.mempool.txs[desc].ancestors.remove(tx)
                # print("modifying descendant {}".format(desc))

        while txs:
            # Pop first transaction from ordered dict
            tx = next(iter(txs.values()))
            if block_weight + tx.ancestor_weight > weightlimit:
                # Package won't fit in block
                txs.pop(tx.txid)
                continue
            # Add all unincluded package txs to block
            # print("including package {}: {}".format(tx.txid, ','.join([a.txid for a in tx.ancestors])))
            ancestors = [a for a in tx.ancestors]
            for ancestor in ancestors:
                if self.mempool.txs[ancestor].txid not in txs:
                    # ancestor already included
                    print(self.mempool.txs[ancestor].txid)
                    assert False
                print("anc" + ancestor)
                print("dec" + str(self.mempool.txs[ancestor].descendants))
                for desc in self.mempool.txs[ancestor].descendants:
                    print(desc)
                remove_from_pool(ancestor)
                block.append(txs.pop(self.mempool.txs[ancestor].txid).txid)
                block_weight += self.mempool.txs[ancestor].weight
            # Resort list
            txs = OrderedDict(sorted(txs.items(), key=lambda tx: tx[1].ancestor_feerate, reverse=True))
            continue  # Break into outer loop. Restart iteration over all unincluded txs

        return block


if __name__ == '__main__':
    mempool = bb.Mempool()
    mempool.fromTXT("/Users/clara/Documents/GitHub/blockbuilding/test/anotherTestBlock.mempool")
    builder = BlockbuilderByAnces(mempool)
    builder.getAncestors(mempool.txs["2"])
  #  builder.OrderTxs(mempool.txs)
    print("block is "+str(builder.buildBlockTemplat(100000)))








