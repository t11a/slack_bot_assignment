import json
import logging
import re
import boto3
import time
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import hmac
import hashlib

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.client('dynamodb')

SLACK_TOKEN = os.environ['SLACK_TOKEN']
SLACK_SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']

def lambda_handler(event, context):
    
    if not verify_request(event, SLACK_SIGNING_SECRET):
        logger.error("Verify Request Error")
        return

    logger.info(event['body'])
    
    body = json.loads(event['body'])
    text = body['event']['text']

    if is_reaction_message(text):
        from_username = body['event']['user']
        # ex)
        # text : alice++ alice++ bob++ Thanks!
        # response: {'alice': 2, 'bob': 1}
        user_map = extract_data(text)

        # ex)  response: {'alice': 16, 'bob': 31}
        new_user_count_map = save_data_to_dynamodb(from_username, user_map, text)

        channel_id = body['event']['channel']
        text = ""
        for username, count in new_user_count_map.items():
            text += f"{username}: {count}\n"

        res = post_message(channel_id, text)
        return {
            'statusCode': 200,
            'ok' : res.get('ok')
        }
    else:
        return {
            'statusCode': 200,
        }


def verify_request(event, slack_signing_secret):
    # https://api.slack.com/authentication/verifying-requests-from-slack

    request_body = event['body']
    headers = event['headers']
    timestamp = headers['x-slack-request-timestamp']
    sig_basestring = 'v0:' + timestamp + ':' + request_body

    slack_signing_secret_bytes = slack_signing_secret.encode('utf-8') 
    sig_basestring_bytes = sig_basestring.encode('utf-8')

    my_signature = 'v0=' + hmac.new(
        slack_signing_secret_bytes,
        sig_basestring_bytes,
        hashlib.sha256).hexdigest()
    
    slack_signature = headers['x-slack-signature']
    if hmac.compare_digest(my_signature, slack_signature):
        return True
    else:
        return False

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/put_item.html
def put_item_to_messages(from_username, user_map, msg):
    timestamp = int(time.time())

    result = []
    for to_username, count in user_map.items():
        time_to_username = str(timestamp) + '#' + to_username
        
        response = dynamodb.put_item(
            TableName='Messages',
            Item={
                'username': {'S': from_username},
                'time_to_username': {'S': time_to_username},
                'to_username': {'S': to_username},
                'message': {'S': msg},
                'incr_num': {'N': str(count)}
            }
        )
        result.append(response['ResponseMetadata']['HTTPStatusCode'])

    return {'ok' : result.count(200) == len(user_map)}

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/update_item.html
def increment_count(user_map):
    result = []
    new_user_count_map = {}
    for username, count in user_map.items():
        
        response = dynamodb.update_item(
            TableName='UserCounts',
            Key={
                'username': {'S': username}
            },
            UpdateExpression="ADD total_num :incr",
            ExpressionAttributeValues={
                ':incr': {'N': str(count)}
            },
            ReturnValues="UPDATED_NEW"
        )
        new_user_count_map[username] = int(response['Attributes']['total_num']['N'])
        result.append(response['ResponseMetadata']['HTTPStatusCode'])

    return {
        'ok' : result.count(200) == len(user_map),
        'new_user_count_map' : new_user_count_map
    }

def save_data_to_dynamodb(from_username, user_map, msg):
    # DDB Table
    # Messages
    #   username (PK) : String
    #   time_to_username (SK) : String
    #   to_username : String
    #   message : String
    #   incr_num : Number
    # UserCounts
    #   username (PK): String
    #   total_num : Number

    response = put_item_to_messages(from_username, user_map, msg)
    logger.info(response)
    if not response['ok']:
        return {'ok': False}

    response = increment_count(user_map)
    logger.info(response)
    if not response['ok']:
        return {'ok': False}

    new_user_count_map = response['new_user_count_map']

    return new_user_count_map

def post_message(channel_id, text, username="++Bot"):
    # Create a Slack client with your token
    client = WebClient(token=SLACK_TOKEN)

    try:
        # Call the chat.postMessage method using the WebClient
        # https://api.slack.com/methods/chat.postMessage
        response = client.chat_postMessage(
            channel = channel_id,
            text = text,
            username = username
        )
        logger.info(response)
        return response
    except SlackApiError as e:
        logger.error(f"Error posting message: {e}")
        return e.response

def get_slack_username(user):
    """
    https://api.slack.com/methods/users.info
    Args:
        user (str): slack user id

    Returns:
        str: display name of slack user
    """
    client = WebClient(token=SLACK_TOKEN)

    try:
        response = client.users_info(user)

        if response["ok"]:
            # display_name
            display_name = response['user']['profile']['display_name']
            # real_name
            real_name = response['user']['profile']['real_name']
            logger.info(f"display name:{display_name}, real name:{real_name}")
            return display_name
        else:
            logger.error(f"users_info response: {response}")
            return ""
    except SlackApiError as e:
        logger.error(f"Error fetching user info: {e.response['error']}")
        return ""

def is_reaction_message(text):
    pattern = r'(\w+\+\+ *)+\s*.*'
    return bool(re.match(pattern, text))

def extract_data(text):
    # 'username++' のパターンを検索
    pattern = r'(\w+)\+\+'
    usernames = re.findall(pattern, text)

    # 各usernameの出現回数をカウント
    user_map = {}
    for user in usernames:
        user_map[user] = 1 + user_map.get(user, 0)

    return user_map