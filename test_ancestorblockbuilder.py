import unittest
import blockbuilder
import ancestorBlockBuilder as abb

class TestBlockbuilderByAnces(unittest.TestCase):
    def setUp(self):
        self.testDict = {
            "123": blockbuilder.Transaction("123", 100, 100, [], ["abc"]),
            "abc": blockbuilder.Transaction("abc", 100, 100, ["123"], []),
            "nop": blockbuilder.Transaction("nop", 1000, 100, [], ["qrs"]),  # medium feerate
            "qrs": blockbuilder.Transaction("qrs", 10000, 100, ["nop"], ["tuv"]),  # high feerate
            "tuv": blockbuilder.Transaction("tuv", 100, 100, ["qrs"], []),  # low feerate
            "xyz": blockbuilder.Transaction("xyz", 10, 10, [], [])
        }

    def test_get_ancestors(self):
        mp = blockbuilder.Mempool()
        mp.fromDict(self.testDict)

        ancBlockBuilder = abb.BlockbuilderByAnces(mp)
        ancestors = ancBlockBuilder.getAncestors(self.testDict["tuv"])

        self.assertEqual(ancestors, ["nop", "qrs", "tuv"])


if __name__ == '__main__':
    unittest.main()
