# AncestorSets are used to track a transaction in the context of all its
# ancestors. We lazily instantiate these just with the transaction and backfill
# remaining data when we need it.

class AncestorSet():
    def __init__(self, rep):
        self.rep = rep
        self.txs = {rep.txid: rep}
        self.isComplete = False
        self.isObsolete = False
        self.weight = -1
        self.feerate = -1
        self.hash = None

    def __repr__(self):
        return "AncestorSet(%s, %s, %s)" % (str(self.rep.txid), str(sorted(list(self.txs.keys()))), str(self.getFeerate()))

    def __hash__(self):
        if self.hash is None:
            self.hash = hash(self.__repr__())
        return self.hash

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, AncestorSet):
            return self.__hash__() == other.__hash__()
        return NotImplemented

    def __lt__(self, other):
        if self.getFeerate() == other.getFeerate():
            if self.isComplete != other.isComplete:
                return other.isComplete
            return self.getWeight() > other.getWeight()
        return self.getFeerate() > other.getFeerate()

    def update(self, txs):
        print("Updating AncestorSet " + str(self) + " with " + str(txs))
        self.weight = -1
        self.feerate = -1
        for tx in txs:
            self.txs[tx.txid] = tx
        self.isComplete = True

    def getWeight(self):
        if self.weight < 0:
            self.weight = sum(tx.weight for tx in self.txs.values())
        return self.weight

    def getFees(self):
        return sum(tx.fee for tx in self.txs.values())

    def getFeerate(self):
        if self.feerate < 0:
            self.feerate = self.getFees()/self.getWeight()
        return self.feerate

    def getAncestorTxids(self):
        return self.rep.ancestors

    def getAllDescendants(self):
        print("getAllDescendants for: " + str(self))
        allDescendants = []
        for tx in self.txs.values():
            allDescendants = allDescendants + tx.descendants

        print("allDescendants for " + str(self) + ":" + str(allDescendants))
        withoutSelf = list(set(allDescendants) - set(self.txs.keys()))
        print("allDescendants for " + str(self) + "after removing self:" + str(withoutSelf))
        return withoutSelf

    def __str__(self):
        return "{txid: " + str(self.rep.txid) + " feerate: " + str(self.getFeerate()) + ", txs: "+ str(list(self.txs.keys())) + " isComplete: " + str(self.isComplete) + "}"

