import unittest
import blockbuilder

testDict = {
    "123": {"somekey": "value", "depends":  [], "spentby": ["abc"]},
    "abc": {"somekey": "otherValue", "depends":  ["123"], "spentby": []},
    "nop": {"somekey": "v4", "depends":  [], "spentby": ["qrs"]},
    "qrs": {"somekey": "baum", "depends":  ["nop"], "spentby": ["tuv"]},
    "tuv": {"somekey": "irgendwas", "depends":  ["qrs"], "spentby": []},
    "xyz": {"somekey": "v3", "depends":  [], "spentby": []},
}


class TestBlockbuilder(unittest.TestCase):
    print("Test from JSON")

    def test_parse_mempool_class(self):
        mempool = blockbuilder.mempool()
        print("Start parseMempoolFile")
        mempool.fromJSON("data/mini-mempool.json")
        txids = [
            "a5823eb3ec64c381ce29b98aa71a5998094054171c5b9a9e0f0084289ad2ccf6",
            "9a9b73b2a6ea86a495662d5e90cda9fadbf70c470231dff6b4f9286707f30812",
            "154ff366005101ed97c044782d82e3abf44073968bd0db21c9f5b27296aa3de2",
            "6a2ba899956359eb278f6daffc8ae0f5dfb631a67dbfe57687f665b20bcf063e"
        ]

        keys = mempool.getTxs().keys()
        for txid in txids:
            self.assertEqual(True, txid in keys)

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
                blockbuilder.getLocalClusterTxids("abc", testDict["abc"]),
                ["abc", "123"],
                "Should be ['abc', '123']"
            )

    def test_cluster_tx(self):
        print("Start clusterTx")
        self.assertDictEqual(
                blockbuilder.clusterTx("abc", testDict["abc"], {}, {}),
                {"123": ["123", "abc"]}
            )

    def test_parse_mempool_file(self):
        print("Start parseMempoolFile")
        clusters = blockbuilder.parseMempoolFile("data/mini-mempool.json")
        self.assertDictEqual(
            clusters,
            {
                "154ff366005101ed97c044782d82e3abf44073968bd0db21c9f5b27296aa3de2":
                [
                    "a5823eb3ec64c381ce29b98aa71a5998094054171c5b9a9e0f0084289ad2ccf6",
                    "9a9b73b2a6ea86a495662d5e90cda9fadbf70c470231dff6b4f9286707f30812",
                    "154ff366005101ed97c044782d82e3abf44073968bd0db21c9f5b27296aa3de2",
                    "6a2ba899956359eb278f6daffc8ae0f5dfb631a67dbfe57687f665b20bcf063e"
                ]
            }
        )


if __name__ == '__main__':
    unittest.main()
