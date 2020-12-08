import json

clusters = {} # Clusters are represented by the lowest txid and map to a list of txids.
txClusterMap = {} # Maps transactions to cluster representatives.

def getRepresentativeTxid(txids):
    txids.sort()
    return txids[0]

def getLocalClusterTxids(txid, transaction):
    txids = [txid] + transaction["depends"] + transaction["spentby"]
    return txids

def clusterTransaction(txid, transaction):
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
        clusters[repTxid] = list(set([repTxid, txid]))
with open('data/mempool.json') as f:
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
        clusterTransaction(txid, vals)
        repAfter = txClusterMap[txid]
        anyUpdated = anyUpdated or repAfter != repBefore

print(json.dumps(clusters, 2))

f.close()
