import json
import random
import string


def formatJSONRespone(data):
    statusCode = data['statusCode']
    body = data['body'] or None
    
    return {
        'statusCode': statusCode,
        'body': json.dumps(body)
    }
    
    
def generateAlphanumericID(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))