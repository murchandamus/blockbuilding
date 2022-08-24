import functools

# An abstract class that subsumes CandidateSets and AncestorSets
class TransactionSet():
    def __init__(self, txs):
        self.txs = txs
        self.weight = -1
        self.feerate = -1
        self.hash = None


    def get_weight(self):
        if self.weight < 0:
            self.weight = sum(tx.weight for tx in self.txs.values())
        return self.weight


    def get_fees(self):
        return sum(tx.fee for tx in self.txs.values())


    def get_feerate(self):
        if self.feerate < 0:
            self.feerate = self.get_fees()/self.get_weight()
        return self.feerate


    def get_topologically_sorted_txids(self):
        return [tx.txid for tx in sorted(list(self.txs.values()), key=lambda tx: (len(tx.ancestors), tx.txid))]


    def __repr__(self):
        return NotImplemented


    def __hash__(self):
        if self.hash is None:
            self.hash = hash(self.__repr__())
        return self.hash


    def __eq__(self, other):
        return NotImplemented


    def __str__(self):
        return "{feerate: " + str(self.get_feerate()) + ", txs: "+ str(list(self.txs.keys())) + "}"
