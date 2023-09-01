import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from lambda_function.handler import post_message
from secret_config import SLACK_TOKEN, channel_id
import random

# This test actually executes the Slack API, so it's closer to an Integration test.
class TestPostMessage(unittest.TestCase):
    
    def test_valid_post_message(self):
        random_number = random.randint(0, 100)
        text = "username: {}".format(random_number)
        res = post_message(SLACK_TOKEN, channel_id, text)
        self.assertTrue(res['ok'])
    
    def test_invalid_token(self):
        text = "username: 88"
        res = post_message("INVALID_TOKEN", channel_id, text)
        self.assertFalse(res['ok'])
        self.assertEqual(res['error'], "invalid_auth")

    def test_invalid_channel_id(self):
        text = "username: 88"
        res = post_message(SLACK_TOKEN, "foo", text)
        self.assertFalse(res['ok'])
        self.assertEqual(res['error'], "channel_not_found")

if __name__ == '__main__':
    unittest.main()