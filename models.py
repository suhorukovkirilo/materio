from app import database
from sqlalchemy.ext.mutable import MutableList
from flask_login import UserMixin
from datetime import datetime, timedelta

class User(UserMixin, database.Model):
    id = database.Column(database.Integer(), primary_key=True)
    name = database.Column(database.String(25), nullable=False, unique=True)
    email = database.Column(database.String(), nullable=False, unique=True)
    email_confirm = database.Column(database.Boolean(), default=False)
    password = database.Column(database.String(), nullable=False)
    join_date = database.Column(database.String(), default=datetime.today().strftime("%d/%m/%Y"))
    plan = database.Column(database.String(), default="free")
    followers = database.Column(database.String(), default="")
    favourites = database.Column(database.String(), default="")
    reposts = database.Column(database.String(), default="")
    page = database.Column(database.String(10000), default="")
    telegram = database.Column(database.String(), default="")

    def __repr__(self):
        return '<User %r>' % self.id
class Article(database.Model):
    id = database.Column(database.Integer(), primary_key=True)
    title = database.Column(database.String(), nullable=False)
    short = database.Column(database.String(), nullable=False)
    text = database.Column(database.String(), nullable=False)
    public = database.Column(database.Boolean(), default=False)
    date = database.Column(database.DateTime(), default=datetime.utcnow)
    author = database.Column(database.Integer(), nullable=False)
    tags = database.Column(database.String(), default="")
    replies = database.Column(MutableList.as_mutable(database.JSON))
    likes = database.Column(database.String(), default="")

    def __repr__(self):
        return '<Article %r>' % self.id
class OTP(database.Model):
    id = database.Column(database.Integer(), primary_key=True)
    user = database.Column(database.Integer())
    code = database.Column(database.Integer())
    time = database.Column(database.DateTime(), default=datetime.utcnow() + timedelta(minutes=5))
    type = database.Column(database.String(), default="email_verify")

    def __repr__(self):
        return '<OTP %r>' % self.id

