import unittest
from candidateset import CandidateSet
from transaction import Transaction

class TestCandidateSet(unittest.TestCase):
    def setUp(self):
        self.testDict = {
            "123": Transaction("123", 100, 100, [], ["abc"]),
            "abc": Transaction("abc", 100, 100, ["123"], []),
            "nop": Transaction("nop", 1000, 100, [], ["qrs"]),  # medium feerate
            "qrs": Transaction("qrs", 10000, 100, ["nop"], ["tuv"]),  # high feerate
            "tuv": Transaction("tuv", 100, 100, ["qrs"], []),  # low feerate
            "xyz": Transaction("xyz", 10, 10, [], [])
        }

    def test_valid_candidate_set(self):
        CandidateSet({"123": self.testDict["123"], "abc": self.testDict["abc"]})

    def test_missing_ancestor_candidate_set(self):
        self.assertRaises(TypeError, CandidateSet, {"abc": self.testDict["abc"]})

    def test_candidate_set_equivalence(self):
        cs = CandidateSet({"123": self.testDict["123"]})
        other = CandidateSet({"123": self.testDict["123"]})
        self.assertTrue(cs == other)

    def test_fail_candidate_set_equivalence(self):
        cs = CandidateSet({"nop": self.testDict["nop"]})
        other = CandidateSet({"123": self.testDict["123"]})
        self.assertFalse(cs == other)

    def test_candidate_set_get_weight(self):
        cand = CandidateSet({"123": self.testDict["123"], "abc": self.testDict["abc"]})
        self.assertEqual(cand.get_weight(), 200)

    def test_candidate_set_get_fees(self):
        cand = CandidateSet({"123": self.testDict["123"], "abc": self.testDict["abc"]})
        self.assertEqual(cand.get_fees(), 200)

    def test_candidate_set_get_effective_feerate(self):
        cand = CandidateSet({"123": self.testDict["123"], "abc": self.testDict["abc"]})
        self.assertEqual(cand.get_feerate(), 1)

    def test_candidate_set_get_effective_feerate_can_be_float(self):
        cand = CandidateSet({"123": self.testDict["123"], "abc": self.testDict["abc"]})
        self.testDict['123'].fee = 25
        print('cand for feeRate: '  +  str(cand))
        self.assertEqual(cand.get_feerate(), 0.625)

if __name__ == '__main__':
    unittest.main()
