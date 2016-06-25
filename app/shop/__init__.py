# -*- coding: utf-8 -*-
from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import logging

app = Flask(__name__)
app.config.from_object('shop.config')

app.logger.setLevel(logging.DEBUG)

db = SQLAlchemy(app)

auth = HTTPBasicAuth()

import shop.views
