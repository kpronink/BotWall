#!/usr/bin/python
# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta

import json
import random

import time
import urllib
import urllib.parse

import requests
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# import streamlit as st

from app.config import w_watermark, b_watermark, akk_for_comment, list_groups, \
    SQLALCHEMY_DATABASE_URI, max_count_post, hash_list, id_owner_group, id_user_debug

import vk as vk

from app.models import Hash, Post, FakeUsers, Groups, Comments, StatsSexAge, Stats, StatsSex, \
    StatsCountries, StatsCities, StatsAge

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)

session_vk = vk.SessionVk()
vk_api = vk.VkApi(session_vk)


def add_watermark(image, path):
    count_dark = 0

    for y in range(27):
        for x in range(92):
            rgb = image.getpixel((x, y))
            if rgb[0] < 127 or rgb[1] < 127 or rgb[2] < 127:
                count_dark += 1

    if count_dark < 900:
        watermark = b_watermark
    else:
        watermark = w_watermark

    layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    layer.paste(watermark, (2, 2))

    Image.composite(layer, image, layer).save(path)


def get_most_like_post(wall_records, group_name):
    # noinspection PyGlobalUndefined
    global now_img_hash, now_post_id

    index_record = []
    for record in wall_records['items'][1:]:
        not_only_photo = False
        if 'copy_owner_id' in record:
            continue
        if 'attachments' in record and '/' not in record['text'] and record['marked_as_ads'] == 0:
            if record['likes']['count'] >= 100:
                if record['attachments'].__len__() <= 10:
                    for attach in record['attachments']:
                        if attach['type'] != 'photo':
                            not_only_photo = True
                            break
                    if not_only_photo:
                        print('в этом посте не только фотки')
                        continue
                    else:
                        match = None

                        for attach in record['attachments']:
                            try:
                                img_content = requests.get(attach['photo']['sizes'][-1:][0]['url'])
                                match = find_match(img_content.content, record)
                                if match is not None:
                                    break
                            except Exception as e:
                                print('по каким то не понятным причинам не удалось скачать картинку для проверки')
                                match = None
                        if match is None:
                            index_record.append([record['likes']['count'], record])
                else:
                    if record['attachments'][0]['type'] == 'photo':

                        try:
                            img_content = requests.get(record['attachments'][0]['photo']['src_big'])
                            match = find_match(img_content.content, record)
                        except Exception as e:
                            print('по каким то не понятным причинам не удалось скачать картинку для проверки')

                            match = None
                        if match is None:
                            index_record.append([record['likes']['count'], record])
                    else:
                        print('в этом посте не только фотки')
            else:
                print('у этого посте всего (' + str(record['likes']['count']) + ') лайков')

    index_record.sort(key=lambda x: x[0])

    if index_record.__len__() == 0:
        print('в группе (' + group_name + ') ни чего интересного')
        _rec = None
    else:
        _rec = index_record[index_record.__len__() - 1]
        _rec[1]['text'] = _rec[1]['text'].replace('<br>', ' ')
        now_img_hash, now_post_id = _rec[1]['img_hash'], _rec[1]['post_id']

    return _rec


def upload_photo_server(url_server, photo):
    data = {}
    files = {'photo': (photo.split('/')[1], open(photo, 'rb'))}
    url = url_server.split('?')[0]
    for key, value in urllib.parse.parse_qs(url_server.split('?')[1]).items():
        data[key] = value[0]

    url = url.replace('vkontakte.ru', 'vk.com')
    response = requests.post(url, data, files=files)

    if response.status_code == 200:
        photo_id = json.loads(response.text)
    else:
        vk_api.messages.send(user_id=id_user_debug, message='эх хуй а не серв', access_token=access_token,
                             v='5.95')
        photo_id = None

    return photo_id


def save_photo_for_post(post):
    photos = ''

    for count, attach in enumerate(post[1]['attachments']):
        try:
            path = 'photo_for_post/photo' + str(count) + '.jpeg'
            img_content = requests.get(attach['photo']['sizes'][-1:][0]['url'])

            img_file = open(path, 'wb')
            img_file.write(img_content.content)
            img_file.close()

            add_watermark(Image.open(path), path)

            photos += path
            if count < post[1]['attachments'].__len__() - 1:
                photos += ','
        except Exception as e:
            print('не смогли сохранить пикчу для поста')

    return photos


def material_for_post(photos_path, upload_server):
    attachments = ''
    photos = []

    list_of_path = list(photos_path.split(','))
    for path in list_of_path:
        params = upload_photo_server(upload_server, path)
        while True:
            time.sleep(2)
            attach = vk_api.photos.saveWallPhoto(group_id=id_owner_group, photo=str(params['photo']),
                                                 server=str(params['server']),
                                                 hash=str(params['hash']), access_token=access_token,
                                                 v='5.95')
            # vk_api.messages.send(user_id='326786278', message='воизбежания флуда',
            #                      access_token=access_token, v='5.95')
            if attach is not None:
                photos.append(attach)
                break

    for count, photo in enumerate(photos):
        if photo is None:
            continue
        attachments += 'photo' + str(photo[0]['owner_id']) + '_' + str(photo[0]['id'])
        if count < photos.__len__() - 1:
            attachments += ','

    return attachments


def distance(a, b):
    """вычисление расстояния Левенштейна между a и b"""
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a, b = b, a
        n, m = m, n

    current_row = range(n + 1)  # Keep current and previous row, not entire matrix
    for i in range(1, m + 1):
        previous_row, current_row = current_row, [i] + [0] * n
        for j in range(1, n + 1):
            add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
            # noinspection PyUnresolvedReferences
            if a[j - 1] != b[i - 1]:
                change += 1
            current_row[j] = min(add, delete, change)

    return current_row[n]


def find_match(img_content, post):
    # noinspection PyGlobalUndefined
    global hash_list
    size = 8, 8
    _hash = ''
    content = img_content

    match = None
    session = Session()
    for id_post, in session.query(Post.id_post).filter(Post.id_post == str(post['id']) + str(post['from_id'])):
        match = id_post

    if match is None:
        with open('test.jpeg', 'wb') as out_file:
            out_file.write(content)

        image = Image.open("test.jpeg")  # Открываем изображение.
        image = image.resize(size, Image.BILINEAR)

        _hash = get_hash(image)

        del image

        if _hash is None:
            return 1

        for h in hash_list:
            if isinstance(h.hash, str):
                current_row = distance(h.hash, _hash)
                if current_row <= 1:
                    match = 1
                    print(h.hash + ' - ' + _hash + ' ' + str(current_row))
                    break

    post['post_id'] = str(post['id']) + str(post['from_id'])
    post['img_hash'] = _hash

    return match


def base_convert(number, from_base, to_base):  # процедура для конвертации в шеснадцетиричную систему
    try:
        # Convert number to base 10
        base10 = int(number, from_base)
    except ValueError:
        raise

    if to_base < 2 or to_base > 36:
        raise NotImplementedError

    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    sign = ''

    if base10 == 0:
        return '0'
    elif base10 < 0:
        sign = '-'
        base10 = -base10

    s = ''
    while base10 != 0:
        r = base10 % to_base
        r = int(r)
        s = digits[r] + s
        base10 //= to_base

    output_value = sign + s
    return output_value


def get_hash(img):  # перцептивный хэш

    sum_pix_color = 0
    for x in img.getdata():
        try:
            sum_pix_color += sum(list(x))
        except Exception as e:
            return None

    sred = sum_pix_color / 64

    str_hash = ''

    for x in img.getdata():
        if sum(list(x)) >= sred:
            str_hash += '1'
        else:
            str_hash += '0'

    _hash = base_convert(str_hash, 2, 16)

    return _hash


def build_structure_comments(comments):
    mapping = [['1', '1']]
    previous = ''

    for comment in comments:
        searched = False
        if not isinstance(comment, dict):
            continue
        if '/' in comment['text']:
            comments.remove(comment)
            break
        for old_id in mapping:
            if old_id[0] == str(comment['from_id']):
                comment['from_id'] = old_id[1]
                searched = True

        if searched is False:
            new_id = random.choice(akk_for_comment)['id']
            if new_id == previous:
                new_id = random.choice(akk_for_comment)['id']
            mapping.append([str(comment['from_id']), new_id])
            comment['from_id'] = new_id
            previous = new_id

        if 'reply_to_cid' in comment:
            for comment_for_search in comments:
                if isinstance(comment_for_search, dict):
                    if comment['reply_to_cid'] == comment_for_search['cid']:
                        text_split = comment['text']
                        text_split = text_split.replace('[id' + str(comment['reply_to_uid']) + '|',
                                                        '[id' + comment_for_search['from_id'] + '|')
                        massive = text_split.split('|')
                        if massive.__len__() > 1:
                            massive_name = massive[1].split('}')

                            for akk in akk_for_comment:
                                if comment_for_search['from_id'] == akk['id']:
                                    text_split = text_split.replace(massive_name[0], akk['name'])
                                    text_split += (']' + massive_name[0].split(']')[1])
                                    comment['clen_text'] = massive_name[0].split(']')[1]
                                    break

                        text_split = text_split.replace('<br>', '\n')
                        comment['text'] = text_split

                        if comment['from_id'] == comment_for_search['from_id']:
                            comment['from_id'], mapping = new_id_func(comment['from_id'], mapping)
                        break
        else:
            comment['text'] = comment['text'].replace('<br>', '\n')
            comment['clen_text'] = comment['text'].replace('<br>', '\n')

    return comments


def new_id_func(old_id_str, mapping):
    new_id_str = random.choice(akk_for_comment)['id']
    if old_id_str == new_id_str:
        new_id_str, mapping = new_id_func(old_id_str, mapping)
    else:
        mapping.append([old_id_str, new_id_str])

    return new_id_str, mapping


def create_life(structure_comments, post_id, owner_id, group_id, domain):
    if structure_comments.__len__() > 1:
        session = Session()
        time.sleep(random.randrange(10, 25))
        for comment in structure_comments:
            if isinstance(comment, dict):
                for akk in akk_for_comment:
                    if comment['from_id'] == akk['id']:
                        if 'reply_to_cid' in comment:
                            for created_comment in structure_comments:
                                if isinstance(created_comment, dict):
                                    if created_comment['cid'] == comment['reply_to_cid']:

                                        comment_reply = vk_api.wall.createComment(owner_id='-' + str(owner_id),
                                                                                  reply_to_comment=created_comment[
                                                                                      'new_cid'],
                                                                                  post_id=str(post_id),
                                                                                  message=comment['text'], count='50',
                                                                                  access_token=akk['token'],
                                                                                  v='5.95')
                                        if comment_reply is not None:
                                            comment['new_cid'] = str(comment_reply['cid'])
                                        else:
                                            comment['new_cid'] = ''
                                        break
                        else:
                            comment_reply = vk_api.wall.createComment(owner_id='-' + str(owner_id),
                                                                      post_id=str(post_id),
                                                                      message=comment['text'], count='50',
                                                                      access_token=akk['token'],
                                                                      v='5.95')

                            if comment_reply is not None:
                                comment['new_cid'] = str(comment_reply['cid'])
                            else:
                                comment['new_cid'] = ''

                        if 'new_cid' not in comment:
                            comment['new_cid'] = ''

                        if 'clen_text' in comment:
                            if akk['id'] != '326786278':
                                vk_api.messages.send(user_id='326786278', message=comment['clen_text'],
                                                     access_token=akk['token'], v='5.95')

                        utcnow = datetime.utcnow()
                        session.add(Comments(body=comment['text'],
                                             timestamp=utcnow + timedelta(seconds=1),
                                             id_group=group_id,
                                             domain=domain))
                        print('Коментнул пост ' + str(akk['id']))

                        time.sleep(random.randrange(10, 25))
                        break

        session.commit()

    else:
        print('У поста нет комментов')


def init_var():
    global hash_list
    session = Session()

    groups_ = session.query(Groups).all()
    for group in groups_:
        list_groups.append([group.id_group, group.short_name])

    hash_list = session.query(Hash).all()


def main():
    # noinspection PyGlobalUndefined
    global access_token, user_id, max_count_post

    while True:
        access_token, user_id = vk.auth('+79123260552', "GiveMeUsaTank1337", "4826374",
                                        'audio,groups,friends,photos,wall,notify,messages,stats, offline')
        if access_token != '':
            break

    init_var()
    #  update_stats()

    while True:

        for group_id, domain in list_groups:
            wall_record = vk_api.wall.get(owner_id=group_id, domain=domain, count='10', access_token=access_token
                                          , v='5.95')
            time.sleep(1)
            if wall_record is None:
                continue
            post = get_most_like_post(wall_record, domain)
            time.sleep(1)
            if post is None:
                continue
            else:
                upload_server = vk_api.photos.getWallUploadServer(group_id=id_owner_group, domain=domain,
                                                                  access_token=access_token, v='5.95')
                time.sleep(1)
                if upload_server is None:
                    continue
                else:
                    photos_path = save_photo_for_post(post)
                    time.sleep(1)
                    attachments = material_for_post(photos_path, upload_server['upload_url'])
                    time.sleep(1)
                    if attachments is '':
                        continue

                    try:
                        posted_id = vk_api.wall.post(owner_id='-' + id_owner_group,
                                                     message=post[1]['text'] + ' |%23баян |%23bayan |%23мемы |%23memes',
                                                     attachments=attachments, from_group='1',
                                                     access_token=access_token,
                                                     v='5.95')['post_id']
                        time.sleep(1)
                    except Exception as e:
                        posted_id = None

                    time_to_last_post = datetime.now()
                    if posted_id is not None:
                        utcnow = datetime.utcnow()
                        session = Session()
                        session.add_all([Post(id_post=now_post_id,
                                              timestamp=utcnow + timedelta(seconds=1),
                                              time=datetime.time(datetime.now()),
                                              id_group=domain),
                                         Hash(hash=now_img_hash,
                                              timestamp=utcnow + timedelta(seconds=1))])
                        session.commit()

                        hash_list.append(Hash(hash=now_img_hash, timestamp=utcnow + timedelta(seconds=1)))

                        """
                        comments = vk_api.wall.getComments(owner_id=str(group_id), post_id=str(post[1]['id']),
                                                           count=str(random.randrange(20, 100)),
                                                           need_likes='1', access_token=access_token, v='5.95')
                        """
                        # поставить лайк под постом
                        for akk in akk_for_comment:
                            todo = random.randint(0, 1)
                            if todo:
                                liked = vk_api.likes.add(owner_id='-' + id_owner_group, item_id=str(posted_id),
                                                         type='post', access_token=akk['token'], v='5.95')
                                print(liked)

                        # if comments is not None:
                        #     structure_comments = build_structure_comments(comments)
                        #     time.sleep(1)
                        #     create_life(structure_comments, str(posted_id), id_owner_group, str(group_id), domain)
                        #     time.sleep(1)

                        time_to_sleep = 60 - ((datetime.now() - time_to_last_post).seconds / 60)

                        print('между постами рекомендуется выдержать время, в среднем ' + str(time_to_sleep) + ' минут')
                        print(datetime.now())
                        if time_to_sleep > 0:
                            time.sleep(time_to_sleep * 60)


if __name__ == '__main__':
    main()

# TODO: еще раз прорефакторить код + +
# TODO: добавить возможность постить просто текст
# TODO: сохранять похожие в папку
# TODO: все запросы к апи повторять?

# TODO: попробовать вызывать сессию один раз, или удалять ее после вызова?
# TODO: как/зачем код/комментарий
