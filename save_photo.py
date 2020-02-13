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


def save_photo_for_post(post):

    for count, attach in enumerate(post['attachments']):
        try:
            path = 'Photo_rar/photo' + str(attach['photo']['pid']) + '.jpeg'
            img_content = requests.get(attach['photo']['src_big'])

            img_file = open(path, 'wb')
            img_file.write(img_content.content)
            img_file.close()

        except Exception as e:
            print('не смогли сохранить пикчу для поста')
            logging.debug('не смогли сохранить пикчу для поста')
            logging.exception(e)


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
        offset = offset + 100
        if wall_record is None:
            continue
        for record in wall_record[1:]:
            try:
                if record['attachments'][0]['type'] != 'link':
                    save_photo_for_post(record)
            except Exception as e:
                    print('не смогли сохранить пикчу для поста')
                    logging.debug('не смогли сохранить пикчу для поста')
                    logging.exception(e)

        time.sleep(1)


if __name__ == '__main__':
    main()
