import unittest
import transaction
from mempool import Mempool
import ancestorBlockBuilder as abb

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

    def test_get_ancestors(self):
        mp = Mempool()
        mp.fromDict(self.testDict)

        ancBlockBuilder = abb.BlockbuilderByAnces(mp)
        ancestors = ancBlockBuilder.getAncestors(self.testDict["tuv"])

        self.assertEqual(ancestors, ["nop", "qrs", "tuv"])


if __name__ == '__main__':
    unittest.main()
