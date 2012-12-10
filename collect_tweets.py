#!/usr/bin/env python # encoding: utf-8
"""
INFO 290 - FlickOh Project
Author: Natth
Usage: python collect_tweets.py 'users_file'
"""

import tweepy
import time
import sys
import json


consumer_key=""
consumer_secret=""
access_token=""
access_token_secret=""

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

THIRTY_MIN = 30*60


def collect_tweets(users_file):
    """ Collect statuses of the users from the file and write the results in the JSON format.

    Note that the API limits 350 queries per hour and each query will
    return at most 20 statuses. So we limit the number of statuses to 60 per user.
    Once the account hits the limit, the program will sleep until it is able to
    retrieve data from the API. 

    """
    count = 1
    users_f = open(users_file, 'r')    
    logfile = open('statuses_' + users_file.split('.')[0] + '.json', 'w')
    logfile.write('{')
    output = {}
    global api
    for name in users_f.readlines():
        if (api.rate_limit_status()['remaining_hits'] < 8):
            print(api.rate_limit_status())
            time.sleep(THIRTY_MIN)
        try:
            print 'processed ' + str(count) + ' ' + name
            count += 1
            user = api.get_user(name.strip())
            statuses = api.user_timeline(id=user.id, count=60)

            st_list = []
            for status in statuses:
                temp = {}
                temp['text'] = status.text
                temp['created_at'] = str(status.created_at)
                temp['id'] = status.id
                temp['retweeted'] = status.retweeted
                st_list.append(temp)

            output[name.strip()] = st_list

            logfile.write('\"'+name.strip()+'\":')
            logfile.write(json.dumps(st_list))
            logfile.write(',\n')            
        except tweepy.error.TweepError as e:
            print e.reason
            continue

    logfile.write('}')
        
    users_f.close()
    logfile.close()

