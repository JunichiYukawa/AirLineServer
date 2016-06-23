# -*- coding: utf-8 -*-

import tweepy
from tweepy.error import TweepError, RateLimitError

CONSUMER_KEY = 'L6StgFi57qsxCS3GOvzRrj5I7'
CONSUMER_SECRET = 'DYu4bES4onS68ZSf6jViuHjqXzDr6GaBBAAhHAhywo3ju6DPIP'
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)


def post(access_token, access_secret, message):
    '''
    Tweetする
    :param access_token:
    :param access_secret:
    :param message:
    :return: 1:正常 2:認証エラー 3:ツイート制限
    '''
    try:
        auth.set_access_token(access_token, access_secret)
        api = tweepy.API(auth)
        api.update_status(status=message)
    except TweepError as e:
        return 2
    except RateLimitError as e:
        return 3
    return 1
