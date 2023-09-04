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
    """
    Args:
        event (str): message posted on slack
        context (object): https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    Returns:
        dict: status code
    """
    
    if not verify_request(event, SLACK_SIGNING_SECRET):
        logger.error("Verify Request Error")
        return

    logger.info(event['body'])
    
    body = json.loads(event['body'])
    text = body['event']['text']

    if is_reaction_message(text):
        # get slack user id from request body
        from_username = body['event']['user']

        user_map = extract_data(text)

        new_user_count_map = save_data_to_dynamodb(from_username, user_map, text)

        # get channel id from request body
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
        logger.info("reaction message is not detected")
        return {
            'statusCode': 200,
        }


def verify_request(event, slack_signing_secret):
    """
    Args:
        event (dict): http request header and body from Slack
        slack_signing_secret (str): signing secret for you app
    Returns:
        bool: True if verification succeeds, False if verification fails.

    https://api.slack.com/authentication/verifying-requests-from-slack
    """
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


def put_item_to_messages(from_username, user_map, msg):
    """
    Args:
        from_username (str): http request header and body from Slack
        user_map (dict): A mapping of usernames to their respective counts. 
                         Format: {username (str): count (int)}
        msg (str): message posted on Slack
    Returns:
        bool: True if all operations succeed. 

    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/put_item.html
    """
    timestamp = int(time.time())

    # get display name from 'from_username'
    display_name = get_slack_username(from_username)

    result = []
    for to_username, count in user_map.items():
        time_to_username = str(timestamp) + '#' + to_username
        
        response = dynamodb.put_item(
            TableName='Messages',
            Item={
                'username': {'S': from_username},
                'time_to_username': {'S': time_to_username},
                'to_username': {'S': to_username},
                'from_username': {'S': display_name},
                'message': {'S': msg},
                'incr_num': {'N': str(count)}
            }
        )
        result.append(response['ResponseMetadata']['HTTPStatusCode'])

    return {'ok' : result.count(200) == len(user_map)}

def increment_count(user_map):
    """
    Args:
        user_map (dict): A mapping of usernames to their respective counts. 
                         Format: {username (str): count (int)}
    Returns:
        dict: 
            ok (bool): True if all responses have a 200 status code, False otherwise.
            new_user_count_map (dict): A mapping of updated usernames to their respective counts. 
                                       Format: {username (str): count (int)}

    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/update_item.html
    """
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
    """
    Args:
        from_username (str): Slack user id
        user_map (dict): A mapping of usernames to their respective counts. 
                         Format: {username (str): count (int)}
        msg (str): message posted on Slack
    Returns:
        (dict): A mapping of updated usernames to their respective counts. 
                                    Format: {username (str): count (int)}
    """

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
    """
    Args:
        channel_id (str): Slack channel ID
        text (str): message that will be posted to Slack
        username (str): username of Slack bot
    Returns:
        (object): Slack API response
    
    https://api.slack.com/methods/chat.postMessage
    """
    # Create a Slack client with your token
    client = WebClient(token=SLACK_TOKEN)

    try:
        # Call the chat.postMessage method using the WebClient
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

def get_slack_username(user_id):
    """
    Args:
        user_id (str): slack user id
    Returns:
        str: display name of slack user

    https://api.slack.com/methods/users.info
    """
    client = WebClient(token=SLACK_TOKEN)

    try:
        response = client.users_info(user=user_id)

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
    """
    Args:
        text (str): message posted on slack

    Returns:
        bool: {username}++ format or not
    """
    pattern = r'(\w+\+\+ *)+\s*.*'
    return bool(re.match(pattern, text))

def extract_data(text):
    """
    Args:
        text (str): message posted on slack
    Returns:
        dict: mapping of usernames to their respective frequencies of occurrence
    """
    # search the pattern like 'username++'
    pattern = r'(\w+)\+\+'
    usernames = re.findall(pattern, text)

    # count the occurrence frequency of each username
    user_map = {}
    for user in usernames:
        user_map[user] = 1 + user_map.get(user, 0)

    return user_map