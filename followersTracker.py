# -*- coding: utf-8 -*-
import csv
import time
import re
import codecs, cStringIO
from argparse import ArgumentParser
import os, os.path
import tweepy
from time import gmtime, strftime

# Twitter API credentials
consumer_key = "Your Consumer Key"
consumer_secret = "Your consumer secret"
access_key = "Your access key"
access_secret = "Your access secret"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)

def parseArgs():
    parser = ArgumentParser()
    parser.add_argument(
        '-a',
        '--account',
        help='Twitter account to get followers from.',
        type=str,
        metavar='account'
    )
    
    return parser.parse_args()


def getFollowers(api, twitter_account):
    """
    Return the followers ids of the given twitter account.

    api -- the tweetpy API object
    twitter_account -- the Twitter handle of the user
    """

    user_ids = []

    try:
        for page in tweepy.Cursor(api.followers_ids, id=twitter_account, count=5000).pages():
            user_ids.extend(page)

    except tweepy.RateLimitError:
        print "RateLimitError...waiting 1000 seconds to continue"
        time.sleep(1000)
        for page in tweepy.Cursor(api.followers_ids, id=twitter_account, count=5000).pages():
            user_ids.extend(page)

    followers = []

    for start in xrange(0, len(user_ids), 100):
        end = start + 100

        try:
            followers.extend(api.lookup_users(user_ids[start:end]))

        except tweepy.RateLimitError:
            print "RateLimitError...waiting 1000 seconds to continue"
            time.sleep(1000)
            followers.extend(api.lookup_users(user_ids[start:end]))

    tmp = set()
    for user in followers:
        tmp.add(user.screen_name)
            
    return set(tmp)


def getReport(followers, DIR):
    # new file data
    currentNumOfFollowers = len(followers)
    fileNum = numberOfFiles(DIR)
    filename = DIR + str(fileNum) + '.txt'
    currentTime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        
    # previous file data
    prevFilename = DIR + str(fileNum-1) + '.txt'
    prevFollowers, time = readFileData(prevFilename)
    
    newFollowers = followers - prevFollowers
    unfollowers = prevFollowers - followers

    # if there is one or more follower or unfollower,
    # write data to a new file
    if len(newFollowers) != 0 or len(unfollowers) != 0:
        writeFileData(filename, currentTime, followers)

    report  = '-' * 40 + '\n'
    report += "New Followers (%d):\n" %len(newFollowers)
    report += '\n'.join(newFollowers)
    report += '\n\n'
    report += "New Unfollowers (%d):\n" %len(unfollowers)
    report += '\n'.join(unfollowers)
    report += '\n'
    
    return report

    
def readFileData(filePath):
    '''
    File format:
    <yyyy-mm-dd hh:mm:ss>
    <number-of-followers>
    <follower-id-0>
    <follower-id-1>
    ...
    '''
    followers = set()
    time = None
    with open(filePath, 'r') as f:
        time = f.readline()
        
        f.readline() # skip number of followers line
        
        # store followrs id
        for user in f:
            if user.strip() == '':
                continue
            followers.add(user.strip())
    
    return followers, time


def writeFileData(filename, currentTime, followers):
    '''
    File format:
    <yyyy-mm-dd hh:mm:ss>
    <number-of-followers>
    <follower-id-0>
    <follower-id-1>
    ...
    '''    
    currentNumOfFollowers = len(followers)
    with open(filename, 'w') as f:
        f.write(currentTime+'\n')
        f.write(str(currentNumOfFollowers)+'\n')
        for user in followers:
            f.write(user+'\n')


def numberOfFiles(path):
    count = 0
    for name in os.listdir(path):
        fileExt = name[name.find('.')+1:]
        if os.path.isfile(os.path.join(path, name)) and fileExt == "txt":
            count += 1
    return count


def initialize(TWITTER_ACCOUNT, DIR, followers):
    os.makedirs(TWITTER_ACCOUNT)
    print TWITTER_ACCOUNT + " is registered as a new user."
    print TWITTER_ACCOUNT + "has  %d followers and they are being tracked now.\n" %len(followers)
        
    currentTime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    filename = DIR + '0' + '.txt'
    writeFileData(filename, currentTime, followers)


def isNewUser(TWITTER_ACCOUNT):
    return not os.path.exists(TWITTER_ACCOUNT)


if __name__ == "__main__":
    args = parseArgs()
    
    TWITTER_ACCOUNT = args.account
    DIR = './%s/' %(TWITTER_ACCOUNT)
    
    print "Reading data...\n"
    followers = getFollowers(api, TWITTER_ACCOUNT)
    #followers, time = readFileData('test.txt')

    if isNewUser(TWITTER_ACCOUNT):
        initialize(TWITTER_ACCOUNT, DIR, followers)
    else:
        report = getReport(followers, DIR)
        print report
