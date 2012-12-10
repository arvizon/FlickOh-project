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

def combine_files(directory, nodelist_file):
    """ Combine files of statuses in the specified directory into
    a single JSON file.

    This will be convenient for Sentiment API and filter movie-relevant
    statuses. The output file will contain a list of statuses with the
    field 'user' added.

    @param
    directory - the directory contains the files that need to be combined.
    nodelist_file - the file contains all the nodes in the network
    """
           
    user_network = set()
    for user in open(nodelist_file, 'r'):
        user_network.add(user.strip())

    user_statuses = {}
    for file_ in os.listdir(directory):
        filename = directory + file_
        temp_file = codecs.open(filename, 'r', 'utf8', 'replace')
        temp = json.loads(temp_file.read())
        user_statuses.update(temp)
        #print str(len(temp)) + " added"
        temp_file.close()

    final_output = {}
    #final_output['data'] = []
    outfile = open('combined_statuses.json', 'w')
    outfile.write('{\"data\": [\n')
    for user in user_network:
        if (user in user_statuses):
            stt_list = user_statuses[user]  ## list of statuses
        else:
            continue
        for each in stt_list:
            each['user'] = user   ## add field 'user'
            outfile.write(json.dumps(each)+',\n')

    outfile.close()

