# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask_session import Session
import logging

app = Flask(__name__)
app.config.from_object('shop.config')
app.logger.setLevel(logging.DEBUG)
Session(app)

db = SQLAlchemy(app)

auth = HTTPBasicAuth()

import shop.views
