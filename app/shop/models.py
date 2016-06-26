# -*- coding: utf-8 -*-
from shop import db, app
from sqlalchemy.orm import relation, backref
from sqlalchemy import ForeignKey
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

# Datetime形式のDump
def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    elif isinstance(value, basestring):
        return value
    return value.strftime("%Y-%m-%dT%H:%M:%S")


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
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


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
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
        customer = Customer.query.get(data['id'])
        return customer


# 活躍中のActivity
class Activity(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.Text, unique=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'))
    activity_name = db.Column(db.Text)
    activity_location = db.Column(db.Text)
    activity_start_date = db.Column(db.Text)
    activity_end_date = db.Column(db.Text)
    activity_description = db.Column(db.Text)
    activity_url = db.Column(db.Text)
    activity_template = db.Column(db.Text)

    created_date = db.Column(db.Text)
    finished_date = db.Column(db.Text)

    user = relation("User")

    @property
    def serialize(self):
        return dict(
            id=self.id,
            uuid=self.uuid,
            user_id=self.user_id,
            activity_name=self.activity_name,
            activity_location=self.activity_location,
            activity_start_date=dump_datetime(self.activity_start_date),
            activity_end_date=dump_datetime(self.activity_end_date),
            activity_description=self.activity_description,
            activity_url=self.activity_url,
            activity_template=self.activity_template,
            finished_date=self.finished_date,
            created_date=self.created_date,
            activity_lines=self.serialize_lines
        )

    @property
    def serialize_lines(self):
        return [item.serialize for item in self.lines]


class Line(db.Model):
    __tablename__ = 'lines'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.Text, unique=True)
    number = db.Column(db.Integer)
    activity_id = db.Column(db.Integer, ForeignKey('activities.id'))
    customer_id = db.Column(db.Integer, ForeignKey('customers.id'))

    create_date = db.Column(db.Text)
    arrived_date = db.Column(db.Text)
    pass_date = db.Column(db.Text)

    activity = relation(Activity, backref=backref('lines', primaryjoin='Line.activity_id == Activity.id', order_by=number))
    customer = relation(Customer, backref=backref('customer', order_by=id))

    @property
    def serialize(self):
        return dict(
            customer_id=self.customer_id,
            uuid=self.uuid,
            number=self.number,
            create_date=self.create_date,
            arrived_date = self.arrived_date,
            pass_date = self.pass_date
        )


def init():
    db.create_all()