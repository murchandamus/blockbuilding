import json

clusters = {} #Clusters are represented by the lowest txid and map to a list of txids.
txClusterMap = {} #Maps transactions to cluster representatives.

def getRepresentativeTxid(txids):
    txids.sort()
    return txids[0]

def getLocalClusterTxids(txid, transaction):
    txids = [txid] + transaction["depends"] + transaction["spentby"]
    return txids

def clusterTransaction(txid, transaction):
    localClusterTxids = getLocalClusterTxids(txid, transaction)

    #check for each tx in local cluster if it belongs to another cluster
    for lct in localClusterTxids:
        lctRep = txClusterMap[lct]
        localClusterTxids = localClusterTxids + [lctRep]
        #check recursively if ltcRep belongs to another cluster
        while (lctRep != txClusterMap[lctRep]):
            lctRep = txClusterMap[lctRep]
            localClusterTxids = localClusterTxids + [lctRep]

    repTxid = getRepresentativeTxid(localClusterTxids)

    txClusterMap[txid] = repTxid
    if repTxid in clusters:
        clusters[repTxid] = list(set(clusters[repTxid] + [txid]))
    else:
        clusters[repTxid] = [repTxid, txid]
with open('data/mempool.json') as f:
    mempool = json.load(f)

# initialize txClusterMap with identity
for txid in mempool.keys():
    txClusterMap[txid] = txid

toBeClustered = {txid: vals for txid, vals in mempool.items() if vals["ancestorcount"] + vals["descendantcount"] > 2}
anyUpdated = True

# recursively group clusters until nothing changes
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
