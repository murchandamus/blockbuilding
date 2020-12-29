import json


class Transaction():
    def __init__(self, txid, fee, weight, parents=[], descendants=[]):
        self.txid = txid
        self.fee = int(fee)
        self.weight = int(weight)
        self.descendants = descendants
        self.parents = parents

    def getLocalClusterTxids(self):
        return list(set([self.txid] + self.descendants + self.parents))


class Cluster():
    def __init__(self, tx):
        self.representative = tx.txid
        self.txs = {tx.txid: tx}

    def addTx(self, tx):
        self.txs[tx.txid] = tx
        self.representative = min(tx.txid, self.representative)

    def getBestCandidateSet(self):
        print("not implemented")
        # generate powerset
        # filter for validity
        # sort by effective feerate
        # return best


class Mempool():
    def __init__(self):
        self.txs = {}

    def fromJSON(self, filePath):
        txsJSON = {}
        with open(filePath) as f:
            txsJSON = json.load(f)

            # Initialize txClusterMap with identity
            for txid in txsJSON.keys():
                self.txs[txid] = Transaction(
                    txid,
                    txsJSON[txid]["fees"]["base"],
                    txsJSON[txid]["weight"],
                    txsJSON[txid]["depends"],
                    txsJSON[txid]["spentby"]
                )
        f.close()

    def fromTXT(self, filePath):
        print("not implemented")
        # Clara fills this in

    def getTx(self, txid):
        return self.txs[txid]

    def getTxs(self):
        return self.txs


def getRepresentativeTxid(txids):
    txids.sort()
    return txids[0]


def clusterTx(transaction, clusters, txClusterMap):
    localClusterTxids = transaction.getLocalClusterTxids()

    # Check for each tx in local cluster if it belongs to another cluster
    for lct in localClusterTxids:
        if lct not in txClusterMap.keys():
            txClusterMap[lct] = lct
        lctRep = txClusterMap[lct]
        localClusterTxids = localClusterTxids + [lctRep]
        # Check recursively if ltcRep belongs to another cluster
        while (lctRep != txClusterMap[lctRep]):
            lctRep = txClusterMap[lctRep]
            localClusterTxids = localClusterTxids + [lctRep]

    repTxid = getRepresentativeTxid(localClusterTxids)

    txClusterMap[transaction.txid] = repTxid
    if repTxid in clusters:
        clusters[repTxid] = list(set(clusters[repTxid] + localClusterTxids))
    else:
        clusters[repTxid] = list(set([repTxid] + localClusterTxids))
    clusters[repTxid].sort()
    return clusters


def clusterMempool(mempool):
    clusters = {}  # Maps lowest txid to list of txids
    txClusterMap = {}  # Maps txid to its representative's txid

    # Initialize txClusterMap with identity
    for txid in mempool.getTxs().keys():
        txClusterMap[txid] = txid

    anyUpdated = True

    # Recursively group clusters until nothing changes
    while (anyUpdated):
        clusters = {}
        anyUpdated = False
        for txid, vals in mempool.getTxs().items():
            repBefore = txClusterMap[txid]
            clusters = clusterTx(vals, clusters, txClusterMap)
            repAfter = txClusterMap[txid]
            anyUpdated = anyUpdated or repAfter != repBefore

    return clusters


if __name__ == '__main__':
    # mempoolFileString = "/home/murch/Workspace/blockbuilding/data/mempool.json"
    mempoolFileString = "/home/murch/Workspace/blockbuilding/data/mini-mempool.json"
    mempool = Mempool()
    mempool.fromJSON(mempoolFileString)
    clusters = clusterMempool(mempool)
    print(json.dumps(clusters, 2))
