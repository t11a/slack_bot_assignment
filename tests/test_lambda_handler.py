import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch
from lambda_function.handler import lambda_handler

class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        self.event = {
            'body': '{"event": {"text": "some_text", "user": "some_user", "channel": "some_channel"}}'
        }
        self.context = {}  # You can add more to context if needed

    @patch('lambda_function.handler.verify_request', return_value=False)
    def test_verify_request_failure(self, mock_verify):
        response = lambda_handler(self.event, self.context)
        self.assertIsNone(response)  # Since function returns None on verify failure

    @patch('lambda_function.handler.verify_request', return_value=True)
    @patch('lambda_function.handler.is_reaction_message', return_value=False)
    def test_no_reaction_message(self, mock_verify, mock_is_reaction):
        response = lambda_handler(self.event, self.context)
        self.assertEqual(response, {'statusCode': 200})

    @patch('lambda_function.handler.verify_request', return_value=True)
    @patch('lambda_function.handler.is_reaction_message', return_value=True)
    @patch('lambda_function.handler.extract_data')
    @patch('lambda_function.handler.save_data_to_dynamodb')
    @patch('lambda_function.handler.post_message', return_value={'ok': True})
    def test_reaction_message_success(self, mock_verify, mock_is_reaction, mock_extract, mock_save, mock_post):
        mock_extract.return_value = {"username1": 1}
        mock_save.return_value = {"username1": 2}

        response = lambda_handler(self.event, self.context)

        self.assertEqual(response, {'statusCode': 200, 'ok': True})


if __name__ == "__main__":
    unittest.main()