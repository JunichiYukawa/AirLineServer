# -*- coding: utf-8 -*-
from shop import db, app
from sqlalchemy.orm import relation, backref
from sqlalchemy import ForeignKey
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)


# Datetime形式のDump
def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    twitter_token = db.Column(db.Text)
    twitter_secret = db.Column(db.Text)
    twitter_name = db.Column(db.Text)
    twitter_id = db.Column(db.Integer)

    def generate_auth_token(self, expiration = 3600):
        s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['id'])
        return user


class Shop(db.Model):
    __tablename__ = 'shops'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'))
    name = db.Column(db.Text)
    email = db.Column(db.Text)
    
    def __repr__(self):
        return '<Shop id={id} name={name!r} email={email!r}>'.format(
            id=self.id, name=self.name, email=self.email)


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'))
    
    user = relation(User, backref=backref('customer'))

    def __repr__(self):
        return '<Customer id={id}>'.format(
            id=self.id)


class Activity(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'))
    shop_id = db.Column(db.Integer, ForeignKey('shops.id'))
    activity_name = db.Column(db.Text)
    activity_location = db.Column(db.Text)
    activity_start_date = db.Column(db.DateTime)
    activity_end_date = db.Column(db.DateTime)
    activity_description= db.Column(db.Text)
    activity_url= db.Column(db.Text)
    activity_template= db.Column(db.Text)

    @property
    def serialize(self):
        return dict(
            id=self.id,
            user_id=self.user_id,
            shop_id=self.shop_id,
            activity_name=self.activity_name,
            activity_location=self.activity_location,
            activity_start_date=self.activity_start_date,
            activity_end_date=self.activity_end_date,
            activity_description=self.activity_description,
            activity_url=self.activity_url,
            activity_template=self.activity_template,
            activity_lines=self.serialize_lines
        )

    @property
    def serialize_lines(self):
        return [item.serialize for item in self.lines]

    shop = relation(Shop, backref=backref('activities', order_by=id))


class Line(db.Model):
    __tablename__ = 'lines'

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, ForeignKey('activities.id'))
    customer_id = db.Column(db.Integer, ForeignKey('customers.id'))

    activity = relation(Activity, backref=backref('lines', order_by=id))
    customer = relation(Customer, backref=backref('customers', order_by=id))

    @property
    def serialize(self):
        return dict(
            customer_id=self.customer_id
        )


def init():
    db.create_all()