import json
import os
import boto3
import botocore
import sys
import logging
import pymysql

'''
CODE BY FIZZYPINE, NOT LEAKED LOL
'''

'''
Options are defined by the HTTP headers passed through the request, structure as follows

{
headers: {
    TimeTrial: {all global leaderboards and timetrial names as defined by time_trial_info.json} #note, will only accept one time trial at a time, users should not be able to update multiple trials at once
    UID: {roblox_id}
    }

body: {} #replay of the time trial completed
}

'''

s3 = boto3.resource('s3')


def db_connect():
    rds_host = "RDS_HOST"
    name = "USER"
    password = "PASSWORD"
    db_name = "DATABASE"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    try:
        conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, connect_timeout=10)
    except pymysql.MySQLError as e:
        logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
        logger.error(e)
        return {
            'statusCode': 503,
            'body': 'error occured while connecting to database, please retry in 10 seconds'
        }

    logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")
    return conn


def lambda_handler(event, context):
    bucket_name = 'BUCKET_NAME'
    conn = db_connect()
    UID = event['headers']['UID']
    trial = event['headers']['TimeTrial']
    replay = 'https://{}.s3.amazonaws.com/time_trials/{}/{}.json'.format(bucket_name,trial, UID)

    try:
        s3_path = 'time_trials/{}/{}.json'.format(trial, UID)
        data = json.dumps(event['body'], separators=(',', ':')).encode('utf-8')
        s3.Bucket(bucket_name).put_object(Key=s3_path, Body=data)
        time = event['body']['Time']
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO {} (USER_ID, TIME, REPLAY) ".format(trial) +
                            "VALUES ({}, {}, '{}') ".format(UID, time, replay) +
                            "ON DUPLICATE KEY UPDATE " +
                            "TIME = {}, REPLAY = '{}';".format(time, replay))
                conn.commit()
                cur.close()


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

        except pymysql.err.OperationalError as err:
            print("Error: {}".format(err))
            return {
                'statusCode': 500,
                'body': 'mysql operational error occured, please contact fizzypine#0001 to review the error {}'.format(err)
            }

        except TypeError as e:
            print(e)
            pass

        except:
            e = sys.exc_info()[0]
            print(e)
            return {
                'statusCode': 500,
                'body': 'unhandled error occured while running SQL query, please contact fizzypine#0001 to review the error {}'.format(
                    e)
            }


    except botocore.exceptions.ClientError as e:
        return {
            'statusCode': 500,
            'body': 'ClientError please contact fizzypine#0001 to review the error {}'.format(e)
        }


    except:
        e = sys.exc_info()[0]
        print(e)
        return {
            'statusCode': 500,
            'body': 'unhandled error occured while running TimeTrial JSON update, please contact fizzypine#0001 to review the error {}'.format(
                e)
        }
    return {
        'statusCode': 200,
        'body': "Time Trial updated for user {}".format(event['headers']['UID'])
    }
