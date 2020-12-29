import unittest
import blockbuilder

testDict = {
    "123": blockbuilder.Transaction("123", 100, 100, [], ["abc"]),
    "abc": blockbuilder.Transaction("abc", 100, 100, ["123"], []),
    "nop": blockbuilder.Transaction("nop", 100, 100, [], ["qrs"]),
    "qrs": blockbuilder.Transaction("qrs", 1, 1, ["nop"], ["tuv"]),
    "tuv": blockbuilder.Transaction("tuv", 1, 1, ["qrs"], []),
    "xyz": blockbuilder.Transaction("xyz", 1, 1, [], [])
}


class TestBlockbuilder(unittest.TestCase):
    print("Test from JSON")

    def test_parse_mempool_class(self):
        mempool = blockbuilder.Mempool()
        print("Start parseMempoolFile")
        mempool.fromJSON("data/mini-mempool.json")
        txids = [
            "a5823eb3ec64c381ce29b98aa71a5998094054171c5b9a9e0f0084289ad2ccf6",
            "b5823eb3ec64c381ce29b98aa71a5998094054171c5b9a9e0f0084289ad2ccf6",
            "9a9b73b2a6ea86a495662d5e90cda9fadbf70c470231dff6b4f9286707f30812",
            "154ff366005101ed97c044782d82e3abf44073968bd0db21c9f5b27296aa3de2",
            "6a2ba899956359eb278f6daffc8ae0f5dfb631a67dbfe57687f665b20bcf063e"
        ]

        keys = mempool.getTxs().keys()
        for txid in txids:
            self.assertEqual(True, txid in keys)

    def test_cluster(self):
        print("not tested yet")

    def test_get_representative_tx(self):
        print("repTx")
        self.assertEqual(
                blockbuilder.getRepresentativeTxid(["qrs", "nop", "tuv"]),
                "nop",
                "Should be nop"
            )

    def test_get_local_cluster_txids(self):
        print("localcluster")
        self.assertEqual(
                testDict["abc"].getLocalClusterTxids(),
                ["123", "abc"],
                "Should be ['123','abc']"
            )

    def test_cluster_tx(self):
        print("Start clusterTx")
        self.assertDictEqual(
                blockbuilder.clusterTx(testDict["abc"], {}, {}),
                {"123": ["123", "abc"]}
            )
        self.assertDictEqual(
                blockbuilder.clusterTx(testDict["qrs"], {}, {}),
                {"nop": ["nop", "qrs", "tuv"]}
            )


if __name__ == '__main__':
    unittest.main()
