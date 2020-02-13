#!/usr/bin/python
# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta

import json
import logging
import random

import time
import urllib
import urllib.parse

import requests
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from new_bot_wall_post.app.config import w_watermark, b_watermark, akk_for_comment, list_groups, \
    SQLALCHEMY_DATABASE_URI, max_count_post, hash_list, id_owner_group, id_user_debug

import new_bot_wall_post.vk as vk

from new_bot_wall_post.app.models import Hash, Post, FakeUsers, Groups, Comments, StatsSexAge, Stats, StatsSex, \
    StatsCountries, StatsCities, StatsAge

logging.basicConfig(filename='bot_log.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y '
                            '%I:%M:%S '
                            '%p')

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)

session_vk = vk.SessionVk()
vk_api = vk.VkApi(session_vk)


def main():
    # noinspection PyGlobalUndefined
    global access_token, user_id, max_count_post

    while True:
        access_token, user_id = vk.auth('+79123260552', "VasjaSosiChlen229", "4826374",
                                        'audio,groups,friends,photos,wall,notify,messages,stats, offline')
        if access_token != '':
            break

    offset = 0
    while True:

        wall_record = vk_api.wall.get(owner_id='-103147642', domain='bayan_shop', count='100', access_token=access_token,
                                      offset=str(offset),
                                      version='5.80')
        time.sleep(0.1)
        offset = offset + 100
        print(offset)
        if wall_record is None:
            continue
        for record in wall_record[1:]:
            res = vk_api.wall.delete(owner_id='-103147642', post_id=str(record['id']), version='5.80',
                                     access_token=access_token)
            time.sleep(0.1)


if __name__ == '__main__':
    main()
