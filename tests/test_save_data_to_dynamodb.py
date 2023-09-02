import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch
from botocore.exceptions import ClientError
from lambda_function.handler import save_data_to_dynamodb

class TestSaveDataToDynamodb(unittest.TestCase):

    @patch("lambda_function.handler.put_item_to_messages")
    @patch("lambda_function.handler.increment_count")
    def test_save_data_to_dynamodb(self, mock_increment_count, mock_put_item_to_messages):
        # Setup
        from_username = "alice"
        to_username = "bob"
        msg = "bob++ Thanks!"
        count = 1

        # Mock response for put_item_to_messages
        mock_put_item_to_messages_response = {
            "ResponseMetadata": {
                "HTTPStatusCode": 200
            }
        }
        mock_put_item_to_messages.return_value = mock_put_item_to_messages_response

        # Mock response for increment_count
        mock_increment_count_response = {
            'Attributes': {'total_num': {'N': '6'}}
        }
        mock_increment_count.return_value = mock_increment_count_response

        # Call the function
        new_total_num = save_data_to_dynamodb(from_username, to_username, msg, count)

        # Assert that the function calls the helper functions correctly
        mock_put_item_to_messages.assert_called_once_with(from_username, to_username, msg, count)
        mock_increment_count.assert_called_once_with(to_username, count)

        # Assert that the function returns the correct new total count
        self.assertEqual(new_total_num, 6)

    @patch("lambda_function.handler.put_item_to_messages")
    @patch("lambda_function.handler.increment_count")
    def test_save_data_put_item_error(self, mock_increment_count, mock_put_item):
        # Setup
        from_username = "alice"
        to_username = "bob"
        msg = "bob++ Thanks!"
        count = 1

        # Mock a DynamoDB error for put_item_to_messages
        mock_put_item.side_effect = ClientError(
            error_response={'Error': {'Code': 'InternalServerError', 'Message': 'Internal Server Error'}},
            operation_name='PutItem',
        )

        # Test that an error is raised
        with self.assertRaises(ClientError):
            save_data_to_dynamodb(from_username, to_username, msg, count)

    @patch("lambda_function.handler.put_item_to_messages")
    @patch("lambda_function.handler.increment_count")
    def test_save_data_increment_count_error(self, mock_increment_count, mock_put_item):
        # Setup
        from_username = "alice"
        to_username = "bob"
        msg = "bob++ Thanks!"
        count = 1

        # Mock a successful response for put_item_to_messages
        mock_put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        # Mock a DynamoDB error for increment_count
        mock_increment_count.side_effect = ClientError(
            error_response={'Error': {'Code': 'InternalServerError', 'Message': 'Internal Server Error'}},
            operation_name='UpdateItem',
        )

        # Test that an error is raised
        with self.assertRaises(ClientError):
            save_data_to_dynamodb(from_username, to_username, msg, count)


if __name__ == '__main__':
    unittest.main()
