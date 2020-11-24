import unittest
import blockbuilder

testDict = {
    "acb":{"key":"otherValue", "depends": ["123"], "spentby":[]},
    "123":{"key":"value", "depends": [], "spentby":["abc"]},
    "abc":{"key":"v3", "depends": [], "spentby":[]},
}

class TestBlockbuilder(unittest.TestCase):
    def test_get_representative_tx(self):
            self.assertEqual(blockbuilder.getRepresentativeTx(testDict), "123", "Should be 123")

    def getLocalClusterTxids(self):
        self.assertEqual(blockbuilder.getLocalClusterTxids("acb", testDict["acb"]) == ["acb", "123"], "Should be ['abc', '123']")

if __name__ == '__main__':
    unittest.main()
