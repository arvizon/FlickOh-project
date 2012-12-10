#!/usr/bin/env python # encoding: utf-8
"""
Created by Drew Conway on 2009-02-23.
Copyright (c) 2009. All rights reserved.

The purpose of this script is to generate a 
NetworkX DiGraph object based on the snowball
search results of a single starting node to 
K snowball rounds.

Ideas, code and algorithms by http://www.drewconway.com/zia/?p=345
Parts available at: https://gist.github.com/70375
Modified to use the most recent version of the twitter API and tweepy by Marti Hearst


INFO 290 FlickOh - Project
This code is modified to allow getting more friends and
deal with the API limit.

"""

import tweepy
import networkx 
from networkx import core
import time
import sys
import json
import codecs
import os

# You must set these with your credentials
consumer_key=""
consumer_secret=""
access_token=""
access_token_secret=""


auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)


# For a given user, get their friends, and create a new directed graph
# with the corresponding edges Store the screen names in the edges.
# Note that the API call get_user limits to only the first 100
# friends; more steps need to be taken to expand out to full friend
# lists, but some people's friends lists are really huge.
# If you have a very large number of friends you may need to truncate this list
# to avoid API problems.
AN_HOUR = 3630
TWENTY_MIN = 20*60
THIRTY_MIN = 30*60
LIMIT = 500

def create_egonet(twitter_api, seed_user):
    try:
        egonet = networkx.DiGraph()
        if (api.rate_limit_status()['remaining_hits'] < 5):
            print(api.rate_limit_status())
            time.sleep(TWENTY_MIN)
            
        friends = tweepy.Cursor(api.friends, id=seed_user).items(LIMIT)
        print "processing user" + str(seed_user)
        count = 0
        for fr in friends:
            count = count + 1
            egonet.add_edge(seed_user, str(fr.screen_name))
        print str(count) + ' edges added'
        return egonet
    except tweepy.error.TweepError as e:
        print e.reason
        return False


# Get those people's friends networks, and merge them into the current network
# The network compose operation can increase the in degree of the nodes
def build_friends_of_friends_network(twitter_api, cur_network):
    min_degree = 1
    users = nodes_at_degree(cur_network, min_degree)
    for user in users:
        time.sleep(1)
        new_network = create_egonet(twitter_api, user)
        if new_network != False:
            cur_network = networkx.compose(cur_network, new_network)
            print(str(networkx.info(cur_network)))
    return cur_network

# Pull out those nodes of degree at least min_degree
def nodes_at_degree(network, min_degree):
    d = network.degree()
    d = d.items()
    return [(user) for (user,degree) in d if (degree >= min_degree)]

# Save these results for later use, if needed
def save_network(network, original_seed):
    network._name = "original_seed_network"
    networkx.write_edgelist(network, path="twitter_network_edgelist.csv", delimiter='\t')

# A k-core is a maximal subgraph that contains nodes of degree k or
# more.  So a 2-core analysis will identify a subgraph of people with
# at least 2 links among them.  This gets more central members among
# your friends.  NetworkX contains a specific module for k-core
# analysis, so we will load it and create a subgraph of the 2-core.
# The last line lets you inspect the results.

def core_the_network(new_network, k):
    G = new_network
    kcores = core.find_cores(G)
    core_items = kcores.items()
    two_core_or_higher = [(a) for (a,b) in core_items if b>(k-1)]
    K = networkx.subgraph(G, two_core_or_higher)
    print(str(networkx.info(K)))
    return K

# Now you have a subgraph of densely connected Twitter friends. The
# next step is to get a list of your friends friends that you
# currently do not follow.  This expands out from the K-core to find
# people you might not have considered following.  This will tell you
# the open triads in your network.

def find_core_friends(cored_network, original_seed):
    K = cored_network
    # get your current friends from K
    N = K.neighbors(original_seed)
    F = []
    # for each of your current friends, gather their friends.  There hopefully will be repeats.
    for u in N:
        D = K.neighbors(u)
        for i in D:
            if N.count(i) < 1 and i is not original_seed:
                F.append(i)
    return F

# The more often a user shows up in the F list, the more of your friends
# that already follow that person. Therefore, we will want to get a
# frequency count of the names in this list; the higher a users
# count, the more likely you will want to be friends with that
# person, or close that triad.

def order_new_friends(friend_counts):
	F = friend_counts
	counts = dict((k, F.count(k)) for k in set(F))
	counts_items=counts.items()
	counts_items=[(b,a) for (a,b) in counts_items]
	counts_items.sort()
	counts_items.reverse()
	ff = open('suggested_friends', 'w')
	for i in counts_items:
		ff.write(str(i[0])+' of your friends are already following '+i[1] + '\n')
		print(str(i[0])+' of your friends are already following '+i[1])


from operator import itemgetter    
# show those friends with the most in-degree of this group
# Note that this will be biased towards those people with many followers
def find_highest_degree_friends(K):
    items = K.in_degree().items()
    items.sort(key=itemgetter(1))
    items.reverse()
    print(str(items[0:20]))

# Compute centrality measures.
# First have to convert to undirected graph to compute centrality
# either used to_undirected or just to
# h = Graph(g)
def highest_centrality(cent_dict):
    cent_items=[(b,a) for (a,b) in cent_dict.iteritems()]
    cent_items.sort()
    cent_items.reverse()
    return tuple(reversed(cent_items[0:20]))





    


