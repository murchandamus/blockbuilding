import blockbuilder
import sys
import os
from collections import Counter

def readBlock(fileLocation):
    block_file = open(fileLocation)
    block_file.readline()
    block = [l.strip() for l in block_file.readlines()]
    block_file.close()
    return block

def checkBlockValditiy(mempool, block):
    print('checking Block Validity')
    duplicate_txs = [k for k, count in Counter(block).items() if count > 1]

    block_weight = 0
    block_fees = 0
    txs_in_block = []


    if duplicate_txs:
        print("Invalid block!")
        count = len(duplicate_txs)
        print("{} duplicate txs found: {}".format(count, duplicate_txs))
        sys.exit(1)

    for tx in block:
        if tx not in mempool.txs.keys():
            print("Invalid tx {} in block!".format(tx))
            sys.exit(1)
        for parent in mempool.txs[tx].parents:
            if parent not in txs_in_block:
                print("Block contains transaction {} with unconfirmed parent {}!".format(tx, parent))
                sys.exit(1)
        txs_in_block.append(tx)
        block_weight += mempool.txs[tx].weight
        block_fees += mempool.txs[tx].fee
    if block_weight > MAX_BLOCK_WEIGHT:
        print("Too large block! Weight: {}".format(block_weight))
        sys.exit(1)
    print("Valid block!\nTotal fees: {}\nTotal weight: {}".format(block_fees, block_weight))
    return 1


if __name__ == '__main__':
    MAX_BLOCK_WEIGHT = 4000000
    mempool = blockbuilder.Mempool()
    mempool.fromTXT(r"./data/data example/000000000000000000269e0949579bd98366bef1ca308d134182dbf28dc6fdef.mempool")
    block = readBlock(r"./results/2021-01-14T18.19.25.710629.byclusters")
    checkBlockValditiy(mempool,block)
