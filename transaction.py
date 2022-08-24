import logging

# A Transaction in the context of a specific mempool and blocktemplate state.
# Ancestors, Parents, and children will be updated as the blocktemplate is being built whenever anything gets picked from the Cluster.
class Transaction():
    def __init__(self, txid, fee, weight, parents=None, children=None, ancestors=None, descendants=None):
        self.txid = txid
        self.fee = int(fee)
        self.feerate = None
        self.weight = int(weight)
        self.hash = None
        if parents is None:
            parents = []
        self.parents = set([] + parents)
        if ancestors is None:
            ancestors = []
        self.ancestors = set([] + ancestors)
        self.permanent_parents = []
        if children is None:
            children = []
        self.children = set([] + children)
        if descendants is None:
            descendants = []
        self.descendants = set([] + descendants)

    def createExportDict(self):
        txRep = { 'fee': self.fee, 'weight': self.weight, 'spentby': list(self.children), 'depends': list(self.parents) }
        return txRep

    def get_feerate(self):
        if not self.feerate:
            self.feerate = self.fee / self.weight
        return self.feerate

    def getLocalClusterTxids(self):
        return list(set([self.txid] + list(self.children) + list(self.parents)))

    def __str__(self):
        return "{txid: " + self.txid + ", children: " + str(self.children) + ", parents: " + str(self.parents) + ", fee: " + str(self.fee) + ", weight: " + str(self.weight) + "}"

    def __repr__(self):
        return "Transaction(%s)" % (self.txid)

    def __eq__(self, other):
        if isinstance(other, Transaction):
            return self.txid == other.txid
        return NotImplemented

    def __lt__(self, other):
        # Sort highest feerate first, use highest weight as tiebreaker
        if self.get_feerate() == other.get_feerate():
            return self.weight > other.weight
        return self.get_feerate() > other.get_feerate()

    def __hash__(self):
        if self.hash is None:
            self.hash = hash(self.__repr__())
        return self.hash
