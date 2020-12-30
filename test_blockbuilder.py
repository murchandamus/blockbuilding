import unittest
import blockbuilder

testDict = {
    "123": blockbuilder.Transaction("123", 100, 100, [], ["abc"]),
    "abc": blockbuilder.Transaction("abc", 100, 100, ["123"], []),
    "nop": blockbuilder.Transaction("nop", 1000, 100, [], ["qrs"]),  # medium feerate
    "qrs": blockbuilder.Transaction("qrs", 10000, 100, ["nop"], ["tuv"]),  # high feerate
    "tuv": blockbuilder.Transaction("tuv", 100, 100, ["qrs"], []),  # low feerate
    "xyz": blockbuilder.Transaction("xyz", 1, 1, [], [])
}


class TestBlockbuilder(unittest.TestCase):
    print("Test from JSON")

    def test_valid_candidate_set(self):
        blockbuilder.CandidateSet({"123": testDict["123"], "abc": testDict["abc"]})

    def test_missing_ancestor_candidate_set(self):
        self.assertRaises(TypeError, blockbuilder.CandidateSet, {"abc": testDict["abc"]})

    def test_candidate_set_get_weight(self):
        cand = blockbuilder.CandidateSet({"123": testDict["123"], "abc": testDict["abc"]})
        self.assertEqual(cand.getWeight(), 200)

    def test_candidate_set_get_fees(self):
        cand = blockbuilder.CandidateSet({"123": testDict["123"], "abc": testDict["abc"]})
        self.assertEqual(cand.getFees(), 200)

    def test_candidate_set_get_effective_feerate(self):
        cand = blockbuilder.CandidateSet({"123": testDict["123"], "abc": testDict["abc"]})
        self.assertEqual(cand.getEffectiveFeerate(), 1)

    def build_nop_cluster(self):
        cluster = blockbuilder.Cluster(testDict["nop"])
        cluster.addTx(testDict["qrs"])
        cluster.addTx(testDict["tuv"])

        return cluster

    def test_get_all_candidate_sets(self):
        cluster = self.build_nop_cluster()
        cluster.generateAllCandidateSets()
        expectedSets = [["nop"], ["nop", "qrs"], ["nop", "qrs", "tuv"]]

        for cand in cluster.candidates:
            self.assertEqual(True, sorted(cand.txs.keys()) in expectedSets)
            self.assertEqual(len(cluster.candidates), len(expectedSets))

    def test_get_best_candidate_set(self):
        cluster = self.build_nop_cluster()
        best = cluster.getBestCandidateSet()
        self.assertEqual(list(best.txs.keys()), ["nop", "qrs"])

    def test_get_best_candidate_set_with_limit(self):
        cluster = self.build_nop_cluster()
        best = cluster.getBestCandidateSet(100)
        self.assertEqual(list(best.txs.keys()), ["nop"])

    def test_parse_from_TXT(self):
        mempool = blockbuilder.Mempool()
        mempool.fromTXT("data/mempoolTXT")
        txids = [
            "01123eb3ec64c381ce29b98aa71a5998094054171c5b9a9e0f0084289ad2ccf6",
            "b5823eb3ec64c381ce29b98aa71a5998094054171c5b9a9e0f0084289ad2ccf6",
            "8a2ba899956359eb278f6daffc8ae0f5dfb631a67dbfe57687f665b20bcf063e"
        ]
        keys = mempool.getTxs().keys()
        for txid in txids:
            self.assertEqual(True, txid in keys)
            # self.assertEqual(True, len(txids) == len(keys))

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
                sorted(testDict["abc"].getLocalClusterTxids()),
                ["123", "abc"],
                "Should be ['123','abc']"
            )

    def test_mempool_cluster(self):
        print("Start mempool.cluster")
        mempool = blockbuilder.Mempool()
        mempool.fromDict(testDict)
        clusters = mempool.cluster()
        self.assertEqual(
                list(clusters["123"].txs.keys()),
                ["123", "abc"]
            )
        self.assertEqual(
                list(clusters["nop"].txs.keys()),
                ["nop", "qrs", "tuv"]
            )
        self.assertEqual(
                list(clusters["xyz"].txs.keys()),
                ["xyz"]
            )


if __name__ == '__main__':
    unittest.main()
