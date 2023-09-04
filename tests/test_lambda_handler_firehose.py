import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import base64
import json
from lambda_function_firehose.handler import lambda_handler

class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        # Set up a sample event with a single record
        self.single_record_data = {
            "eventID": "some_id",
            "eventName": "some_name",
            "dynamodb": {
                "ApproximateCreationDateTime": "some_date",
                "NewImage": {
                    "to_username": {"S": "to_user"},
                    "from_username": {"S": "from_user"},
                    "message": {"S": "hello"},
                    "username": {"S": "user123"},
                    "incr_num": {"N": "1"},
                    "time_to_username": {"S": "time_to_user"}
                }
            }
        }

        self.single_encoded_data = base64.b64encode(json.dumps(self.single_record_data).encode('utf-8')).decode('utf-8')
        
        self.single_event = {
            'records': [
                {
                    'recordId': 'rec1',
                    'data': self.single_encoded_data
                }
            ]
        }

        # Set up a sample event with two records
        self.double_event = {
            'records': [
                {
                    'recordId': 'rec1',
                    'data': self.single_encoded_data
                },
                {
                    'recordId': 'rec2',
                    'data': self.single_encoded_data
                }
            ]
        }

        self.context = {}  # Empty context object for this test

    def test_lambda_handler_single_record(self):
        response = lambda_handler(self.single_event, self.context)
        self.assertEqual(len(response['records']), 1)
        self._validate_record(response['records'][0], 'rec1')

    def test_lambda_handler_double_records(self):
        response = lambda_handler(self.double_event, self.context)
        self.assertEqual(len(response['records']), 2)
        self._validate_record(response['records'][0], 'rec1')
        self._validate_record(response['records'][1], 'rec2')

    def _validate_record(self, record, record_id):
        self.assertEqual(record['recordId'], record_id)
        self.assertEqual(record['result'], 'Ok')
        
        decoded_data = base64.b64decode(record['data']).decode('utf-8')
        record_json = json.loads(decoded_data)
        
        self.assertEqual(record_json['eventID'], 'some_id')
        self.assertEqual(record_json['eventName'], 'some_name')
        self.assertEqual(record_json['ApproximateCreationDateTime'], 'some_date')
        self.assertEqual(record_json['to_username'], 'to_user')
        self.assertEqual(record_json['from_username'], 'from_user')
        self.assertEqual(record_json['message'], 'hello')
        self.assertEqual(record_json['username'], 'user123')
        self.assertEqual(record_json['incr_num'], '1')
        self.assertEqual(record_json['time_to_username'], 'time_to_user')

if __name__ == "__main__":
    unittest.main()
