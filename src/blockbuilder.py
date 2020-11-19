import json

with open('../data/mempool.json') as f:
    mempool = json.load(f)

print(len(mempool))

f.close()
