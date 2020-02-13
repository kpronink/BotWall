from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String, Time, Boolean, Enum

from sqlalchemy.ext.declarative import declarative_base

from app.config import SQLALCHEMY_DATABASE_URI

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
Base = declarative_base()


class Post(Base):
    __tablename__ = "Post"

    id = Column(Integer, primary_key=True)
    id_post = Column(String)
    timestamp = Column(Date)
    time = Column(Time)
    id_group = Column(String)

    def __init__(self, id_post, id_group, timestamp, time):
        self.id_post = id_post
        self.timestamp = timestamp
        self.time = time
        self.id_group = id_group


class Comments(Base):
    __tablename__ = "Comments"

    id = Column(Integer, primary_key=True)
    body = Column(String)
    timestamp = Column(Date)
    id_group = Column(String)
    domain = Column(String)

    def __init__(self, body, id_group, timestamp, domain):
        self.body = body
        self.timestamp = timestamp
        self.id_group = id_group
        self.domain = domain


class Hash(Base):
    __tablename__ = "Hash"

    id = Column(Integer, primary_key=True)
    hash = Column(String)
    timestamp = Column(Date)

    def __init__(self, hash, timestamp):
        self.hash = hash
        self.timestamp = timestamp


class Groups(Base):
    __tablename__ = "Groups"

    id = Column(Integer, primary_key=True)
    id_group = Column(String)
    short_name = Column(String)

    def __init__(self, id_group, short_name):
        self.id_group = id_group
        self.short_name = short_name


class FakeUsers(Base):
    __tablename__ = "FakeUsers"

    id = Column(Integer, primary_key=True)
    id_fake_user = Column(String)
    login_fake_user = Column(String)
    pass_fake_user = Column(String)
    name_fake_user = Column(String)
    active = Column(Boolean)
    token = Column(String)
    sex = Column(Integer)

    def __init__(self, id_fake_user, login_fake_user, pass_fake_user, name_fake_user, active, token, sex):
        self.id_fake_user = id_fake_user
        self.login_fake_user = login_fake_user
        self.pass_fake_user = pass_fake_user
        self.name_fake_user = name_fake_user
        self.active = active
        self.token = token
        self.sex = sex

    def __repr__(self):
        return self


class User(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True)
    nickname = Column(String(64), index=True, unique=True)
    email = Column(String(120), index=True, unique=True)
    password = Column(String(120), index=True, unique=True)

    # Flask-Login integration
    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():  # line 37
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __repr__(self):
        return '<User %r>' % self.nickname


class Stats(Base):
    __tablename__ = "Stats"

    id = Column(Integer, primary_key=True)
    subscribed = Column(Integer)
    unsubscribed = Column(Integer)
    views = Column(Integer)
    visitors = Column(Integer)
    reach_subscribers = Column(Integer)
    reach = Column(Integer)
    day = Column(String)

    def __init__(self, subscribed, unsubscribed, views, visitors, reach_subscribers, reach, day):
        self.subscribed = subscribed
        self.unsubscribed = unsubscribed
        self.views = views
        self.visitors = visitors
        self.reach_subscribers = reach_subscribers
        self.reach = reach
        self.day = day


class StatsAge(Base):
    __tablename__ = "StatsAge"

    id = Column(Integer, primary_key=True)
    value = Column(String)
    visitors = Column(Integer)
    day = Column(String)

    def __init__(self, value, visitors, day):
        self.value = value
        self.visitors = visitors
        self.day = day


class StatsCities(Base):
    __tablename__ = "StatsCities"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(String)
    visitors = Column(Integer)
    day = Column(String)

    def __init__(self, name, value, visitors, day):
        self.name = name
        self.value = value
        self.visitors = visitors
        self.day = day


class StatsCountries(Base):
    __tablename__ = "StatsCountries"

    id = Column(Integer, primary_key=True)
    code = Column(String)
    name = Column(String)
    value = Column(String)
    visitors = Column(Integer)
    day = Column(String)

    def __init__(self, code, name, value, visitors, day):
        self.code = code
        self.name = name
        self.value = value
        self.visitors = visitors
        self.day = day


class StatsSex(Base):
    __tablename__ = "StatsSex"

    id = Column(Integer, primary_key=True)
    value = Column(String)
    visitors = Column(Integer)
    day = Column(String)

    def __init__(self, value, visitors, day):
        self.value = value
        self.visitors = visitors
        self.day = day


class StatsSexAge(Base):
    __tablename__ = "StatsSexAge"

    id = Column(Integer, primary_key=True)
    value = Column(String)
    visitors = Column(Integer)
    day = Column(String)

    def __init__(self, value, visitors, day):
        self.value = value
        self.visitors = visitors
        self.day = day

