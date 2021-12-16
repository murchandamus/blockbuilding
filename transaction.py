import logging

# A Transaction in the context of a specific mempool and blocktemplate state.
# Ancestors, Parents, and children will be updated as the blocktemplate is being built whenever anything gets picked from the Cluster.
class Transaction():
    def __init__(self, txid, fee, weight, parents=None, children=None, ancestors=None, descendants=None):
        self.txid = txid
        self.fee = int(fee)
        self.feerate = None
        self.weight = int(weight)
        if parents is None:
            parents = []
            #TODO: NEVER DELETE PARENTS
        self.immutable_parents = set([] + parents)
        if ancestors is None:
            ancestors = []
            #TODO: RENAME TO "UNCONFIRMED_ANCESTORS"
        self.unconfirmed_ancestors = set([] + ancestors) | self.immutable_parents
        if children is None:
            children = []
        self.children = set([] + children)
        if descendants is None:
            descendants = []
        self.descendants = set([] + descendants)

    def createExportDict(self):
        txRep = { 'fee': self.fee, 'weight': self.weight, 'spentby': self.children, 'depends': self.immutable_parents }
        return txRep

    def getFeerate(self):
        if not self.feerate:
            self.feerate = self.fee / self.weight
        return self.feerate

    def getLocalClusterTxids(self):
        return list(set([self.txid] + list(self.children) + list(set(self.immutable_parents) & set(self.unconfirmed_ancestors))))

    def __str__(self):
        return "{txid: " + self.txid + ", children: " + str(self.children) + ", parents: " + str(self.immutable_parents) + ", fee: " + str(self.fee) + ", weight: " + str(self.weight) + "}"

    def __repr__(self):
        return "Transaction(%s)" % (self.txid)

    def __eq__(self, other):
        if isinstance(other, Transaction):
            return self.txid == other.txid
        return NotImplemented

    def __lt__(self, other):
        # Sort highest feerate first, use highest weight as tiebreaker
        if self.getFeerate() == other.getFeerate():
            return self.weight > other.weight
        return self.getFeerate() > other.getFeerate()

    def __hash__(self):
        if self.hash is None:
            self.hash = hash(self.__repr__())
        return self.hash
