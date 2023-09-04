import base64
import json

print('Loading function')

def lambda_handler(event, context):
    output = []
    
    print(f"event: {event}")

    for record in event['records']:
        print(f"recordId: {record['recordId']}")
        payload = base64.b64decode(record['data']).decode('utf-8')
        json_value = json.loads(payload)

        # Do custom processing on the payload here
        print(f"json_value:{json_value}")
        data = {}
        data['eventID']                     = json_value['eventID']
        data['eventName']                   = json_value['eventName']
        data['ApproximateCreationDateTime'] = json_value['dynamodb']['ApproximateCreationDateTime']
        data['to_username']                 = json_value["dynamodb"]["NewImage"]["to_username"]["S"]
        data['from_username']               = json_value["dynamodb"]["NewImage"]["from_username"]["S"]
        data['message']                     = json_value["dynamodb"]["NewImage"]["message"]["S"]
        data['username']                    = json_value["dynamodb"]["NewImage"]["username"]["S"]
        data['incr_num']                    = json_value["dynamodb"]["NewImage"]["incr_num"]["N"]
        data['time_to_username']            = json_value["dynamodb"]["NewImage"]["time_to_username"]["S"]

        # Add line break as suffix to each record
        record_json_with_newline = json.dumps(data) + '\n'

        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(record_json_with_newline.encode('utf-8')).decode('utf-8')
        }
        output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': output}