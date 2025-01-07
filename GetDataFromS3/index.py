import json
import boto3

s3 = boto3.client('s3')

def lambda_handler(event, context):
    file_name = event['queryStringParameters']['file']
    bucket_name = 'termassignmentbucketcf'
    print(file_name)
    
    try:
        # Read the content of the file from S3
        response = s3.get_object(Bucket=bucket_name, Key=file_name)
        file_content = response['Body'].read().decode('utf-8')
        
        return {
            'statusCode': 200,
            'headers': {
		'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': file_content
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
		'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps(f'Error: {str(e)}')
        }

