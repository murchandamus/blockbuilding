import unittest
from transaction import Transaction

class TestTransaction(unittest.TestCase):
    def setUp(self):
        self.txA = Transaction("A", 200, 230, [], ["B"])
        self.txB = Transaction("B", 500, 250, ["A"], [])
        self.txC = Transaction("C", 400, 200, [], [])

        self.txAStar = Transaction("A", 100, 130, [], [])

    def test_sorting(self):
        txs = [self.txA, self.txB, self.txC]
        txs.sort()

        self.assertEqual([self.txB, self.txC, self.txA], txs)

    def test_equality(self):
        self.assertEqual(self.txA, self.txAStar)

    def test_inequality(self):
        self.assertNotEqual(self.txA, self.txB)

    def test_get_local_cluster_single_tx(self):
        cluster_c = self.txC.getLocalClusterTxids()
        self.assertEqual(len(cluster_c), 1)
        self.assertIn('C', cluster_c)

    def test_get_local_cluster_multiple_txs(self):
        cluster_A = set(self.txA.getLocalClusterTxids())
        cluster_B = set(self.txA.getLocalClusterTxids())
        self.assertIn('A', cluster_A)
        self.assertIn('B', cluster_A)
        self.assertEqual(len(cluster_A), 2)
        self.assertSetEqual(cluster_A, cluster_B)

if __name__ == '__main__':
    unittest.main()
