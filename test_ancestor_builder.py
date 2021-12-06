import unittest
import transaction
from mempool import Mempool
from ancestor_set import AncestorSet
from ancestor_builder import AncestorSetBlockbuilder


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

    def test_initialize_stubs(self):
        self.mempool = Mempool()
        self.mempool.fromDict(self.testDict)
        builder = AncestorSetBlockbuilder(self.mempool)
        builder.initialize_stubs()

        self.assertEqual(len(builder.ancestorSets), len(self.testDict))
        self.assertEqual(len(builder.txAncestorSetMap), len(self.testDict))
        nopAS = builder.txAncestorSetMap['nop']
        self.assertFalse(nopAS.isComplete)

    def test_backfill_incomplete_ancestor_set(self):
        self.mempool = Mempool()
        self.mempool.fromDict(self.testDict)
        builder = AncestorSetBlockbuilder(self.mempool)

        qrs_AS = AncestorSet(self.testDict['qrs'])
        self.assertFalse(qrs_AS.isComplete)
        self.assertEqual(len(qrs_AS.txs), 1)

        builder.backfill_incomplete_ancestor_set(qrs_AS)
        self.assertTrue(qrs_AS.isComplete)
        self.assertEqual(len(qrs_AS.txs), 2)


    def test_build_block_template(self):
        self.mempool = Mempool()
        self.mempool.fromDict(self.testDict)
        builder = AncestorSetBlockbuilder(self.mempool)
        selectedTxs = builder.buildBlockTemplate()
        resultingBlock = str(selectedTxs)

        self.assertEqual("['nop', 'qrs', '123', 'abc', 'tuv', 'xyz']", resultingBlock)

    def test_build_block_template_from_chain(self):
        mempool = Mempool()
        mempool.fromTXT('data/chain-test-txt')

        builder = AncestorSetBlockbuilder(mempool)
        selectedTxs = builder.buildBlockTemplate()
        resultingBlock = str(selectedTxs)
        self.assertEqual("['d708375f16e1ec4841b15a08223761b023e72dd3b7bd531fe274722e0f64e2b4', '68cf60a0b02c220088be658b1977fa6ac6ef76bf7e0621f03cc5bbf28770ba37', '2103e604004fafca7df052b4d020009510f95081707de994b57e2a5ed4bcd657', 'ec6d8786811fbdc073af11fffa98d1a403d029e3a978584c7d2dc1a4dbe15038', '5607f6afe932bafdaaa94dc1fa28d0b2c2551d06ca61d8694ccf9e7a55fafaa2', 'ac8b50ccd4d90fa644c74a824548350b50f56e81b44a5a89136426d8de313487', 'ba1d0c2de4ab4881eaffcc2b95e94ca311d909fe35d7fc1902a78750d62351b8', 'f7c2abf0e8c0d553c539cf969ef473c0ae34c535277e23265275ed22fde5adb4', '1128396e2dd2422c32324c0f08b36c0e17babd85b7478b7a2c56bb2a4ac01b29', 'e1d1f387037ec41e6402443af85fb21d24d0dcc2b49586691155df9de726c12a', '15f869b24e302476ac34808fee17999dcebabb62810ebb2ba0bdf89ad7f5911a', '925430489ec6f25adb29791a78d3babd6a14e28f6269420f2b1a2bea6b11fabf', '2e0019a8eaed554ff3deed3c7c35b1de1df902e93037eb8d134aa3f4230a5294', '927ba7496ec4f31351a65a7bed7b8374b1b03fd7364f67409c1932e1fc974bfa', 'c8ae62b8fa5b1426ef00f910ca2a03fcd6779ae1c992da8a589164885b81c084', '3c53e6a6d0f0d6ad0ceadf78327de056dd5d9b3a4620a592f167ad4c4a5368ab', '3641ff40d72755bb21e1723760dff01e694bde0d63c1e832674d6b42dfd68612', 'a37afe12598765bf8d1b21df67cb7f1349ac8c532616557406eaa95468858e8a', 'bd402b34d3bf63df0f8f757b84d028357e21451c32b1eecca7f170cfdc82b275', '78883f19535da8b84d3a6b898758655db0351e2364598aa409c51c32ca7d8850', '5e14ac2898f94aaa55fea7e53209ac65518b4403d236ee94731df9c005d1c3f9', 'e2cb5ee051eb1253c14c84942721d94ef7b60b47e4a0f7354bac8813c340a442', 'afeedede76627dc09d7052996e2bbfd5438edd046c8a82b936b802fbd631d305', '9463c589ab88033f5e00a0e53193c3c06faf87abea5ce520004947fa3f938804', 'cbf1221b317700e958c0f46e6162fe1965967b66b552c9be8fc60aa04fbeaf1c']", resultingBlock)

"""
    def test_build_block_template_from_siblings(self):
        mempool = Mempool()
        mempool.fromTXT('data/sibling-test-txt')

        builder = AncestorSetBlockbuilder(mempool)
        selectedTxs = builder.buildBlockTemplate()
        resultingBlock = str(selectedTxs)
        self.assertEqual("['da049e0b90cbff900678c44eb6b87d8be3c4c32b617862b5df6ddcb1a54991f6', 'bf4a1a9d9844398a96cb6b57f5d2d65bc97c1c2314141bf9db857afa77a38971', '550ee342c094d95e5f9df931bdc5d86ab5eb0b4abdc9cfd137ceacef605ad69f', '06447a0e3dc38315188fc177907aa44417dfdd3e9ff41c5c50dc4447348852fa', 'f4745ca47ce9c552db574e36744d7f3f3bf961fd03541c8ba4c31f1ee86e243c', '52613203575dc68fe20557c74776e909caede0c64ec75e4cc418461b6fc63777', '64975313b72229a42d8a46fd45c3c3934f40751abc01a7d7067d9f472bc64ff2', 'b5ba0f7d66b424dcadea561555e1dc4aa20e694271f8db1d046065c92a8861bd', 'cdbeeb0ed4d57d61aa5c5abfea77bc534279bca52dfdfbdaccfb6215b9f2e671', '3b7ebb6deb35b028c745463a1ec9c71ff64b6149092470fd6b656e2531f76c15', 'b80f4216bdcd757878f502133b75b307edbf25c6aba302fa9777705368431e73', 'c6ba1e1b5bb32ffdfff3407b39c93cfe8d7a4aa5375a85ad151046854ae3d14a', 'fd3fffb77c88851c25ff2b0b777f4350de88e85a3a5a8b464fe4ff23674d3762', '50db94c2e73bbb42b6be887671176645b10c0b440578f90fb0c879a0879c000d', '41825e710a396b3cf9e3f9faa511880840692575c4c4b31cc83180f64a5a1f9d', '6a3da52b446d01a78c01fa470036cc198b93ecba5e1b6c9f2ebcd6f94d247ee4']", resultingBlock)

    def test_get_best_ancestor_set_from_siblings(self):
        mempool = Mempool()
        mempool.fromTXT('data/sibling-test-txt')
        bb = AncestorSetBlockbuilder(mempool, 4000000)
        self.assertEqual(sorted(list(best.txs.keys())), ['06447a0e3dc38315188fc177907aa44417dfdd3e9ff41c5c50dc4447348852fa', '52613203575dc68fe20557c74776e909caede0c64ec75e4cc418461b6fc63777', '550ee342c094d95e5f9df931bdc5d86ab5eb0b4abdc9cfd137ceacef605ad69f', '64975313b72229a42d8a46fd45c3c3934f40751abc01a7d7067d9f472bc64ff2', 'b5ba0f7d66b424dcadea561555e1dc4aa20e694271f8db1d046065c92a8861bd', 'bf4a1a9d9844398a96cb6b57f5d2d65bc97c1c2314141bf9db857afa77a38971', 'da049e0b90cbff900678c44eb6b87d8be3c4c32b617862b5df6ddcb1a54991f6', 'f4745ca47ce9c552db574e36744d7f3f3bf961fd03541c8ba4c31f1ee86e243c'])
"""

if __name__ == '__main__':
    unittest.main()
