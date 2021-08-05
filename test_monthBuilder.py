import unittest
import blockbuilder as bb
import monthBuilder as mb

class TestmonthBuilder(unittest.TestCase):
    def test_loadingBlock(self):
        m = mb.Monthbuilder("./data/data_example/test")
        m.allowList = {1, 2, 3, 4}
        m.confirmedList = {1, 2}
        m.globalMempool = bb.Mempool()
        txDict = {1 : bb.Transaction(1, 1, 1), 2 : bb.Transaction(2,2,2)}
        m.globalMempool.fromDict(txDict)
        m.loadBlockMempool("test_block")
        print()


if __name__ == '__main__':
    unittest.main()