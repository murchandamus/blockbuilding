import unittest
import transaction
from mempool import Mempool
from ancestorBlockBuilder import BlockbuilderByAnces


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


if __name__ == '__main__':
    unittest.main()
