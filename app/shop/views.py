# -*- coding: utf-8 -*-
from flask import jsonify, request, url_for, abort, g
from flask_restless import APIManager, ProcessingException

from shop import app, db, auth
from shop.models import User, Shop, Customer, Activity, Line



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

@app.route('/api/tw/register', methods = ['POST'])
def new_user():
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
    app.logger.debug('get_auth_token')
    return jsonify({ 'auth_token': g.user.generate_auth_token() })


@app.route('/api/myinfo')
@auth.login_required
def get_my_info():
    return (jsonify({
        "auth_token": g.user.generate_auth_token(),
        'twitter_name': g.user.twitter_name,
        'twitter_token': g.user.twitter_token,
        'twitter_secret': g.user.twitter_secret,
        'twitter_id': g.user.twitter_id
        }), 200)


@app.route('/api/activities')
@auth.login_required
def get_my_activity():
    objects = [ act.serialize for act in Activity.query.filter(Activity.user_id==g.user.id).all()]
    data = dict(total=len(objects), objects=objects)
    return (jsonify(data), 200)


manager.create_api(Shop, methods=['GET', 'POST', 'PUT', 'DELETE'])
manager.create_api(Customer, methods=['GET', 'POST', 'PUT', 'DELETE'])
manager.create_api(Activity, methods=['GET', 'POST', 'PUT', 'DELETE'])
manager.create_api(Line, methods=['GET', 'POST', 'PUT', 'DELETE'])
