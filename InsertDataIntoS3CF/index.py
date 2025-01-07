import json
import boto3
import base64
import hashlib
import redis
import os

# Redis connection parameters
REDIS_HOST = os.environ.get("REDIS_ENDPOINT")
REDIS_PORT = 6379

s3 = boto3.client('s3')
bucket_name = 'termassignmentbucketcf'

def calculate_md5(value):
    """
    Calculate the MD5 hash of a given value (binary).
    """
    print(f"Calculating MD5 hash for value of length {len(value)} bytes.")
    hash_func = hashlib.md5()
    hash_func.update(value)  # 'value' should be bytes, not a string
    file_hash = hash_func.hexdigest()
    print(f"MD5 hash calculated: {file_hash}")
    return file_hash

def lambda_handler(event, context):

    try:
        # Handle actual requests (POST)
        # print("manish")
        # print(f"event {event} already exists. Skipping upload.")
        
        # request_body = json.loads(event['body'])
    
        # # Extract the filename and base64 data from the parsed body
        # file_name = request_body.get('filename', None)
        # base64data = request_body.get('base64data', None)

        file_name = event['queryStringParameters']['file']
        print(file_name)

        # Extract base64data from the request body
        request_body = json.loads(event['body'])
        base64data = request_body['base64data']

        # Decode the base64 data to get the binary content of the file
        file_content = base64.b64decode(base64data)
    
        # Calculate MD5 hash of the file content
        file_hash = calculate_md5(file_content)
        
        print(f"MD5 hash of the uploaded file: {file_hash}")

        # Connect to Redis
        redis_client = redis.StrictRedis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            ssl=True,
            decode_responses=True
        )

        # Check if the file hash already exists in Redis
        retrieved_value = redis_client.get(file_hash)

        if retrieved_value:
            # If the file already exists in Redis, log it
            print(f"File with MD5 hash {file_hash} already exists. Skipping upload.")
            print(retrieved_value)
        else:
            # If the file doesn't exist, upload it to S3 and store the hash in Redis
            s3.put_object(Bucket=bucket_name, Key=file_name, Body=file_content)
            print(f"File uploaded to S3 bucket '{bucket_name}' with key '{file_name}'.")

        # Return a successful response
        return {
            'statusCode': 200,
            'headers': {
		'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            # 'body': json.dumps(retrieved_value)  # Make sure this is in a string format
            'body': json.dumps({
            'retrieved_value': retrieved_value,
            'additional_value': file_hash  # Add the new value here
    })
        }

    except Exception as e:
        print("Error occurred: ", str(e))
        return {
            'statusCode': 500,
            'headers': {
		'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps(f'Failed to process file: {str(e)}')
        }
