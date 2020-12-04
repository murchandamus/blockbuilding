import json

#Clusters are represented by the lowest txid and map to a list of txids.
clusters = {}

#Maps transactions to cluster representatives.
txClusterMap = {}

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

for txid in mempool.keys():
    txClusterMap[txid] = txid

toBeClustered = {txid: vals for txid, vals in mempool.items() if vals["ancestorcount"] + vals["descendantcount"] > 2}
anyUpdated = True

while (anyUpdated):
    clusters = {}
    anyUpdated = False
    for txid, vals in mempool.items():
        #print "txid, vals: ", txid, vals
        repBefore = txClusterMap[txid]
        #print "repBefore: ", repBefore
        clusterTransaction(txid, vals)
        repAfter = txClusterMap[txid]
        #print "repAfter: ", repAfter
        anyUpdated = anyUpdated or repAfter != repBefore
        #print "anyUpdated: ", anyUpdated

print(json.dumps(clusters, 2))

f.close()
