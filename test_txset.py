import unittest
from txset import TransactionSet
from transaction import Transaction
from mempool import Mempool

class TestTransactionSet(unittest.TestCase):
    def setUp(self):
        self.testDict = {
            "ZZZ": Transaction("ZZZ", 100, 100, []),
            "YYY": Transaction("YYY", 100, 100, []),
            "XXX": Transaction("XXX", 100, 100, []),
            'QQQ': Transaction('QQQ', 100, 100, ['ZZZ', 'YYY', 'XXX']),
            'PPP': Transaction('PPP', 100, 100, ['YYY']),
            'AAA': Transaction('AAA', 100, 100, ['QQQ']),
            'BBB': Transaction('BBB', 100, 100, []),
            'CCC': Transaction('CCC', 100, 100, [])
        }


    def test_get_topologically_sorted_txids(self):
        mempool = Mempool()
        mempool.fromDict(self.testDict) # needed to backfill relatives
        txset = TransactionSet(self.testDict)
        topo_sorted = txset.get_topologically_sorted_txids()
        self.assertSequenceEqual(topo_sorted, ['BBB', 'CCC', "XXX", "YYY", "ZZZ", 'PPP', 'QQQ', 'AAA'])
