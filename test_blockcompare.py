import unittest
import XLSBlockCompare

class TestBlockcompare(unittest.TestCase):

    def test_getBlockDetailsFromFile(self):
        self.assertEqual(XLSBlockCompare.getBlockDetailsFromFile(r"./blockCompareTest/11111111.gbt"), ("100", "200"))

if __name__ == '__main__':
    unittest.main()