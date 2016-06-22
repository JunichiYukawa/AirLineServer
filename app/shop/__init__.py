from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask_login import current_user
import logging

app = Flask(__name__)
app.config.from_object('shop.config')

app.logger.setLevel(logging.DEBUG)

db = SQLAlchemy(app)

auth = HTTPBasicAuth()

import shop.views
