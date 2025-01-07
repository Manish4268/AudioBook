import json
import urllib.parse
import boto3
import hashlib
import redis
import os
import base64

# Initialize boto3 clients for S3 and Textract
s3 = boto3.client('s3')
textract = boto3.client('textract')

# Redis connection parameters
REDIS_HOST = os.environ.get("REDIS_ENDPOINT")
REDIS_PORT = 6379

def calculate_md5(binary_data):
    """
    Calculate the MD5 hash of a given value (string).
    """
    hash_func = hashlib.md5()
    hash_func.update(binary_data)  # binary_data is already in bytes, no need to encode
    file_hash = hash_func.hexdigest()
    print(f"MD5 hash calculated: {file_hash}")
    return file_hash

def lambda_handler(event, context):
    try:
        print("Event received:", json.dumps(event))

        # Check if the event contains the 'Records' key
        if 'Records' not in event or len(event['Records']) == 0:
            print("No Records found in the event")
            return {
                'statusCode': 400,
                'body': json.dumps('Event does not contain S3 record')
            }
        
        # Get the S3 bucket and object key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
        print(f"S3 bucket: {bucket}, S3 object key: {key}")
        
        # Call Amazon Textract to analyze the document
        print("Calling Amazon Textract to analyze the document...")
        response = textract.analyze_document(
            Document={'S3Object': {'Bucket': bucket, 'Name': key}},
            FeatureTypes=['TABLES', 'FORMS']  # Request extraction of tables and forms
        )
        print("Textract response received:", json.dumps(response))
        
        # Extract text from the Textract response
        extracted_text = ''
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                extracted_text += block['Text'] + '\n'
        print(f"Extracted text: {extracted_text}")
        
        # Calculate the MD5 hash of the filename
        s3 = boto3.client('s3')
    
        response = s3.get_object(Bucket=bucket, Key=key)
        binary_data = response['Body'].read()  # Binary data
    
        # Calculate the MD5 hash of the binary data
        file_hash = calculate_md5(binary_data)
        
        print(f"File hash: {file_hash}")
        
        # Connect to Redis
        print("Connecting to Redis...")
        redis_client = redis.StrictRedis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            ssl=True,
            decode_responses=True
        )
        print("Connected to Redis successfully.")
        
        # Store extracted text in Redis with the hash as the key
        redis_client.set(file_hash, extracted_text)
        print(f"Extracted text stored in Redis with key: {file_hash}")
        
        retrieved_value = redis_client.get(file_hash)
        print(f"Retrieved value from Redis for key '{file_hash}': {retrieved_value}")

        # Write extracted text to a file in Lambda's /tmp directory
        print("Writing extracted text to a temporary file...")
        file_path = '/tmp/extracted_text.txt'
        
        with open(file_path, 'w') as f:
            f.write(extracted_text)
        print("Extracted text written to temporary file.")
        
        # Upload the file to S3
        output_key = f'{file_hash}.txt'
        print(f"Uploading file to S3 with key: {output_key}")
        with open(file_path, 'rb') as f:
            s3.upload_fileobj(f, bucket, output_key)
        print(f"File uploaded to S3: {output_key}")
        
        # Clean up the temporary file
        os.remove(file_path)
        print("Temporary file removed.")

        return {
            'statusCode': 200,
            'body': json.dumps('File processed and data stored in Redis successfully!')
        }
    
    except Exception as e:
        # Log the error and return a failure response
        print(f"Error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }
