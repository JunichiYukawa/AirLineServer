# -*- coding: utf-8 -*-
from datetime import datetime
import uuid
import io
from flask import jsonify, request, url_for, redirect, abort, g, render_template, make_response, session

from shop import app, db, auth
from shop.models import User, Activity, Line, Customer

import tweepy
from tweepy.error import TweepError, RateLimitError

import qrcode

READWRITE_CONSUMER_KEY = 'L6StgFi57qsxCS3GOvzRrj5I7'
READWRITE_CONSUMER_SECRET = 'DYu4bES4onS68ZSf6jViuHjqXzDr6GaBBAAhHAhywo3ju6DPIP'
READONLY_CONSUMER_KEY = 'xa78PeGeQF6G6y5Jwp7Og9Oco'
READONLY_CONSUMER_SECRET = 'AncK0rn0LLBGq4yrFzQwYBz0jVNH9VaqbgoJYGB8HKFE5Yeg5z'

CALLBACK_URL = 'http://192.168.111.109:5000/twitter_redirect'

@auth.verify_password
def verify_password(token, secret):
    # first try to authenticate by token
    app.logger.debug('verify password >> token:{0} secret:{1}'.format(token, secret))
    user = User.verify_auth_token(token)
    if not user:
        user = User.query.filter_by(twitter_token=token, twitter_secret=secret).first()
        if user is None:
            return False
    g.user = user
    return True


def auth_func(**kw):
    app.logger.debug("auth_func")
    pass

def str2date(str):
    if str:
        return datetime.strptime(str, "%Y-%m-%dT%H:%M:%S").strftime("%Y年%m月%d日 %H時%S分").decode('utf-8')
    else:
        return ""


def tweet_post(access_token, access_secret, message):
    '''
    Tweetする
    :param access_token:
    :param access_secret:
    :param message:
    :return: 1:正常 2:認証エラー 3:ツイート制限
    '''
    try:
        tweet_auth = tweepy.OAuthHandler(READWRITE_CONSUMER_KEY, READWRITE_CONSUMER_SECRET)
        tweet_auth.set_access_token(access_token, access_secret)
        api = tweepy.API(tweet_auth)
        api.update_status(status=message)
    except TweepError as e:
        print e
        return 2
    except RateLimitError as e:
        return 3
    return 1


@app.route('/', methods=['GET'])
def root():
    print session
    return redirect('/shop')


@app.route('/shop', methods=['GET'])
def shop_view():
    act_uuid = request.args.get('i')
    if act_uuid is None:
        abort(404)
    act_uuid = act_uuid.replace('_', '-')
    act = Activity.query.filter(Activity.uuid==act_uuid).first()
    if act is None:
        abort(404)

    handler = tweepy.OAuthHandler(READONLY_CONSUMER_KEY, READONLY_CONSUMER_SECRET, CALLBACK_URL)
    twitter_url = handler.get_authorization_url()

    session['request_token'] = handler.request_token
    session['act_uuid'] = act_uuid

    print session
    # static
    url_for('static', filename="style.css")
    return render_template('shop.html', act=act.serialize, start_date=str2date(act.activity_start_date), twitter_url=twitter_url)


@app.route('/twitter_redirect')
def add_member():
    '''
    Twitterで認証を受けたらここにくる

    やること: 客と行列を取得する。なければ作る。
    '''
    print session
    verifier = request.args.get('oauth_verifier')
    oauth_token = request.args.get('oauth_token')
    request_token = session.get('request_token')
    session.pop('request_token', None)
    act_uuid = session.get('act_uuid')

    if verifier is None or request_token is None or act_uuid is None:
        abort(400)

    # 並ぶ対象のActivityをゲットする
    act = Activity.query.filter(Activity.uuid == act_uuid).first()
    if act is None:
        abort(404)

    # 客を特定する。なければ作る。
    handler = tweepy.OAuthHandler(READONLY_CONSUMER_KEY, READONLY_CONSUMER_SECRET, CALLBACK_URL)
    handler.request_token = {
        'oauth_token': oauth_token,
        'oauth_token_secret': request_token['oauth_token_secret']
    }

    access_token, access_token_secret = handler.get_access_token(verifier)

    customer = Customer.query.filter(
        Customer.twitter_token==access_token,
        Customer.twitter_secret==access_token_secret).first()
    if customer is None:
        handler.get_username()
        customer = Customer(
            twitter_token=access_token,
            twitter_secret=access_token_secret,
            twitter_name=handler.username)
        db.session.add(customer)
        db.session.commit()

    # 行列を特定する。なければ作る
    line = Line.query.filter(Line.activity_id==act.id, Line.customer_id==customer.id).first()
    if line is None:
        line = Line(uuid=str(uuid.uuid4()),activity_id=act.id,customer_id=customer.id)
        db.session.add(line)
        db.session.commit()

    # 行列のuuidは他の人に絶対見せちゃだめ
    return redirect(url_for('.line_view', line_no=line.uuid))


@app.route('/line/<line_no>', methods=['GET'])
def line_view(line_no):
    '''
    ここにはTwitter認証ができた人しか到達してはいけない
    今はURL平文だけど、そのうちTwitter認証ログインを真面目に実装する
    '''
    act_uuid = session.get('act_uuid')
    if act_uuid is None:
        abort(404)

    # 並ぶ対象のActivityをゲットする
    act = Activity.query.filter(Activity.uuid == act_uuid).first()
    if act is None:
        abort(404)

    return render_template('line.html',
        act=act.serialize,
        line_uuid=line_no,
        start_date=str2date(act.activity_start_date))


@app.route('/line/qr')
def get_image():
    line_uuid = request.args.get('i')
    if line_uuid is None:
        abort(404)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(line_uuid)
    qr.make(fit=True)
    pil_image = qr.make_image()
    output = io.BytesIO()
    pil_image.save(output, format="png")
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'image/jpeg'
    return response


@app.route('/api/tw/register', methods = ['POST'])
def new_user():
    '''Twtitterの登録'''
    twitter_id = request.json.get('twitter_id')
    token = request.json.get('token')
    secret = request.json.get('secret')
    name = request.json.get('name')

    if twitter_id is None or token is None or secret is None or name is None:
        abort(400) # missing arguments
    if User.query.filter_by(twitter_id = twitter_id).first() is not None:
        abort(409) # existing user
    user = User(twitter_id = twitter_id, twitter_token = token, twitter_secret = secret, twitter_name = name)
    db.session.add(user)
    db.session.commit()
    return (jsonify({
        "auth_token": user.generate_auth_token(),
        'twitter_name': user.twitter_name,
        'twitter_token': user.twitter_token,
        'twitter_secret': user.twitter_secret,
        'twitter_id': user.twitter_id
        }), 200)


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    '''トークンの取得'''
    app.logger.debug('get_auth_token')
    return jsonify({ 'auth_token': g.user.generate_auth_token() })


@app.route('/api/myinfo')
@auth.login_required
def get_my_info():
    '''自分自身の情報を取得'''
    return (jsonify({
        "auth_token": g.user.generate_auth_token(),
        'twitter_name': g.user.twitter_name,
        'twitter_token': g.user.twitter_token,
        'twitter_secret': g.user.twitter_secret,
        'twitter_id': g.user.twitter_id
        }), 200)


@app.route('/api/activities', methods=['GET'])
@auth.login_required
def get_my_activity():
    '''ユーザーのアクティビティを全て取得'''
    objects = [ act.serialize for act in Activity.query.filter(Activity.user_id==g.user.id).all()]
    data = dict(total=len(objects), objects=objects)
    return (jsonify(data), 200)


@app.route('/api/activities', methods=['POST'])
@auth.login_required
def post_my_activity():
    '''アクティビティを登録'''
    activity_name = request.json.get('activity_name')
    activity_location = request.json.get('activity_location')
    activity_start_date = request.json.get('activity_start_date')
    activity_end_date = request.json.get('activity_end_date')
    activity_description = request.json.get('activity_description')
    activity_url = request.json.get('activity_url')
    activity_template = request.json.get('activity_template')

    act = Activity(
        user_id=g.user.id,
        uuid=str(uuid.uuid4()),
        activity_name=activity_name,
        activity_location=activity_location,
        activity_start_date=activity_start_date,
        activity_end_date=activity_end_date,
        activity_description=activity_description,
        activity_url=activity_url,
        activity_template=activity_template
    )
    db.session.add(act)
    db.session.commit()

    msg = "【自宅ネットワークでテスト中】{0}\nhttp://{1}/shop?i={2}".format(
        activity_template,
        '192.168.111.109:5000',
        act.uuid.replace('-', '_'))

    tweet_post(g.user.twitter_token, g.user.twitter_secret, msg)

    return jsonify(act.serialize)

