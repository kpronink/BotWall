#!/usr/bin/python
# -*- coding: UTF-8 -*-
from new_bot_wall_post.app.config import id_owner_group
import datetime
import calendar
from new_bot_wall_post.vk import SessionVk, VkApi, auth
from new_bot_wall_post.app.models import Stats, StatsAge, StatsCities, StatsCountries, StatsSex, StatsSexAge, Post

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from new_bot_wall_post.app.config import SQLALCHEMY_DATABASE_URI

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)

session_vk = SessionVk()
vk_api = VkApi(session_vk)

while True:
    access_token, user_id = auth('+79227343940', "uchkuduktrikolodca2016", "4826374",
                                 'audio,groups,friends,photos,wall,notify,messages,stats')
    if access_token != '':
        break

stats = vk_api.stats.get(group_id=id_owner_group, date_from='2015-01-01', date_to='2020-01-01',
                         access_token=access_token)
session = Session()
for d in stats[::-1]:

    session.query(Stats).filter_by(day=d['day']).update({"subscribed": d['subscribed'],
                                                         "unsubscribed": d['unsubscribed'],
                                                         "views": d['views'],
                                                         "visitors": d['visitors'],
                                                         "reach_subscribers": d['reach_subscribers'],
                                                         "reach": d['reach'],
                                                         "day": d['day']})
    for age in d['age']:
        stats_age_in_db = session.query(StatsAge).filter_by(day=d['day']).all()
        if stats_age_in_db:
            session.query(StatsAge).filter_by(day=d['day']).update({"value": age['value'],
                                                                    "visitors": age['visitors'],
                                                                    "day": d['day']})
        else:
            session.add_all([StatsAge(value=age['value'],
                                      visitors=age['visitors'],
                                      day=d['day'])])

    for cities in d['cities']:
        stats_cities_in_db = session.query(StatsCities).filter_by(day=d['day']).all()
        if stats_cities_in_db:
            session.query(StatsCities).filter_by(day=d['day']).update({"name": cities['name'],
                                                                       "value": cities['value'],
                                                                       "visitors": cities['visitors'],
                                                                       "day": d['day']})
        else:
            session.add_all([StatsCities(name=cities['name'],
                                         value=cities['value'],
                                         visitors=cities['visitors'],
                                         day=d['day'])])

    for countries in d['countries']:
        stats_countries_in_db = session.query(StatsCountries).filter_by(day=d['day']).all()
        if stats_countries_in_db:
            session.query(StatsCountries).filter_by(day=d['day']).update({"name": countries['name'],
                                                                          "code": countries['code'],
                                                                          "value": countries['value'],
                                                                          "visitors": countries['visitors'],
                                                                          "day": d['day']})
        else:
            session.add_all([StatsCountries(name=countries['name'],
                                            code=countries['code'],
                                            value=countries['value'],
                                            visitors=countries['visitors'],
                                            day=d['day'])])

    for sex in d['sex']:
        stats_sex_in_db = session.query(StatsSex).filter_by(day=d['day']).all()
        if stats_sex_in_db:
            session.query(StatsSex).filter_by(day=d['day']).update({"value": sex['value'],
                                                                    "visitors": sex['visitors'],
                                                                    "day": d['day']})
        else:
            session.add_all([StatsSex(value=sex['value'],
                                      visitors=sex['visitors'],
                                      day=d['day'])])

    for sex_age in d['sex_age']:
        stats_sex_age_in_db = session.query(StatsSexAge).filter_by(day=d['day']).all()
        if stats_sex_age_in_db:
            session.query(StatsSexAge).filter_by(day=d['day']).update({"value": sex_age['value'],
                                                                       "visitors": sex_age['visitors'],
                                                                       "day": d['day']})
        else:
            session.add_all([StatsSexAge(value=sex['value'],
                                         visitors=sex['visitors'],
                                         day=d['day'])])

    session.commit()
