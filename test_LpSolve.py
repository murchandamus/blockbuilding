import unittest
import candidate_set_blockbuilder as bb
import LpSolve as lp
from collections import Counter

def checkBlockValditiy(mempool, block, MAX_BLOCK_WEIGHT):
    print('checking Block Validity')
    duplicate_txs = [k for k, count in Counter(block).items() if count > 1]

    block_weight = 0
    block_fees = 0
    txs_in_block = []


    if duplicate_txs:
        print("Invalid block!")
        count = len(duplicate_txs)
        print("{} duplicate txs found: {}".format(count, duplicate_txs))
        return 1

    for tx in block:
        if tx not in mempool.txs.keys():
            print("Invalid tx {} in block!".format(tx))
            sys.exit(1)
        for parent in mempool.txs[tx].parents:
            if parent not in txs_in_block:
                print("Block contains transaction {} with unconfirmed parent {}!".format(tx, parent))
                return 1
        txs_in_block.append(tx)
        block_weight += mempool.txs[tx].weight
        block_fees += mempool.txs[tx].fee
    if block_weight > MAX_BLOCK_WEIGHT:
        print("Too large block! Weight: {}".format(block_weight))
        return 1
    print("Valid block!\nTotal fees: {}\nTotal weight: {}".format(block_fees, block_weight))
    return 0


class TestLpSolver(unittest.TestCase):
    def setUp(self):
        self.mempool = bb.Mempool()
        self.mempool.txs = {'234': bb.Transaction('234', 100, 100, ['10423']),
                            '10423': bb.Transaction('10423', 10, 10)
                    }

    def test_blockBuildingIsCorrect(self):
        self.fee, self.weight, self.blockTxs, self.opt = lp.LinearProgrammingSolve(self.mempool.txs, 10, 'CBC', 1000)
        self.assertEqual(self.fee, 10)

    def test_OrderTxsForBlock(self):
        self.max_weight = 1000
        self.fee, self.weight, self.blockTxs, self.opt = lp.LinearProgrammingSolve(self.mempool.txs, self.max_weight,
                                                                                   'SAT', 1000)
        self.block = lp.create_block(self.blockTxs)
        self.assertEqual(checkBlockValditiy(self.mempool, self.block, self.max_weight), 0)

    def test_printToFile(self):
        self.max_weight = 1000
        self.fee, self.weight, self.blockTxs, self.opt = lp.LinearProgrammingSolve(self.mempool.txs, self.max_weight,
                                                                                   'CBC', 1000)
        lp.printToFile(self.blockTxs,self.weight,self.fee, 'test.txt', 'CBC', 'opt_test', '123')



if __name__ == '__main__':
    unittest.main()
