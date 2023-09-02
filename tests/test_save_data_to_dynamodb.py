import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch
from botocore.exceptions import ClientError
from lambda_function.handler import save_data_to_dynamodb

class TestSaveDataToDynamodb(unittest.TestCase):

    @patch('lambda_function.handler.put_item_to_messages')
    @patch('lambda_function.handler.increment_count')
    @patch('lambda_function.handler.logger')
    def test_save_data_to_dynamodb(self, mock_logger, mock_increment_count, mock_put_item_to_messages):
        # モックの設定
        mock_put_item_to_messages.return_value = {'ok': True}
        mock_increment_count.return_value = {
            'ok': True,
            'new_user_count_map': {'alice': 5, 'bob': 3}
        }

        # 関数の呼び出し
        from_username = 'johndoe'
        user_map = {'alice': 2, 'bob': 1}
        msg = 'alice++ alice++ bob++ Thank you!'
        result = save_data_to_dynamodb(from_username, user_map, msg)

        # 戻り値の確認
        self.assertEqual(result, {'alice': 5, 'bob': 3})

        # 関数の呼び出しが期待通りであることを確認
        mock_put_item_to_messages.assert_called_once_with(from_username, user_map, msg)
        mock_increment_count.assert_called_once_with(user_map)


    @patch('lambda_function.handler.put_item_to_messages')
    @patch('lambda_function.handler.increment_count')
    @patch('lambda_function.handler.logger')
    def test_save_data_to_dynamodb_failure_on_put_item(self, mock_logger, mock_increment_count, mock_put_item_to_messages):
        # モックの設定
        mock_put_item_to_messages.return_value = {'ok': False}
        
        # 関数の呼び出し
        from_username = 'johndoe'
        user_map = {'alice': 2, 'bob': 1}
        msg = 'alice++ alice++ bob++ Thank you!'
        result = save_data_to_dynamodb(from_username, user_map, msg)
        
        # 戻り値の確認
        self.assertEqual(result, {'ok': False})

    @patch('lambda_function.handler.put_item_to_messages')
    @patch('lambda_function.handler.increment_count')
    @patch('lambda_function.handler.logger')
    def test_save_data_to_dynamodb_failure_on_increment_count(self, mock_logger, mock_increment_count, mock_put_item_to_messages):
        # モックの設定
        mock_put_item_to_messages.return_value = {'ok': True}
        mock_increment_count.return_value = {'ok': False}

        # 関数の呼び出し
        from_username = 'johndoe'
        user_map = {'alice': 2, 'bob': 1}
        msg = 'alice++ alice++ bob++ Thank you!'
        result = save_data_to_dynamodb(from_username, user_map, msg)
        
        # 戻り値の確認
        self.assertEqual(result, {'ok': False})

if __name__ == '__main__':
    unittest.main()
