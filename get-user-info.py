import sys
import logging
import boto3
import json
import botocore
import base64
from botocore.exceptions import ClientError

'''
CODE BY FIZZYPINE, NOT LEAKED LOL
'''

bucket_name = "BUCKET NAME"

'''
Options are defined by the HTTP headers passed through the request, structure as follows

{
headers: {
    FileName: {main, meta}, #extensable to anything you want if you choose to split data or add new files to each user
    UID: {roblox_id}
    }


}

returns json content of the requested file
'''

def lambda_handler(event, context):
    try:
        s3 = boto3.resource('s3')
        try:
            s3_path = 'user_data/{}/{}.json'.format(event['headers']['UID'], event['headers']['FileName']) #used if custom name is used, if no custom name is defined will default to main
        except:
            s3_path = 'user_data/{}/main.json'.format(event['headers']['UID'])
        content_object = s3.Object(bucket_name, s3_path)
        file_content = content_object.get()['Body'].read().decode('utf-8')

        json_content = json.loads(file_content)
        print(json_content)
        return {
            'statusCode': 200,
            'body': json_content
        }

    except ClientError as ex:
        if ex.response['Error']['Code'] == 'NoSuchKey':
            return {
                'statusCode': 204
            }

        elif ex.response['Error']['Code'] == 'NameError':
            print(ex)

        else:
            return {
                'statusCode': 500,
                'body': 'unhandled error occured while running user JSON update, please contact fizzypine#0001 to review the error {}'.format(
                    ex)
            }

    except NameError as e:
        print(e)

    except:
        e = sys.exc_info()[0]
        print(e)
        return {
            'statusCode': 500,
            'body': 'unhandled error occured while running user JSON update, please contact fizzypine#0001 to review the error {}'.format(
                e)
        }