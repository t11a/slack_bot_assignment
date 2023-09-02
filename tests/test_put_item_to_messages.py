import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch
from botocore.exceptions import ClientError
from lambda_function.handler import put_item_to_messages

class TestPutItemToMessages(unittest.TestCase):

    @patch("lambda_function.handler.dynamodb.put_item")
    @patch("lambda_function.handler.time.time", return_value=1693658446)
    def test_put_item_to_messages(self, mock_time, mock_put_item):
        # Setup
        from_username = "alice"
        to_username = "bob"
        msg = "bob++ Thanks!"
        count = 1

        # Mock response
        mock_response = {
            "ResponseMetadata": {
                "HTTPStatusCode": 200
            }
        }
        mock_put_item.return_value = mock_response

        # Call the function
        response = put_item_to_messages(from_username, to_username, msg, count)

        # Assert that the function makes the correct DynamoDB call
        mock_put_item.assert_called_once_with(
            TableName='Messages',
            Item={
                'username': {'S': from_username},
                'timestamp': {'N': str(1693658446)},
                'to_username': {'S': to_username},
                'message': {'S': msg},
                'incr_num': {'N': str(count)}
            }
        )

        # Assert that the function returns the correct response
        self.assertEqual(response, mock_response)

    @patch("lambda_function.handler.dynamodb")
    def test_put_item_error(self, mock_dynamodb):
        # Setup
        from_username = "alice"
        to_username = "bob"
        msg = "bob++ Thanks!"
        count = 1

        # Mock the DynamoDB error
        mock_dynamodb.put_item.side_effect = ClientError(
            error_response={'Error': {'Code': 'InternalServerError', 'Message': 'Internal Server Error'}},
            operation_name='PutItem',
        )

        # Test that an error is raised
        with self.assertRaises(ClientError):
            put_item_to_messages(from_username, to_username, msg, count)



if __name__ == '__main__':
    unittest.main()
