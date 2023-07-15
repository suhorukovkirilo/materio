from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_recaptcha import ReCaptcha
from random import shuffle

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'materioconfirm@gmail.com'
app.config['MAIL_PASSWORD'] = 'xqsgdgtwiseybuvf'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['RECAPTCHA_ENABLED'] = True
app.config['RECAPTCHA_SITE_KEY'] = '6Len5DAmAAAAAN92u_a_vj7P4d6dw90BkSqYSG-O'
app.config['RECAPTCHA_SECRET_KEY'] = '6Len5DAmAAAAAGzuMI5PSdYSTv276kfNdpiRwWtL'
database = SQLAlchemy(app)
login_manager = LoginManager(app)
mailer = Mail(app)
recaptcha = ReCaptcha(app)
login_manager.login_view = 'login'

symbols = [*list("abcdefghijklmnopqrstuvwsyz"), *list("abcdefghijklmnopqrstuvwsyz".upper()), *list("1234567890")]
shuffle(symbols)
secretcode = "".join(symbols[:20])
app.secret_key = secretcode
