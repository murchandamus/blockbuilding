import unittest
import blockcompare

class TestBlockcompare(unittest.TestCase):

    def test_getBlockDetailsFromFile(self):
        self.assertEqual(blockcompare.getBlockDetailsFromFile(r"./blockCompareTest/11111111.gbt"), ("100", "200"))

if __name__ == '__main__':
    unittest.main()