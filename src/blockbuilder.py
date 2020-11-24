import json

def getRepresentativeTx(transactions):
    txids = transactions.keys()
    txids.sort()
    return txids[0]

def getLocalClusterTxids(txid, transaction):
    print(transaction)
    txids = [txid] + transaction["depends"] + transaction["spentby"] 
    print(txids)
    return txids

with open('../data/mempool.json') as f:
    mempool = json.load(f)

print(len(mempool))

toBeClustered = {txid: vals for txid, vals in mempool.items() if vals["ancestorcount"] + vals["descendantcount"] > 2}

print(len(toBeClustered))

testDict = {
    "acb":{"key":"otherValue", "depends": ["123"], "spentby":[]},
    "123":{"key":"value", "depends": [], "spentby":["abc"]},
    "abc":{"key":"v3", "depends": [], "spentby":[]},
}

assert getRepresentativeTx(testDict) == "123", "Should be 123"
assert getLocalClusterTxids("acb", testDict["acb"]) == ["acb", "123"]

f.close()
