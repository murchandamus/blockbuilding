import json

def getRepresentativeTx(transactions):
    txids = transactions.keys()
    txids.sort()
    return txids[0]

def getRepresentativeTxid(txids):
    txids.sort()
    return txids[0]

def getLocalClusterTxids(txid, transaction):
    txids = [txid] + transaction["depends"] + transaction["spentby"] 
    return txids

with open('data/mempool.json') as f:
    mempool = json.load(f)

toBeClustered = {txid: vals for txid, vals in mempool.items() if vals["ancestorcount"] + vals["descendantcount"] > 2}
clusters = {}

f.close()
