import unittest
import blockbuilder

testDict = {
    "123": {"key": "value", "depends":  [], "spentby": ["abc"]},
    "abc": {"key": "otherValue", "depends":  ["123"], "spentby": []},
    "nop": {"key": "v4", "depends":  [], "spentby": ["qrs"]},
    "qrs": {"key": "baum", "depends":  ["nop"], "spentby": ["tuv"]},
    "tuv": {"key": "irgendwas", "depends":  ["qrs"], "spentby": []},
    "xyz": {"key": "v3", "depends":  [], "spentby": []},
}


class TestBlockbuilder(unittest.TestCase):
    def test_get_representative_tx(self):
        self.assertEqual(
                blockbuilder.getRepresentativeTxid(["qrs", "nop", "tuv"]),
                "nop",
                "Should be nop"
            )

    def getLocalClusterTxids(self):
        self.assertEqual(
                blockbuilder.getLocalClusterTxids("abc", testDict["abc"]),
                ["abc", "123"],
                "Should be ['abc', '123']"
            )


if __name__ == '__main__':
    unittest.main()
