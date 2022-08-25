from txset import TransactionSet


class CandidateSet(TransactionSet):
    def __init__(self, txs):
        self.txs = {}
        self.weight = -1
        self.feerate = -1
        if len(txs) < 1:
            raise TypeError("set cannot be empty")
        for txid, tx in txs.items():
            if all(parent in txs.keys() for parent in tx.parents):
                self.txs[txid] = tx
            else:
                raise TypeError("parent of " + txid + " is not in txs")

        TransactionSet.__init__(self, self.txs)


    def __hash__(self):
        if self.hash is None:
            self.hash = hash(self.__repr__())
        return self.hash

    def __repr__(self):
        return "CandidateSet(%s, %s)" % (str(sorted(list(self.txs.keys()))), str(self.get_feerate()))


    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, CandidateSet):
            return self.__hash__() == other.__hash__()
        return NotImplemented


    def __lt__(self, other):
        if self.get_feerate() == other.get_feerate():
            return self.get_weight() > other.get_weight()
        return self.get_feerate() > other.get_feerate()


    def getChildren(self):
        allChildren = (d for tx in self.txs.values() for d in tx.children)
        unexploredChildren = set(allChildren) - set(self.txs.keys())
        return list(unexploredChildren)


    def __str__(self):
        return "{feerate: " + str(self.get_feerate()) + ", txs: "+ str(list(self.txs.keys())) + "}"

