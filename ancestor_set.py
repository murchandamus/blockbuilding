import logging

from txset import TransactionSet

# AncestorSets are used to track a transaction in the context of all its
# ancestors. We lazily instantiate these just with the transaction and backfill
# remaining data when we need it.

class AncestorSet(TransactionSet):
    def __init__(self, rep):
        self.rep = rep
        self.txs = {rep.txid: rep}
        self.isComplete = False
        self.isObsolete = False

        TransactionSet.__init__(self, self.txs)


    def __repr__(self):
        return "AncestorSet(%s, %s, %s)" % (str(self.rep.txid), str(sorted(list(self.txs.keys()))), str(self.get_feerate()))


    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, AncestorSet):
            return self.__hash__() == other.__hash__()
        return NotImplemented


    def __lt__(self, other):
        if self.get_feerate() == other.get_feerate():
            if self.isComplete != other.isComplete:
                return other.isComplete
            return self.get_weight() > other.get_weight()
        return self.get_feerate() > other.get_feerate()


    def update(self, txs):
        logging.debug("Updating AncestorSet " + str(self) + " with " + str(txs))
        self.weight = -1
        self.feerate = -1
        for tx in txs:
            self.txs[tx.txid] = tx
        self.isComplete = True


    def getAncestorTxids(self):
        return self.rep.ancestors


    def getAllDescendants(self):
        logging.debug("getAllDescendants for: " + str(self))
        allDescendants = set()
        for tx in self.txs.values():
            allDescendants = allDescendants | set(tx.descendants)

        logging.debug("allDescendants for " + str(self) + ":" + str(allDescendants))
        withoutSelf = list(allDescendants - set(self.txs.keys()))
        logging.debug("allDescendants for " + str(self) + "after removing self:" + str(withoutSelf))
        return withoutSelf


    def __str__(self):
        return "{txid: " + str(self.rep.txid) + " feerate: " + str(self.get_feerate()) + ", txs: "+ str(list(self.txs.keys())) + " isComplete: " + str(self.isComplete) + "}"

