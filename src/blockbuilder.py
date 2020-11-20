import json

def getRepresentativeTx(transactions):
    txids = transactions.keys()
    txids.sort()
    return txids[0]

with open('../data/mempool.json') as f:
    mempool = json.load(f)

print(len(mempool))

toBeClustered = {txid: vals for txid, vals in mempool.items() if vals["ancestorcount"] + vals["descendantcount"] > 2}

print(len(toBeClustered))

testDict = {
    "acb":{"key":"otherValue"},
    "123":{"key":"value"},
    "abc":{"key":"v3"},
}

assert getRepresentativeTx(testDict) == "123", "Should be 123"

f.close()
