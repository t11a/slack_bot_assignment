import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch
from lambda_function.handler import increment_count

class TestIncrementCount(unittest.TestCase):

    @patch('lambda_function.handler.dynamodb')
    def test_increment_count_success(self, mock_dynamodb):
        # Setup
        mock_dynamodb.update_item.side_effect = [
            {
                'ResponseMetadata': {'HTTPStatusCode': 200},
                'Attributes': {'total_num': {'N': '5'}}
            },
            {
                'ResponseMetadata': {'HTTPStatusCode': 200},
                'Attributes': {'total_num': {'N': '3'}}
            }
        ]

        user_map = {'alice': 2, 'bob': 1}

        # Call the function
        response = increment_count(user_map)

        # Assert
        self.assertTrue(response['ok'])
        self.assertEqual(response['new_user_count_map'], {'alice': 5, 'bob': 3})
        self.assertEqual(mock_dynamodb.update_item.call_count, 2)

    @patch('lambda_function.handler.dynamodb')
    def test_increment_count_failure(self, mock_dynamodb):
        # Setup
        mock_dynamodb.update_item.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 400},
        }

        user_map = {'alice': 2}

        # KeyError を期待してテストを実行
        with self.assertRaises(KeyError):
            increment_count(user_map)

if __name__ == '__main__':
    unittest.main()
