import sys
import logging
import boto3
import json
from botocore.exceptions import ClientError

'''
CODE BY FIZZYPINE, NOT LEAKED LOL
'''

rdsData = boto3.client('rds-data')
cluster_arn = ""
secret_arn = ""

logger = logging.getLogger()
logger.setLevel(logging.INFO)

'''
Options are defined by the HTTP headers passed through the request, structure as follows

{
headers: {
    LocalSpace : {Global, TimeTrial},
    Type : {Top, Self}
    Leaderboard: {all global leaderboards and timetrial names as defined by time_trial_info.json}
    UID: {roblox_id}
    }
}

'''


def lambda_handler(event, context):
    try:
        if event['headers']['LocalSpace'] == 'Global':
            if event['headers']['Type'] == 'Top':
                logger.info("Global Top In")
                if event['headers']['Leaderboard'] == 'WALLBOOST_SPEED':
                    search_sql = "SELECT USER_ID, {0} from global_leaderboard WHERE WALLBOOST_SPEED > 0 ORDER BY {0} LIMIT 50".format(
                        event['headers']['Leaderboard'])

                else:
                    search_sql = "SELECT USER_ID, {0} from global_leaderboard ORDER BY {0} DESC LIMIT 50".format(
                        event['headers']['Leaderboard'])
                logger.info("TRANSAC: begin glob top")
                response1 = rdsData.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database='DATABASE',
                    sql=search_sql)
                logger.info("TRANSAC: response")

                data = response1['records']
                # print(data)
                list = {'Leaderboard': [{"UID": x[0]['longValue'], "Rating": x[1]['doubleValue']} for x in data]}

                json_data = json.dumps(list)
                # print(json_data)

            if event['headers']['Type'] == 'Self':
                search_sql = "SELECT USER_ID, {0} from global_leaderboard WHERE USER_ID in ({1})".format(
                    event['headers']['Leaderboard'], event['headers']['UID'])
                logger.info("{}".format(search_sql))
                logger.info("TRANSAC: begin global self")
                response1 = rdsData.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database='DATABASE',
                    sql=search_sql)
                logger.info("TRANSAC: response")

                data = response1['records']
                print(data)
                list = {'Leaderboard': [{"UID": x[0]['longValue'], "Rating": x[1]['doubleValue']} for x in data]} # returns a list of 500(?) results from the database

                json_data = json.dumps(list)
                # print(json_data)



        elif event['headers']['LocalSpace'] == 'TimeTrial':
            if event['headers']['Type'] == 'Self':
                try:
                    search_sql = "SELECT USER_ID, TIME from {} WHERE USER_ID in ({1})".format(
                        event['headers']['Leaderboard'], event['headers']['UID'])
                    logger.info("{}".format(search_sql))
                except ClientError as ex:
                    if ex.response['Error']['Code'] == 'NoSuchKey':
                        return {
                            'statusCode': 204  # Explanation: If the person has not loaded in prior they wont have a save file and thus wont have a leaderboard presence
                        }
                logger.info("TRANSAC: begin global self")
                response1 = rdsData.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database='DATABASE',
                    sql=search_sql)
                logger.info("TRANSAC: response")

                data = response1['records']
                list = {'Leaderboard': [{"UID": x[0]['longValue'], "Time": x[1]['doubleValue']} for x in data]}

                json_data = json.dumps(list)

            if event['headers']['Type'] == 'Top':
                search_sql = "SELECT USER_ID, TIME from {0} ORDER BY TIME LIMIT 50".format(
                    event['headers']['Leaderboard'])
                logger.info("TRANSAC: begin global t")
                response1 = rdsData.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database='DATABASE',
                    sql=search_sql)
                logger.info("TRANSAC: response")

                data = response1['records']
                list = {'Leaderboard': [{"UID": x[0]['longValue'], "Time": x[1]['doubleValue']} for x in data]}

                json_data = json.dumps(list)
                # print(json_data)
        return {
            'statusCode': 200,
            'body': json_data
        }

    except ClientError as ex:
        if ex.response['Error']['Code'] == 'NoSuchKey':
            return {
                'statusCode': 204 # Explanation: If the person has not loaded in prior they wont have a save file and thus wont have a leaderboard presence
            }