# -*- coding: utf-8 -*-
from datetime import datetime
import uuid
from flask import jsonify, session, request, url_for, redirect, abort, g, render_template
from flask_restless import APIManager

from shop import app, db, auth
from shop.models import User, Activity, Line
import tweet


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


manager = APIManager(
    app,
    preprocessors=dict(
        POST=[auth_func],
        GET_SINGLE=[auth_func],
        GET_MANY=[auth_func],
        PATCH_SINGLE=[auth_func],
        PATCH_MANY=[auth_func],
        DELETE_SINGLE=[auth_func],
        DELETE_MANY=[auth_func]),
    flask_sqlalchemy_db=db
)

@app.route('/shop', methods=['GET'])
def shop_view():
    act_uuid = request.args.get('i')
    #if uuid is None:
    #    abort(404)
    #uuid = uuid.replace('_', '-')
    #act = Activity.query.filter(Activity.uuid==uuid).first()
    #if act is None:
    #    abort(404)
    callback_url = '/twitter_redirect'
    twitter_url, request_token = tweet.get_authorization_url(callback_url)
    session['request_token'] = request_token
    session['act_uuid'] = act_uuid
    return render_template('shop.html', act=dict(name="test"), twitter_url=twitter_url)

@app.route('/twitter_redirect')
def add_member():
    '''
    Twitterで認証を受けたらここにくる

    やること: 客と行列を取得する。なければ作る。
    '''
    verifier = request.GET.get('oauth_verifier')
    token = session.get('request_token')
    act_uuid = session.get('act_uuid')
    if verifier is None or token is None or act_uuid is None:
        abort(400)
    session.delete('request_token')
    # 並ぶ対象のActivityをゲットする
    act = Activity.query.filter(Activity.uuid == act_uuid).first()
    if act is None:
        abort(404)

    # 客を特定する。なければ作る。
    auth = tweet.get_auth_from_token(token, verifier)
    user = User.query.filter(
        User.twitter_token==auth.access_token,
        User.twitter_secret==auth.access_secret).first()
    if user is None:
        user = User(
            twitter_token=auth.access_token,
            twitter_secret=auth.access_token_secret,
            twitter_name=auth.username)
        db.session.add(user)
        db.session.commit()

    # 行列を特定する。なければ作る
    line = Line.query.filer(Line.activity_id==act.id, Line.user_id==user.id).first()
    if line is None:
        line = Line(uuid=str(uuid.uuid4()),activity_id=act.id,user_id=user.id)
        db.session.add(line)
        db.session.commit()

    # 行列のuuidは他の人に絶対見せちゃだめ
    redirect(url_for(line_view, line_no=line.uuid))


@app.route('/line/<line_no>', methods=['GET'])
def line_view(line_no):
    '''
    ここにはTwitter認証ができた人しか到達してはいけない
    今はURL平文だけど、そのうちTwitter認証ログインを真面目に実装する
    '''
    act_uuid = session.get('act_uuid')
    if act_uuid is None:
        abort(404)


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

    if activity_start_date:
        start_date = datetime.strptime(activity_start_date, "%Y-%m-%dT%H:%M:%S")
    else:
        start_date = None
    if activity_end_date:
        end_date = datetime.strptime(activity_end_date, "%Y-%m-%dT%H:%M:%S")
    else:
        end_date = None

    act = Activity(
        user_id=g.user.id,
        uuid=str(uuid.uuid4()),
        activity_name=activity_name,
        activity_location=activity_location,
        activity_start_date=start_date,
        activity_end_date=end_date,
        activity_description=activity_description,
        activity_url=activity_url,
        activity_template=activity_template
    )
    db.session.add(act)
    db.session.commit()

    msg = "【テスト】{0}\nhttp://vourja.info/shop/?access={1}".format(
        activity_template, act.uuid.replace('-', '_'))

    #tweet.post(msg)

    return jsonify(act.serialize)

