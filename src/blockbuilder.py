import json

with open('../data/mempool.json') as f:
    mempool = json.load(f)

print(len(mempool))

toBeClustered = {txid: vals for txid, vals in mempool.items() if vals["ancestorcount"] + vals["descendantcount"] > 2}

print(len(toBeClustered))

f.close()
