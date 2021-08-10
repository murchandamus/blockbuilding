import unittest
import blockbuilder as bb
import monthBuilder as mb


class TestmonthBuilder(unittest.TestCase):
    def setUp(self):
        self.mobu = mb.Monthbuilder("./persistenceTestData")
        self.testDict = {'1' : bb.Transaction(1, 1, 1), '2' : bb.Transaction(2,2,2)}

    def test_load_allow_set(self):
        self.mobu.loadAllowSet()
        expectedAllowSet= {'1', '2', '3'}
        self.assertSetEqual(self.mobu.allowSet, expectedAllowSet)

    def test_loadingBlock(self):
        self.mobu.allowSet = {'1', '2', '3'}
        self.mobu.loadBlockMempool('100001_000aaa')
        expectedMempool = {'1', '2', '3'}
        self.assertSetEqual(set(self.mobu.globalMempool.txs.keys()), expectedMempool)

    def test_pruning_via_used_list(self):
        self.mobu.allowSet = {'1', '2', '3'}
        self.mobu.usedTxSet = {'1'}
        self.mobu.loadBlockMempool('100001_000aaa')
        self.assertNotIn('1', self.mobu.globalMempool.txs.keys())
        self.assertIn('2', self.mobu.globalMempool.txs.keys())
        self.assertIn('3', self.mobu.globalMempool.txs.keys())

    def test_global_mempool_persistence(self):
        self.mobu.allowSet = {'1', '2', '3'}
        self.mobu.globalMempool.fromDict(self.testDict) # loads 1, 2
        self.assertIn('1', self.mobu.globalMempool.txs.keys())
        self.assertIn('2', self.mobu.globalMempool.txs.keys())
        self.assertNotIn('3', self.mobu.globalMempool.txs.keys())
        self.mobu.loadBlockMempool('100002_000abc') # loads only 3
        self.assertIn('1', self.mobu.globalMempool.txs.keys())
        self.assertIn('2', self.mobu.globalMempool.txs.keys())
        self.assertIn('3', self.mobu.globalMempool.txs.keys())

    def test_pruning_via_allow_set(self):
        self.mobu = mb.Monthbuilder("./persistenceTestData")
        self.mobu.allowSet = {'1', '3'}
        self.mobu.loadBlockMempool('100001_000aaa')
        self.assertIn('1', self.mobu.globalMempool.txs.keys())
        self.assertNotIn('2', self.mobu.globalMempool.txs.keys())
        self.assertIn('3', self.mobu.globalMempool.txs.keys())

    def test_month_builder_full_cycle(self):
        self.mobu.loadAllowSet()
        self.assertSetEqual(self.mobu.allowSet, {'1','2','3'})
        self.mobu.usedTxSet = set()
        self.mobu.loadCoinbaseSizes()
        self.assertEqual(self.mobu.height, -1)
        self.mobu.getNextBlockHeight()
        self.assertEqual(self.mobu.height, 100001)
        self.mobu.loadBlockMempool('100001_000aaa') # loads 1, 2, 3
        self.assertSetEqual(set(self.mobu.globalMempool.txs.keys()), {'1','2','3'})
        self.mobu.runBlockWithGlobalMempool()
        self.mobu.getNextBlockHeight()
        self.assertEqual(self.mobu.height, 100002)
        self.assertSetEqual(self.mobu.usedTxSet, {'1'})
        self.mobu.loadBlockMempool('100002_000abc') # loads only 3
        self.assertSetEqual(set(self.mobu.globalMempool.txs.keys()), {'2','3'})
        self.assertSetEqual(self.mobu.allowSet, {'1','2','3'})
        self.assertSetEqual(self.mobu.usedTxSet, {'1'})
        self.mobu.runBlockWithGlobalMempool()
        self.assertSetEqual(self.mobu.usedTxSet, {'1', '2', '3'})

if __name__ == '__main__':
    unittest.main()
