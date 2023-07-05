from flask import Flask
import config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

db = SQLAlchemy()
db.init_app(app)
app.config['UPLOAD_FOLDER'] = config.BaseConfig.UPLOAD_FOLDER
if not os.path.exists(os.getcwd() + app.config['UPLOAD_FOLDER']):
    os.mkdir(os.getcwd() + app.config['UPLOAD_FOLDER'])
migrate = Migrate(app, db)

from . import api