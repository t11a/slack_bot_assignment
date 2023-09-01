import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from lambda_function.handler import extract_data

class TestExtractData(unittest.TestCase):
    def test_single_username_jp(self):
        text = "username++ ありがとう。"
        count, message = extract_data(text)
        self.assertEqual(count, 1)
        self.assertEqual(message, "ありがとう。")

    def test_single_username_en(self):
        text = "username++ Thank you:)"
        count, message = extract_data(text)
        self.assertEqual(count, 1)
        self.assertEqual(message, "Thank you:)")
    """
    def test_username_include_period(self):
        text = "user.name++ Thank you:)"
        count, message = extract_data(text)
        self.assertEqual(count, 1)
        self.assertEqual(message, "Thank you:)")
    """
    def test_multiple_usernames(self):
        text = "username++ username++ username++ ありがとう。"
        count, message = extract_data(text)
        self.assertEqual(count, 3)
        self.assertEqual(message, "ありがとう。")

    def test_no_message(self):
        text = "username++ username++ username++"
        count, message = extract_data(text)
        self.assertEqual(count, 3)
        self.assertIsNone(message)

    def test_double_spaces_before_message(self):
        text = "username++ username++ username++  ありがとう。"
        count, message = extract_data(text)
        self.assertEqual(count, 3)
        self.assertEqual(message, "ありがとう。")

    def test_multibyte_space_before_message(self):
        text = "username++　ありがとう。"
        count, message = extract_data(text)
        self.assertEqual(count, 1)
        self.assertEqual(message, "ありがとう。")

if __name__ == '__main__':
    unittest.main()