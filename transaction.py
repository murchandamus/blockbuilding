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
        self.parents = parents
        if ancestors is None:
            ancestors = []
        self.ancestors = ancestors
        if children is None:
            children = []
        self.children = children
        if descendants is None:
            descendants = []
        self.descendants = descendants

    def createExportDict(self):
        txRep = { 'fee': self.fee, 'weight': self.weight, 'spentby': self.children, 'depends': self.parents }
        return txRep

    def getFeerate(self):
        if not self.feerate:
            self.feerate = self.fee / self.weight
        return self.feerate

    def getLocalClusterTxids(self):
        return list(set([self.txid] + self.children + self.parents))

    def __str__(self):
        return "{txid: " + self.txid + ", children: " + str(self.children) + ", parents: " + str(self.parents) + ", fee: " + str(self.fee) + ", weight: " + str(self.weight) + "}"


# TODO: Add methods for sorting transaction by feerate
