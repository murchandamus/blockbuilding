import unittest
from transaction import Transaction
from candidateset import CandidateSet

class TestCandidateSet(unittest.TestCase):
    def setUp(self):
        self.txA = Transaction('A', 150, 200, [], ["B"])
        self.txB = Transaction('B', 100, 100, ["A"], ["C"])
        self.txC = Transaction('C', 200, 150, ["B"], [])

        self.csA = CandidateSet({"A": self.txA})
        self.csAB = CandidateSet({"A": self.txA, "B": self.txB})

    def test_get_children(self):
        self.assertIn("C", self.csAB.getChildren())

    def test_get_effective_feerate(self):
        self.assertEqual(self.csAB.getEffectiveFeerate(), 5/6)

    def test_sorting(self):
        self.assertLess(self.csAB, self.csA)

if __name__ == '__main__':
    unittest.main()
