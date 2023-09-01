import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from lambda_function.handler import is_reaction_message

class TestIsReactionMessage(unittest.TestCase):
    def test_valid_reaction_messages(self):
        self.assertTrue(is_reaction_message("username++ ありがとう。"))
        self.assertTrue(is_reaction_message("username++ username++ username++ ありがとう。"))
        self.assertTrue(is_reaction_message("username++"))

    def test_invalid_reaction_messages(self):
        self.assertFalse(is_reaction_message("ただのメッセージ"))
        self.assertFalse(is_reaction_message("username+-"))
        self.assertFalse(is_reaction_message("++username"))

if __name__ == '__main__':
    unittest.main()