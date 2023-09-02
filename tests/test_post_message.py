import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from lambda_function.handler import post_message
from secret_config import channel_id
import random
import pytest

# This test actually executes the Slack API, so it's closer to an Integration test.
class TestPostMessage(unittest.TestCase):
    
    @pytest.mark.skip(reason="The test is marked because it actually posts to a Slack channel.")
    def test_valid_post_message(self):
        random_number = random.randint(0, 100)
        text = "username: {}".format(random_number)
        res = post_message(channel_id, text)
        self.assertTrue(res['ok'])

    def test_invalid_channel_id(self):
        text = "username: 88"
        res = post_message("foo", text)
        self.assertFalse(res['ok'])
        self.assertEqual(res['error'], "channel_not_found")

if __name__ == '__main__':
    unittest.main()