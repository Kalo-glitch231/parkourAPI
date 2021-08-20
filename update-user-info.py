import json
import os
import boto3
import pymysql
import logging
import sys
# import requests
import math
from botocore.exceptions import ClientError
import botocore

'''
CODE BY FIZZYPINE, NOT LEAKED LOL
'''

'''
Options are defined by the HTTP headers passed through the request, structure as follows

{
headers: {
    FileName: {main, meta}, #extensable to anything you want if you choose to split data or add new files to each user
    UID: {roblox_id}
    }

body: {} #JSON table of whatever you want stored in the files
}

returns json content of the requested file
'''

# with open('data.json') as json_file:
#    event = json.load(json_file)

s3 = boto3.resource('s3')
bucket_name = 'BUCKET_NAME'

rdsData = boto3.client('rds-data')

cluster_arn = ""
secret_arn = ""

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def db_connect():
    rds_host = "RDS CLUSTER"
    name = "USERNAME"
    password = "PASSWORD"
    db_name = "DB_NAME"

    try:
        conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name,
                               cursorclass=pymysql.cursors.DictCursor, connect_timeout=10)
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
    logger.info("PREP: S3 Preparing Connection")
    try:
        s3_path = 'user_data/{}/{}.json'.format(event['headers']['UID'], event['headers']['FileName'])
        d = json.dumps(event['body'], separators=(',', ':')).encode('utf-8')
    except:
        s3_path = 'user_data/{}/main.json'.format(event['headers']['UID'])
    data = json.dumps(event['body'], separators=(',', ':')).encode('utf-8')
    s3.Bucket(bucket_name).put_object(Key=s3_path, Body=data)
    logger.info("SUCCESS: Connection to s3 bucket succeeded")
    sql = update_settings(event, context)

    return {
        'statusCode': '200',
        'body': 'successfully updated user {}, {}'.format(event['headers']['UID'], sql)
    }


def update_settings(event, context):
    logger.info("PREP: Preparing new RDS access vars")
    conn = db_connect()
    user_id = event['headers']['UID']
    # create leaderboard scores

    # combo_score leaderboard score
    try:
        total_combo = event['body']['Stats']['TotalCombo']
        total_breaks = event['body']['Stats']['ComboBreaks']
        longest_combo = event['body']['Stats']['LongestCombo']
        highest_combo = event['body']['Stats']['MaxCombo']
        try:
            average_combo = total_combo / total_breaks
        except:
            average_combo = 0
        try:
            raw_combo = average_combo * longest_combo * highest_combo
        except:
            raw_combo = 0
        try:
            combo_score = max(1, raw_combo / (raw_combo ** .2) / 400)
        except:
            combo_score = 0
    except:
        pass

    # perfect_landing_ratio
    try:
        perfect_landings = event['body']['Stats']['PerfectLandings']
        landings = event['body']['Stats']['PerfectLandings']
        try:
            perfect_landing_ratio = perfect_landings / landings

        except:
            perfect_landing_ratio = 0
    except:
        pass
    # time_trial leaderboard score
    s3.Bucket(bucket_name).download_file('time_trials/time_trial_info.json', '/tmp/time_trial_info.json')
    f = open('/tmp/time_trial_info.json')
    time_trial_info = json.load(f)
    raw_scores = []
    combined_score = 0
    for json_obj in time_trial_info:
        try:
            with conn.cursor() as cur:
                # print(json_obj)
                query = "SELECT TIME FROM {} WHERE USER_ID = {}".format(json_obj, user_id)
                time_trial = cur.execute(query)
                result = cur.fetchone()
                for row in result:
                    score = math.floor(100 / ((result / time_trial_info[json_obj]) ** 1.4))
                    combined_score += score
                    cur.close()
                # print(records)




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

    # boosts
    try:
        combined_boost = 0
        count = 0
        for i in event['body']['_recentBoosts']:
            combined_boost += i
            count += 1

        if combined_boost == 0 or count == 0:
            boost_score = 0
        else:
            boost_score = combined_boost / count

        level = event['body']['Generic']['Level']

        try:
            global_ranking = ((combo_score + combined_score) / 2 * (.65 + perfect_landing_ratio * .35)) * 3.5
        except:
            global_ranking = 0

        # TODO: DEATH RATIO
        playtime = event['body']['Stats']['Playtime']
        grappler_elo = event['body']['Ranked']['Grappler']['Elo']
        grappler_losses = event['body']['Ranked']['Grappler']['Losses']
        grappler_wins = event['body']['Ranked']['Grappler']['Wins']
        mag_elo = event['body']['Ranked']['MagRail']['Elo']
        mag_losses = event['body']['Ranked']['MagRail']['Losses']
        mag_wins = event['body']['Ranked']['MagRail']['Wins']
        gearless_elo = event['body']['Ranked']['Gearless']['Elo']
        gearless_wins = event['body']['Ranked']['Gearless']['Wins']
        gearless_losses = event['body']['Ranked']['Gearless']['Losses']

        if grappler_losses + grappler_wins + mag_losses + mag_wins + gearless_losses + gearless_wins > 10:
            if grappler_elo > mag_elo and grappler_elo > gearless_elo:
                cumulativeElo = grappler_elo + (mag_elo + gearless_elo) / 32
            elif mag_elo > grappler_elo and mag_elo > gearless_elo:
                cumulativeElo = mag_elo + (grappler_elo + gearless_elo) / 32
            elif gearless_elo > grappler_elo and gearless_elo > mag_elo:
                cumulativeElo = gearless_elo + (grappler_elo + mag_elo) / 32
            else:
                cumulativeElo = (grappler_elo + mag_elo + gearless_elo) / 32

        # user_name =requests.get("https://users.roblox.com/v1/users/{}".format(user_id)).json()["name"]
        inventory = 'https://{}}.s3.amazonaws.com/user_data/{}/Inventory.json'.format(bucket_name,user_id)
        settings = 'https://{}.s3.amazonaws.com/user_data/{}/Settings.json'.format(bucket_name,user_id)

        # Other Stats
        resets = event['body']['Stats']['Resets']
        # warn_count = event['body']['_moderation']['Warnings']

        glb_sql = (
                "INSERT INTO global_leaderboard (USER_ID, COMBO_SCORE, PLAYTIME, RANKED, WALLBOOST_SPEED, TIME_TRIALS, LEVELS, GLOBAL_RATING) " +
                "VALUES ({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}) ".format(user_id, combo_score, playtime, cumulativeElo,
                                                                          boost_score, combined_score, level,
                                                                          global_ranking) +
                "ON DUPLICATE KEY UPDATE " +
                "COMBO_SCORE = {}, PLAYTIME = {}, RANKED = {}, WALLBOOST_SPEED = {}, TIME_TRIALS = {}, LEVELS = {}, GLOBAL_RATING = {};".format(
                    combo_score, playtime, cumulativeElo, boost_score, combined_score, level, global_ranking))

        settings_sql = ("INSERT INTO settings (USER_ID, SETTINGS)\n" +
                        "VALUES ({0}, '{1}')\n".format(user_id, settings) +
                        "ON DUPLICATE KEY UPDATE\n" +
                        "SETTINGS = '{}'; ".format(settings))

        user_sql = ("INSERT INTO users_inf (USER_ID, DUNCED, BANNED, inventory, RESETS, fk_GLB_ID, fk_Settings_ID)\n" +
                    "VALUES ({0}, false, false, '{1}', {2}, {0}, {0})\n ".format(user_id, inventory, resets) +
                    "ON DUPLICATE KEY UPDATE\n" +
                    "inventory = '{0}',fk_GLB_ID = {1}, fk_Settings_ID ={1}, RESETS = {2};".format(inventory, user_id,
                                                                                                   resets))

        grappler_sql = ("INSERT INTO grappler_ranked (USER_ID, WINS, LOSSES, ELO) " +
                        "VALUES ({0}, {1}, {2}, {3}) ".format(user_id, grappler_wins, grappler_losses, grappler_elo) +
                        "ON DUPLICATE KEY UPDATE " +
                        "WINS = {0}, LOSSES = {1}, ELO = {2};".format(grappler_wins, grappler_losses, grappler_elo))

        gearless_sql = ("INSERT INTO gearless_ranked (USER_ID, WINS, LOSSES, ELO) " +
                        "VALUES ({0}, {1}, {2}, {3}) ".format(user_id, gearless_wins, gearless_losses, gearless_elo) +
                        "ON DUPLICATE KEY UPDATE " +
                        "WINS = {0}, LOSSES = {1}, ELO = {2};".format(gearless_wins, gearless_losses, gearless_elo))

        mag_sql = ("INSERT INTO mag_ranked (USER_ID, WINS, LOSSES, ELO) " +
                   "VALUES ({0}, {1}, {2}, {3}) ".format(user_id, mag_wins, mag_losses, mag_elo) +
                   "ON DUPLICATE KEY UPDATE " +
                   "WINS = {0}, LOSSES = {1}, ELO = {2};".format(mag_wins, mag_losses, mag_elo))

        logger.info("TRANSAC: Transacting with RDS API")

        try:
            tr = rdsData.begin_transaction(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database='prod')
            logger.info("TRANSAC: INIT")

            response1 = rdsData.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database='prod',
                sql=glb_sql,
                transactionId=tr['transactionId'])
            logger.info("TRANSAC: response 1")

            response2 = rdsData.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database='prod',
                sql=settings_sql,
                transactionId=tr['transactionId'])
            logger.info("TRANSAC: response 2")

            response3 = rdsData.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database='prod',
                sql=user_sql,
                transactionId=tr['transactionId'])
            logger.info("TRANSAC: response 3")

            response4 = rdsData.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database='prod',
                sql=grappler_sql,
                transactionId=tr['transactionId'])
            logger.info("TRANSAC: response 4")

            response5 = rdsData.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database='prod',
                sql=gearless_sql,
                transactionId=tr['transactionId'])
            logger.info("TRANSAC: response 5")

            response6 = rdsData.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database='prod',
                sql=mag_sql,
                transactionId=tr['transactionId'])
            logger.info("TRANSAC: response 6")

            cr = rdsData.commit_transaction(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                transactionId=tr['transactionId'])

            logger.info("TRANSAC: commit")

            return 'SQL Okay'

            logger.info("TRANSAC: TRANSAC succeeded")


        except pymysql.err.IntegrityError as err:
            print("Error: {}".format(err))
            return {
                'statusCode': 500,
                'body': 'mysql integrety error occured, please contact fizzypine#0001 to review the error {}'.format(
                    err)
            }

        except pymysql.err.OperationalError as err:
            print("Error: {}".format(err))
            return {
                'statusCode': 500,
                'body': 'mysql operational error occured, please contact fizzypine#0001 to review the error {}'.format(
                    err)
            }

        except NameError as err:
            print("Error: {}".format(err))
            return {
                'statusCode': 500,
                'body': 'NameError has occured, please contact fizzypine#0001 to review the error {}'.format(err)
            }

        except pymysql.err.ProgrammingError as e:
            print(e)
            return {
                'statusCode': 500,
                'body': 'unhandled programming error while running SQL query, please contact fizzypine#0001 to review the error {}'.format(
                    e)
            }

        except TypeError as e:
            print(e)
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
            print(e)
            return {
                'statusCode': 500,
                'body': 'unhandled error occured while running SQL query, please contact fizzypine#0001 to review the error {}'.format(
                    e)
            }
    except:
        pass