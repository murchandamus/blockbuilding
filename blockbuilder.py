import json


class transaction():
    def __init__(self, txid, fee, weight, parents=[], descendants=[]):
        self.txid = txid
        self.fee = int(fee)
        self.weight = int(weight)
        self.descendants = []
        self.parents = parents


def getRepresentativeTxid(txids):
    txids.sort()
    return txids[0]


def getLocalClusterTxids(txid, transaction):
    txids = [txid] + transaction["depends"] + transaction["spentby"]
    return txids


def clusterTx(txid, transaction, clusters, txClusterMap):
    localClusterTxids = getLocalClusterTxids(txid, transaction)

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

    txClusterMap[txid] = repTxid
    if repTxid in clusters:
        clusters[repTxid] = list(set(clusters[repTxid] + [txid]))
    else:
        clusters[repTxid] = list({repTxid, txid})
    return clusters

def loadMempoolFile(mempoolFile):
    mempool = {}
    with open(mempoolFile) as f:
        mempool = json.load(f)
    f.close()
    return mempool


def parseMempoolFile(mempoolFile):
    mempool = loadMempoolFile(mempoolFile)
    clusters = {}  # Maps lowest txid to list of txids
    txids = {}
    txClusterMap = {}  # Maps txid to its representative's txid

    # Initialize txClusterMap with identity
    for txid in mempool.keys():
        txids[txid] = transaction(txid,
                        mempool[txid]["fees"]["base"],
                        mempool[txid]["weight"],
                        mempool[txid]["depends"],
                        mempool[txid]["spentby"]
                    )
        txClusterMap[txid] = txid

    anyUpdated = True

    # Recursively group clusters until nothing changes
    while (anyUpdated):
        clusters = {}
        anyUpdated = False
        for txid, vals in mempool.items():
            repBefore = txClusterMap[txid]
            clusters = clusterTx(txid, vals, clusters, txClusterMap)
            repAfter = txClusterMap[txid]
            anyUpdated = anyUpdated or repAfter != repBefore

    return clusters


if __name__ == '__main__':
    # mempoolFileString = "/home/murch/Workspace/blockbuilding/data/mempool.json"
    mempoolFileString = "/home/murch/Workspace/blockbuilding/data/mini-mempool.json"
    clusters = parseMempoolFile(mempoolFileString)
    print(json.dumps(clusters, 2))
