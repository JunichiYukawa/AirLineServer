# -*- coding: utf-8 -*-

import tweepy

READONLY_CONSUMER_KEY = 'xa78PeGeQF6G6y5Jwp7Og9Oco'
READONLY_CONSUMER_SECRET = 'AncK0rn0LLBGq4yrFzQwYBz0jVNH9VaqbgoJYGB8HKFE5Yeg5z'


def get_authorization_url(callback_url):
    '''
    認証トークンのためのURLとリクエストトークンのタプルを返却する
    '''
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, callback_url)
    return (auth.get_authorization_url(), auth.request_token)


def get_auth_from_token(callback_url, request_token, oauth_verifier):
    '''
    リクエストトークンと認証値からアクセストークンとパスを取得する
    '''
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.request_token = request_token
    auth.get_access_token(oauth_verifier)
    return auth