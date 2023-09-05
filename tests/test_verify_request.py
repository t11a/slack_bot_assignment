import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from lambda_function.handler import verify_request
from secret_config import valid_event, invalid_event

class TestVerifyRequest(unittest.TestCase):
    def test_valid_request(self):
        self.assertTrue(verify_request(valid_event, os.environ['SLACK_SIGNING_SECRET']))

    def test_invalid_request(self):
        self.assertFalse(verify_request(invalid_event, os.environ['SLACK_SIGNING_SECRET']))
        #with self.assertRaises(ValueError):
        #    verify_request(invalid_event)

if __name__ == '__main__':
    unittest.main()