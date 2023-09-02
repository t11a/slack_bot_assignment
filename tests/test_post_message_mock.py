import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
from lambda_function.handler import post_message
from slack_sdk.errors import SlackApiError

class TestPostMessageMock(unittest.TestCase):
    
    @patch('lambda_function.handler.WebClient')
    def test_post_message_success(self, MockWebClient):
        # Mocking successful response from chat_postMessage method
        mock_response = {"ok": True}
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = mock_response
        MockWebClient.return_value = mock_client

        response = post_message('test_token', 'test_channel', 'test_text')
        
        self.assertEqual(response, mock_response)
        mock_client.chat_postMessage.assert_called_once()

    @patch('lambda_function.handler.WebClient')
    def test_post_message_error(self, MockWebClient):
        # Mocking error from chat_postMessage method
        mock_error_response = {"ok": False, "error": "some_error"}
        mock_client = MagicMock()
        mock_client.chat_postMessage.side_effect = SlackApiError(
            message="Error message",
            response=mock_error_response
        )
        MockWebClient.return_value = mock_client

        response = post_message('test_token', 'test_channel', 'test_text')

        self.assertEqual(response, mock_error_response)
        mock_client.chat_postMessage.assert_called_once()

if __name__ == '__main__':
    unittest.main()