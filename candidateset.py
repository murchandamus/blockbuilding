class CandidateSet():
    def __init__(self, txs):
        self.txs = {}
        self.weight = -1
        self.effectiveFeerate = -1
        self.hash = None
        if len(txs) < 1:
            raise TypeError("set cannot be empty")
        for txid, tx in txs.items():
            unconfirmed_parents = set(tx.immutable_parents) & set(tx.unconfirmed_ancestors)
            if all(parent in txs.keys() for parent in unconfirmed_parents):
                self.txs[txid] = tx
            else:
                raise TypeError("unconfirmed parent of " + txid + " is not in txs")

    def __repr__(self):
        return "CandidateSet(%s, %s)" % (str(sorted(list(self.txs.keys()))), str(self.getEffectiveFeerate()))

    def __hash__(self):
        if self.hash is None:
            self.hash = hash(self.__repr__())
        return self.hash

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, CandidateSet):
            return self.__hash__() == other.__hash__()
        return NotImplemented

    def __lt__(self, other):
        if self.getEffectiveFeerate() == other.getEffectiveFeerate():
            return self.getWeight() > other.getWeight()
        return self.getEffectiveFeerate() > other.getEffectiveFeerate()

    def getWeight(self):
        if self.weight < 0:
            self.weight = sum(tx.weight for tx in self.txs.values())
        return self.weight

    def getFees(self):
        return sum(tx.fee for tx in self.txs.values())

    def getEffectiveFeerate(self):
        if self.effectiveFeerate < 0:
            self.effectiveFeerate = self.getFees()/self.getWeight()
        return self.effectiveFeerate

    def getChildren(self):
        allChildren = (d for tx in self.txs.values() for d in tx.children)
        unexploredChildren = set(allChildren) - set(self.txs.keys())
        return list(unexploredChildren)

    def __str__(self):
        return "{feerate: " + str(self.getEffectiveFeerate()) + ", txs: "+ str(list(self.txs.keys())) + "}"

