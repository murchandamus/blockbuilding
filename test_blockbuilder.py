import unittest
import blockbuilder

testDict = {
    "abc":{"key":"otherValue", "depends": ["123"], "spentby":[]},
    "123":{"key":"value", "depends": [], "spentby":["abc"]},
    "nop":{"key":"v4", "depends": [], "spentby":["qrs"]},
    "qrs":{"key":"baum", "depends": ["nop"], "spentby":["tuv"]},
    "tuv":{"key":"irgendwas", "depends": ["qrs"], "spentby":[]},
    "xyz":{"key":"v3", "depends": [], "spentby":[]},
}

class TestBlockbuilder(unittest.TestCase):
    def test_get_representative_tx(self):
        self.assertEqual(blockbuilder.getRepresentativeTxid("qrs", testDict["qrs"]), "nop", "Should be nop")

    def getLocalClusterTxids(self):
        self.assertEqual(blockbuilder.getLocalClusterTxids("abc", testDict["abc"]) == ["abc", "123"], "Should be ['xyz', '123']")

if __name__ == '__main__':
    unittest.main()
