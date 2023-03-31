import os
import boto3

def lambda_handler(event, context):
    dynamo = boto3.resource('dynamodb', 'us-east-2')
    
    # https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html
    event_data = event['Records'][0]['Sns']
    message_id = event_data['MessageId']
    topic_arn = event_data['TopicArn']
    subject = event_data['Subject']
    msg = event_data['Message']
    timestamp = event_data['Timestamp']
    
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/put_item.html
    # Cheatsheet: https://dynobase.dev/dynamodb-python-with-boto3/#put-item
    table = dynamo.Table(os.environ['tableName'])
    response = table.put_item(
        Item={
            'id': message_id,
            'topic': topic_arn,
            'subject': subject,
            'message': msg,
            'timestamp': timestamp
        }
    )