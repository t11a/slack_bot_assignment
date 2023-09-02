import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch
from botocore.exceptions import ClientError
from lambda_function.handler import increment_count

class TestIncrementCount(unittest.TestCase):

    @patch("lambda_function.handler.dynamodb.update_item")
    def test_increment_count(self, mock_update_item):
        # Setup
        username = "bob"
        increment_value = 3

        # Mock response for update_item
        mock_update_item_response = {
            "Attributes": {
                "total_num": {
                    "N": "7"
                }
            }
        }
        mock_update_item.return_value = mock_update_item_response

        # Call the function
        response = increment_count(username, increment_value)

        # Construct the expected call arguments
        expected_args = {
            'TableName': 'UserCounts',
            'Key': {
                'username': {'S': username}
            },
            'UpdateExpression': "ADD total_num :incr",
            'ExpressionAttributeValues': {
                ':incr': {'N': str(increment_value)}
            },
            'ReturnValues': "UPDATED_NEW"
        }

        # Assert that update_item was called correctly
        mock_update_item.assert_called_once_with(**expected_args)

        # Assert the response matches the mock response
        self.assertEqual(response, mock_update_item_response)

    @patch("lambda_function.handler.dynamodb.update_item")
    def test_increment_count_dynamodb_error(self, mock_update_item):
        # Setup
        username = "Bob"
        increment_value = 3

        # Mock a DynamoDB error
        mock_update_item.side_effect = ClientError(
            error_response={'Error': {'Code': 'InternalServerError', 'Message': 'Internal Server Error'}},
            operation_name='UpdateItem',
        )

        # Test that an error is raised
        with self.assertRaises(ClientError):
            increment_count(username, increment_value)

if __name__ == '__main__':
    unittest.main()
