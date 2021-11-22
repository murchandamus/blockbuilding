import unittest
import blockbuilder
from mempool import Mempool

class TestBlockbuilder(unittest.TestCase):
    def setUp(self):
        self.testDict = {
            "123": blockbuilder.Transaction("123", 100, 100, [], ["abc"]),
            "abc": blockbuilder.Transaction("abc", 100, 100, ["123"], []),
            "nop": blockbuilder.Transaction("nop", 1000, 100, [], ["qrs"]),  # medium feerate
            "qrs": blockbuilder.Transaction("qrs", 10000, 100, ["nop"], ["tuv"]),  # high feerate
            "tuv": blockbuilder.Transaction("tuv", 100, 100, ["qrs"], []),  # low feerate
            "xyz": blockbuilder.Transaction("xyz", 10, 10, [], [])
        }

    def test_valid_candidate_set(self):
        blockbuilder.CandidateSet({"123": self.testDict["123"], "abc": self.testDict["abc"]})

    def test_missing_ancestor_candidate_set(self):
        self.assertRaises(TypeError, blockbuilder.CandidateSet, {"abc": self.testDict["abc"]})

    def test_candidate_set_equivalence(self):
        cs = blockbuilder.CandidateSet({"123": self.testDict["123"]})
        otherCs = blockbuilder.CandidateSet({"123": self.testDict["123"]})
        self.assertTrue(cs == otherCs)

    def test_fail_candidate_set_equivalence(self):
        cs = blockbuilder.CandidateSet({"nop": self.testDict["nop"]})
        otherCs = blockbuilder.CandidateSet({"123": self.testDict["123"]})
        self.assertFalse(cs == otherCs)

    def test_candidate_set_get_weight(self):
        cand = blockbuilder.CandidateSet({"123": self.testDict["123"], "abc": self.testDict["abc"]})
        self.assertEqual(cand.getWeight(), 200)

    def test_candidate_set_get_fees(self):
        cand = blockbuilder.CandidateSet({"123": self.testDict["123"], "abc": self.testDict["abc"]})
        self.assertEqual(cand.getFees(), 200)

    def test_candidate_set_get_effective_feerate(self):
        cand = blockbuilder.CandidateSet({"123": self.testDict["123"], "abc": self.testDict["abc"]})
        self.assertEqual(cand.getEffectiveFeerate(), 1)

    def test_candidate_set_get_effective_feerate_can_be_float(self):
        cand = blockbuilder.CandidateSet({"123": self.testDict["123"], "abc": self.testDict["abc"]})
        self.testDict['123'].fee = 25
        print('cand for feeRate: '  +  str(cand))
        self.assertEqual(cand.getEffectiveFeerate(), 0.625)

    def build_nop_cluster(self):
        cluster = blockbuilder.Cluster(self.testDict["nop"], 4000000)
        cluster.addTx(self.testDict["qrs"])
        cluster.addTx(self.testDict["tuv"])

        return cluster

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

    def build_chain_test_cluster(self):
        mempool = Mempool()
        mempool.fromTXT('data/chain-test-txt')
        mempool.cluster(4000000)
        cluster = list(mempool.clusters.values())[0]
        return cluster

    def test_get_best_candidate_set_from_chain(self):
        cluster = self.build_chain_test_cluster()
        best = cluster.getBestCandidateSet(4000000)
        self.assertEqual(sorted(list(best.txs.keys())), sorted(['925430489ec6f25adb29791a78d3babd6a14e28f6269420f2b1a2bea6b11fabf', '15f869b24e302476ac34808fee17999dcebabb62810ebb2ba0bdf89ad7f5911a', 'e1d1f387037ec41e6402443af85fb21d24d0dcc2b49586691155df9de726c12a', '1128396e2dd2422c32324c0f08b36c0e17babd85b7478b7a2c56bb2a4ac01b29', 'f7c2abf0e8c0d553c539cf969ef473c0ae34c535277e23265275ed22fde5adb4', 'ba1d0c2de4ab4881eaffcc2b95e94ca311d909fe35d7fc1902a78750d62351b8', 'ac8b50ccd4d90fa644c74a824548350b50f56e81b44a5a89136426d8de313487', '5607f6afe932bafdaaa94dc1fa28d0b2c2551d06ca61d8694ccf9e7a55fafaa2', 'ec6d8786811fbdc073af11fffa98d1a403d029e3a978584c7d2dc1a4dbe15038', '2103e604004fafca7df052b4d020009510f95081707de994b57e2a5ed4bcd657', '68cf60a0b02c220088be658b1977fa6ac6ef76bf7e0621f03cc5bbf28770ba37', 'd708375f16e1ec4841b15a08223761b023e72dd3b7bd531fe274722e0f64e2b4', '2e0019a8eaed554ff3deed3c7c35b1de1df902e93037eb8d134aa3f4230a5294', '927ba7496ec4f31351a65a7bed7b8374b1b03fd7364f67409c1932e1fc974bfa', 'c8ae62b8fa5b1426ef00f910ca2a03fcd6779ae1c992da8a589164885b81c084', '3c53e6a6d0f0d6ad0ceadf78327de056dd5d9b3a4620a592f167ad4c4a5368ab', '3641ff40d72755bb21e1723760dff01e694bde0d63c1e832674d6b42dfd68612', 'a37afe12598765bf8d1b21df67cb7f1349ac8c532616557406eaa95468858e8a', 'bd402b34d3bf63df0f8f757b84d028357e21451c32b1eecca7f170cfdc82b275', '78883f19535da8b84d3a6b898758655db0351e2364598aa409c51c32ca7d8850', '5e14ac2898f94aaa55fea7e53209ac65518b4403d236ee94731df9c005d1c3f9', 'e2cb5ee051eb1253c14c84942721d94ef7b60b47e4a0f7354bac8813c340a442', 'afeedede76627dc09d7052996e2bbfd5438edd046c8a82b936b802fbd631d305', '9463c589ab88033f5e00a0e53193c3c06faf87abea5ce520004947fa3f938804', 'cbf1221b317700e958c0f46e6162fe1965967b66b552c9be8fc60aa04fbeaf1c']))

    def test_get_best_candidate_set_from_siblings(self):
        mempool = Mempool()
        mempool.fromTXT('data/sibling-test-txt')
        mempool.cluster(4000000)
        cluster = list(mempool.clusters.values())[0]
        best = cluster.getBestCandidateSet(4000000)
        self.assertEqual(sorted(list(best.txs.keys())), ['06447a0e3dc38315188fc177907aa44417dfdd3e9ff41c5c50dc4447348852fa', '52613203575dc68fe20557c74776e909caede0c64ec75e4cc418461b6fc63777', '550ee342c094d95e5f9df931bdc5d86ab5eb0b4abdc9cfd137ceacef605ad69f', '64975313b72229a42d8a46fd45c3c3934f40751abc01a7d7067d9f472bc64ff2', 'b5ba0f7d66b424dcadea561555e1dc4aa20e694271f8db1d046065c92a8861bd', 'bf4a1a9d9844398a96cb6b57f5d2d65bc97c1c2314141bf9db857afa77a38971', 'da049e0b90cbff900678c44eb6b87d8be3c4c32b617862b5df6ddcb1a54991f6', 'f4745ca47ce9c552db574e36744d7f3f3bf961fd03541c8ba4c31f1ee86e243c'])

    def test_build_block_template_from_siblings(self):
        mempool = Mempool()
        mempool.fromTXT('data/sibling-test-txt')

        builder = blockbuilder.Blockbuilder(mempool)
        selectedTxs = builder.buildBlockTemplate()
        print(str(selectedTxs))

    def test_get_best_candidate_set_with_limit(self):
        cluster = self.build_nop_cluster()
        best = cluster.getBestCandidateSet(100)
        self.assertEqual(list(best.txs.keys()), ["nop"])

    def test_parse_from_TXT(self):
        mempool = Mempool()
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
            mempool = Mempool()
            print("Start parsing mempool file")
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
                sorted(self.testDict["abc"].getLocalClusterTxids()),
                ["123", "abc"],
                "Should be ['123','abc']"
            )

    def test_mempool_cluster(self):
        print("Start mempool.cluster")
        mempool = Mempool()
        mempool.fromDict(self.testDict)
        clusters = mempool.cluster(4000000)
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

    def test_pop_best_candidate_set(self):
        mempool = Mempool()
        mempool.fromDict(self.testDict)

        bestCandidateSet = mempool.popBestCandidateSet(4000000)
        expectedTxids = ["nop", "qrs"]

        self.assertEqual(len(bestCandidateSet.txs), 2)
        self.assertListEqual(sorted(list(bestCandidateSet.txs.keys())), expectedTxids)
        for txid in expectedTxids:
            self.assertNotIn(txid, mempool.txs.keys())

    def test_pop_best_candidate_set_low_weight(self):
        mempool = Mempool()
        mempool.fromDict(self.testDict)

        bestCandidateSet = mempool.popBestCandidateSet(5)

        self.assertEqual(bestCandidateSet, None)

    def test_build_block_template(self):
        mempool = Mempool()
        mempool.fromDict(self.testDict)

        builder = blockbuilder.Blockbuilder(mempool)
        selectedTxs = builder.buildBlockTemplate()
        print(str(selectedTxs))

    def test_output_block_template(self):
        print("not tested yet")

    def test_build_block_template_empty_mempool(self):
        mempool = Mempool()
        mempool.fromDict({})
        builder = blockbuilder.Blockbuilder(mempool)
        selectedTxs = builder.buildBlockTemplate()

    def test_drop_tx(self):
        mempool = Mempool()
        mempool.fromDict(self.testDict)
        self.assertIn('qrs', mempool.txs.keys())
        mempool.dropTx('qrs')
        self.assertNotIn('qrs', mempool.txs.keys())
        self.assertNotIn('qrs', mempool.txs['nop'].children)
        self.assertIn('qrs', mempool.txs['tuv'].parents)

    def test_drop_tx_called_twice_throws(self):
        mempool = Mempool()
        mempool.fromDict(self.testDict)
        self.assertIn('qrs', mempool.txs.keys())
        mempool.dropTx('qrs')
        self.assertNotIn('qrs', mempool.txs.keys())
        with self.assertRaises(KeyError):
            mempool.dropTx('qrs')

    def test_remove_confirmed_tx(self):
        mempool = Mempool()
        mempool.fromDict(self.testDict)
        self.assertIn('qrs', mempool.txs.keys())
        mempool.removeConfirmedTx('qrs')
        self.assertNotIn('qrs', mempool.txs.keys())
        with self.assertRaises(KeyError):
            mempool.removeConfirmedTx('qrs')

if __name__ == '__main__':
    unittest.main()
