import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from lambda_function.handler import extract_data

class TestExtractData(unittest.TestCase):
    def test_extract_single_username(self):
        text = "alice++"
        expected = {'alice': 1}
        result = extract_data(text)
        self.assertEqual(expected, result)

    def test_extract_multiple_different_usernames(self):
        text = "alice++ bob++"
        expected = {'alice': 1, 'bob': 1}
        result = extract_data(text)
        self.assertEqual(expected, result)

    def test_extract_multiple_same_usernames(self):
        text = "alice++ alice++"
        expected = {'alice': 2}
        result = extract_data(text)
        self.assertEqual(expected, result)

    def test_extract_mixed_usernames(self):
        text = "alice++ bob++ alice++"
        expected = {'alice': 2, 'bob': 1}
        result = extract_data(text)
        self.assertEqual(expected, result)

    def test_no_usernames(self):
        text = "Hello World!"
        expected = {}
        result = extract_data(text)
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()