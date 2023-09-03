import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
from lambda_function.handler import get_slack_username
from slack_sdk.errors import SlackApiError

class TestGetSlackUsername(unittest.TestCase):

    @patch('lambda_function.handler.WebClient')  # Mock the WebClient
    def test_get_slack_username_success(self, MockWebClient):

        # Mocked response
        mock_response = {
            "ok": True,
            "user": {
                "profile": {
                    "display_name": "test_display_name",
                    "real_name": "test_real_name"
                }
            }
        }

        # Setting the mock client's users_info method to return our mocked response
        mock_client = MagicMock()
        mock_client.users_info.return_value = mock_response
        MockWebClient.return_value = mock_client

        result = get_slack_username("some_user_id")

        self.assertEqual(result, "test_display_name")

    @patch('lambda_function.handler.WebClient')
    def test_get_slack_username_failure(self, MockWebClient):

        mock_response = {
            "ok": False,
            "error": "some_error"
        }

        mock_client = MagicMock()
        mock_client.users_info.return_value = mock_response
        MockWebClient.return_value = mock_client

        result = get_slack_username("some_user_id")

        self.assertEqual(result, "")

    @patch('lambda_function.handler.WebClient')
    def test_get_slack_username_exception(self, MockWebClient):

        mock_error_response = {"ok": False, "error": "some_error"}
        mock_client = MagicMock()
        mock_client.users_info.side_effect = SlackApiError(
            message="Error message",
            response=mock_error_response
        )
        MockWebClient.return_value = mock_client

        result = get_slack_username("some_user_id")

        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()