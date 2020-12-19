import json


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
    return clusters[repTxid]


def parseMempoolFile(mempoolFile):
    mempool = []
    clusters = {}  # Maps lowest txid to list of txids
    txClusterMap = {}  # Maps txid to its representative's txid

    with open(mempoolFile) as f:
        mempool = json.load(f)

    # Initialize txClusterMap with identity
    for txid in mempool.keys():
        txClusterMap[txid] = txid

    anyUpdated = True

    # Recursively group clusters until nothing changes
    while (anyUpdated):
        clusters = {}
        anyUpdated = False
        for txid, vals in mempool.items():
            repBefore = txClusterMap[txid]
            clusterTx(txid, vals, clusters, txClusterMap)
            repAfter = txClusterMap[txid]
            anyUpdated = anyUpdated or repAfter != repBefore

    print(json.dumps(clusters, 2))

    f.close()


mempoolFileString = "/home/murch/Workspace/blockbuilding/data/mempool.json"
parseMempoolFile(mempoolFileString)
