import sys
import logging
import boto3
import json
import pymysql
from botocore.exceptions import ClientError

'''
returns either the leaderboard of a timetrial or the replay of a users time trial depending on the mode

mode 1 is replay
mode 0,2 is leaderboard
'''

'''
CODE BY FIZZYPINE, NOT LEAKED LOL
'''

'''
Options are defined by the HTTP headers passed through the request, structure as follows

{
headers: {
    Replay = {'1', '0'} #these are picked up as strings due to limitations in the roblox HTTP service
    TimeTrial: {all global leaderboards and timetrial names as defined by time_trial_info.json} #note, will only accept one time trial at a time, cant do multiple in one call at the moment
    UID: {roblox_id}
    }

}

'''

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cluster_arn = ""
secret_arn = ""
bucket_name = "BUCKET NAME"

def db_connect():
    rds_host = "RDS_HOSTS"
    name = "USERNAME"
    password = "PASSWORD"
    db_name = "DATABASE"

    try:
        conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, connect_timeout=10)
    except pymysql.MySQLError as e:
        return {
            'statusCode': 503,
            'body': 'error occured while connecting to database, please retry in 10 seconds'
        }

    return conn


def lambda_handler(event, context):
    if event['headers']['Replay'] == '1':
        logger.info("Replay Requested")
        try:
            s3 = boto3.resource('s3')
            content_object = s3.Object(bucket_name, 'time_trials/{0}/{1}.json'.format(event['headers']['TimeTrial'],
                                                                                          event['headers']['UID']))
            # content_object = s3.Object(bucket_name, 'time_trials/HerbalRun/18205436.json')
            print(content_object)
            file_content = content_object.get()['Body'].read().decode('utf-8')
            print(file_content)
            json_content = json.loads(file_content)

            return {
                'statusCode': 200,
                'body': json_content
            }


        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                return {
                    'statusCode': 204
                }


    else:
        rdsData = boto3.client('rds-data')
        conn = db_connect()
        get_time_sql = "SELECT TIME FROM {0} WHERE USER_ID = {1}".format(event['headers']['TimeTrial'],
                                                                         event['headers']['UID'])

        try:
            with conn.cursor() as cur:
                # print(json_obj)
                query = get_time_sql
                time_trial = cur.execute(query)
                result = cur.fetchone()
                # print(records)
                cur.close()

            return {
                'statusCode': 200,
                'body': '{}'.format(result)
            }

        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                return {
                    'statusCode': 204
                }

        except pymysql.err.ProgrammingError as e:
            print(e)
            return {
                'statusCode': 500,
                'body': 'unhandled programming error while running SQL query, please contact fizzypine#0001 to review the error {}'.format(
                    e)
            }

        except NameError as e:
            print(e)
            return {
                'statusCode': 500,
                'body': 'unhandled Name Error while running SQL query, please contact fizzypine#0001 to review the error {}'.format(
                    e)
            }

        except TypeError as e:
            # print(e)
            pass

        except ClientError as e:
            if e.response['Error']['Code'] == 'BadRequestException':
                return {
                    'statusCode': 500,
                    'body': 'unhandled Name Error while running SQL query, please contact fizzypine#0001 to review the error {}'.format(
                        e)
                }

        except ClientError as e:
            if e.response['Error']['Code'] == 'ParamValidationError':
                return {
                    'statusCode': 500,
                    'body': 'unhandled Name Error while running SQL query, please contact fizzypine#0001 to review the error {}'.format(
                        e)
                }

        except:
            e = sys.exc_info()[0]
            print(e)
            return {
                'statusCode': 500,
                'body': 'unhandled error occured while running SQL query, please contact fizzypine#0001 to review the error {}'.format(
                    e)
            }