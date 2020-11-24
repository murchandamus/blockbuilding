import json

#Clusters are represented by the lowest txid and map to a set of txids.
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
    repTxid = getRepresentativeTxid(getLocalClusterTxids(txid, transaction))
    #check if repTxid belongs to another cluster
    while (repTxid != txClusterMap[repTxid]):
        repTxid = txClusterMap[repTxid]
    txClusterMap[txid] = repTxid
    clusters[repTxid].add(txid)

with open('data/mempool.json') as f:
    mempool = json.load(f)

toBeClustered = {txid: vals for txid, vals in mempool.items() if vals["ancestorcount"] + vals["descendantcount"] > 2}

f.close()
