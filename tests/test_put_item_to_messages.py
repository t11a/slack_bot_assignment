import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch
from lambda_function.handler import put_item_to_messages

class TestPutItemToMessages(unittest.TestCase):

    @patch('lambda_function.handler.dynamodb')
    def test_put_item_to_messages_success(self, mock_dynamodb):
        # Setup
        mock_dynamodb.put_item.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }

        from_username = "johndoe"
        user_map = {'alice': 2, 'bob': 1}
        msg = "alice++ alice++ bob++ Thank you!"

        # Call the function
        response = put_item_to_messages(from_username, user_map, msg)

        # Assert
        self.assertTrue(response['ok'])
        self.assertEqual(mock_dynamodb.put_item.call_count, 2)

    @patch('lambda_function.handler.dynamodb')
    def test_put_item_to_messages_failure(self, mock_dynamodb):
        # Setup
        mock_dynamodb.put_item.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 400}
        }

        from_username = "johndoe"
        user_map = {'alice': 2}
        msg = "alice++ alice++ Thank you!"

        # Call the function
        response = put_item_to_messages(from_username, user_map, msg)

        # Assert
        self.assertFalse(response['ok'])

if __name__ == '__main__':
    unittest.main()
