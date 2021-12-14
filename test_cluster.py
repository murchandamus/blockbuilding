import unittest
from cluster import Cluster
from transaction import Transaction

class TestCluster(unittest.TestCase):
    def setUp(self):
        self.testDict = {
            "123": Transaction("123", 100, 100, [], ["abc"]),
            "abc": Transaction("abc", 100, 100, ["123"], []),
            "nop": Transaction("nop", 1000, 100, [], ["qrs"]),  # medium feerate
            "qrs": Transaction("qrs", 10000, 100, ["nop"], ["tuv"]),  # high feerate
            "tuv": Transaction("tuv", 100, 100, ["qrs"], []),  # low feerate
            "xyz": Transaction("xyz", 10, 10, [], [])
        }

    def build_nop_cluster(self):
        cluster = Cluster(self.testDict["nop"], 4000000)
        cluster.addTx(self.testDict["qrs"])
        cluster.addTx(self.testDict["tuv"])

        return cluster

    def test_get_best_candidate_set_with_limit(self):
        cluster = self.build_nop_cluster()
        best = cluster.getBestCandidateSet(100)
        self.assertEqual(list(best.txs.keys()), ["nop"])

    def test_assemble_ancestry(self):
        cluster = self.build_nop_cluster()
        nopAS = cluster.assembleAncestry('nop')
        self.assertTrue('nop' in nopAS.txs.keys())

        qrsAS = cluster.assembleAncestry('qrs')
        self.assertTrue('nop' in qrsAS.txs.keys())
        self.assertTrue('qrs' in qrsAS.txs.keys())

    def test_get_best_candidate_set(self):
        cluster = self.build_nop_cluster()
        best = cluster.getBestCandidateSet(4000000)
        self.assertEqual(sorted(list(best.txs.keys())), ["nop", "qrs"])

    def test_remove_candidate_set_links(self):
        cluster = self.build_nop_cluster()
        best = cluster.getBestCandidateSet(4000000)
        cluster.removeCandidateSetLinks(best)
        for txid, tx in cluster.txs.items():
            print(tx)

if __name__ == '__main__':
    unittest.main()
