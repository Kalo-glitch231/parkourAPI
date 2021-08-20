import json
import os
import boto3
import logging
import sys
import math
from botocore.exceptions import ClientError
import botocore

'''
This function clears user data from the database, as it can be a PITA in some cases, and definetly a pain to do manually
'''

'''
CODE BY FIZZYPINE, NOT LEAKED LOL
'''

'''
Options are defined by the HTTP headers passed through the request, structure as follows

{
headers: {
    Mode: {TimeTrial, aaa} #pass no mode to wipe all data of a user, aaa is a testing function, will not work, built to throw an error
    TimeTrial: {all global leaderboards and timetrial names as defined by time_trial_info.json} #used only when mode TimeTrial is passed
    UID: {roblox_id}
    }

}

returns json content of the requested file
'''

s3 = boto3.resource('s3')
bucket_name = 'BUCKET_NAME'

rdsData = boto3.client('rds-data')

cluster_arn = ""
secret_arn = ""

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def clear_time_trial(user_id, time_trial):
    logger.info("CLEAR TIME TRIAL {} USER {}")
    try:
        time_trial_query = "SELECT * FROM {} WHERE USER_ID = {}".format(time_trial, user_id)

        tr = rdsData.begin_transaction(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database='DATABASE')
        # logger.info("TRANSAC: INIT {}".format(time_trial))
        response1 = rdsData.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database='DATABASE',
            sql=time_trial_query,
            transactionId=tr['transactionId'])
        logger.info("TRANSAC: response 1")

        cr = rdsData.commit_transaction(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            transactionId=tr['transactionId'])
        logger.info("TRANSAC: commit {}".format(time_trial, user_id))

        # logger.info("TRANSAC: TRANSAC succeeded")

    except NameError as err:
        logger.error("Error: {}".format(err))
        return {
            'statusCode': 500,
            'body': 'NameError has occured, please contact fizzypine#0001 to review the error {}'.format(err)
        }
    except TypeError as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'body': 'unhandled Type Error error while running SQL query, please contact fizzypine#0001 to review the error {}'.format(
                e)
        }

    except ClientError as e:
        if e.response['Error']['Code'] == 'BadRequestException':
            return {
                'statusCode': 500,
                'body': 'unhandled Name Error while running SQL query, please contact fizzypine#0001 to review the error {}'.format(
                    e)
            }
    except botocore.exceptions.ParamValidationError as e:
        return {
            'statusCode': 500,
            'body': "Parameter validation error: %s" % e
        }
    except:
        e = sys.exc_info()[0]
        logger.error(e)
        return {
            'statusCode': 500,
            'body': 'unhandled error occured while running SQL query, please contact fizzypine#0001 to review the error {}'.format(
                e)
        }


def clear_glb(user_id):
    q1 = "delete from users_inf where user_id = {};".format(user_id)
    q2 = "delete from gearless_ranked where user_id = {};".format(user_id)
    q3 = "delete from global_leaderboard where user_id = {};".format(user_id)
    q4 = "delete from player_info where user_id = {};".format(user_id)
    q5 = "delete from settings where user_id = {};".format(user_id)

    tr = rdsData.begin_transaction(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database='DATABASE')
    logger.info("TRANSAC: INIT")

    response1 = rdsData.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database='DATABASE',
        sql=q1,
        transactionId=tr['transactionId'])
    logger.info("TRANSAC: response 1")

    response2 = rdsData.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database='DATABASE',
        sql=q2,
        transactionId=tr['transactionId'])
    logger.info("TRANSAC: response 2")

    response3 = rdsData.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database='DATABASE',
        sql=q3,
        transactionId=tr['transactionId'])
    logger.info("TRANSAC: response 3")

    response4 = rdsData.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database='DATABASE',
        sql=q4,
        transactionId=tr['transactionId'])
    logger.info("TRANSAC: response 4")

    response5 = rdsData.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database='DATABASE',
        sql=q5,
        transactionId=tr['transactionId'])
    logger.info("TRANSAC: response 5")

    cr = rdsData.commit_transaction(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        transactionId=tr['transactionId'])
    logger.info("TRANSAC: commit")

    return {
        'statusCode': 200,
        'body': "user {} removed from leaderboards".format(user_id)
    }


def clear_data(user_id, mode):
    if mode == 'all':
        s3.Bucket(bucket_name).download_file('time_trials/time_trial_info.json', '/tmp/time_trial_info.json')
        f = open('/tmp/time_trial_info.json')
        time_trial_info = json.load(f)
        for json_obj in time_trial_info:
            clear_time_trial(user_id, json_obj)
        return {
            'statusCode': 200,
            'body': "user {} removed from leaderboards".format(user_id)
        }

    elif mode == 'none':
        clear_glb(user_id)
        return {
            'statusCode': 200,
            'body': "user {} removed from leaderboards".format(user_id)
        }

    elif mode != 'aaa':
        clear_time_trial(user_id, mode)
        return {
            'statusCode': 200,
            'body': "user {} removed from leaderboards".format(user_id)
        }

    else:
        s3.Bucket(bucket_name).download_file('time_trials/time_trial_info.json', '/tmp/time_trial_info.json')
        f = open('/tmp/time_trial_info.json')
        time_trial_info = json.load(f)
        for json_obj in time_trial_info:
            clear_time_trial(user_id, json_obj)

        clear_glb(user_id)
        return {
            'statusCode': 200,
            'body': "user {} removed from leaderboards".format(user_id)
        }


def lambda_handler(event, context):
    user_id = event['headers']['UID']
    try:
        mode = event['headers']['TimeTrialID']
    except:
        mode = 'aaa'
    return clear_data(user_id, mode)