import unittest
import transaction
from mempool import Mempool
from ancestor_set import AncestorSet
from ancestorBlockBuilder import BlockbuilderByAnces


class TestBlockbuilderByAnces(unittest.TestCase):
    def setUp(self):
        self.testDict = {
            "123": transaction.Transaction("123", 100, 100, [], ["abc"]),
            "abc": transaction.Transaction("abc", 100, 100, ["123"], []),
            "nop": transaction.Transaction("nop", 1000, 100, [], ["qrs"]),  # medium feerate
            "qrs": transaction.Transaction("qrs", 10000, 100, ["nop"], ["tuv"]),  # high feerate
            "tuv": transaction.Transaction("tuv", 100, 100, ["qrs"], []),  # low feerate
            "xyz": transaction.Transaction("xyz", 10, 10, [], [])
        }

    def test_initialize_stubs(self):
        self.mempool = Mempool()
        self.mempool.fromDict(self.testDict)
        builder = BlockbuilderByAnces(self.mempool)
        builder.initialize_stubs()

        self.assertEqual(len(builder.ancestorSets), len(self.testDict))
        self.assertEqual(len(builder.txAncestorSetMap), len(self.testDict))
        nopAS = builder.txAncestorSetMap['nop']
        self.assertFalse(nopAS.isComplete)

    def test_backfill_incomplete_ancestor_set(self):
        self.mempool = Mempool()
        self.mempool.fromDict(self.testDict)
        builder = BlockbuilderByAnces(self.mempool)

        qrs_AS = AncestorSet(self.testDict['qrs'])
        self.assertFalse(qrs_AS.isComplete)
        self.assertEqual(len(qrs_AS.txs), 1)

        builder.backfill_incomplete_ancestor_set(qrs_AS)
        self.assertTrue(qrs_AS.isComplete)
        self.assertEqual(len(qrs_AS.txs), 2)


    def test_build_block_template(self):
        self.mempool = Mempool()
        self.mempool.fromDict(self.testDict)
        builder = BlockbuilderByAnces(self.mempool)
        selectedTxs = builder.buildBlockTemplate()
        resultingBlock = str(selectedTxs)

        self.assertEqual("['nop', 'qrs', '123', 'abc', 'tuv', 'xyz']", resultingBlock)


if __name__ == '__main__':
    unittest.main()
