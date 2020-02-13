#!/usr/bin/python
# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta
import http.cookiejar as cooki
import json
import logging
import random

import time
import urllib
import urllib.parse
from html.parser import HTMLParser
from urllib import request
from urllib.parse import urlparse

import requests
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from new_bot_wall_post.app.config import w_watermark, b_watermark, akk_for_comment, list_groups, \
    SQLALCHEMY_DATABASE_URI, max_count_post

from new_bot_wall_post.app.models import Hash, Post, FakeUsers, Groups, Comments

logging.basicConfig(filename='bot_log.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y '
                            '%I:%M:%S '
                            '%p')

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)


class FormParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.url = None
        self.params = {}
        self.in_form = False
        self.form_parsed = False
        self.method = "GET"

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "form":
            if self.form_parsed:
                raise RuntimeError("Second form on page")
            if self.in_form:
                raise RuntimeError("Already in form")
            self.in_form = True
        if not self.in_form:
            return
        attrs = dict((name.lower(), value) for name, value in attrs)
        if tag == "form":
            self.url = attrs["action"]
            if "method" in attrs:
                self.method = attrs["method"].upper()
        elif tag == "input" and "type" in attrs and "name" in attrs:
            if attrs["type"] in ["hidden", "text", "password"]:
                self.params[attrs["name"]] = attrs["value"] if "value" in attrs else ""

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "form":
            if not self.in_form:
                raise RuntimeError("Unexpected end of <form>")
            self.in_form = False
            self.form_parsed = True

    def error(self, message):
        pass


def auth(email, password, client_id, scope):
    def split_key_value(kv_pair):
        kv = kv_pair.split("=")
        return kv[0], kv[1]

    # Authorization form
    def auth_user(email, password, client_id, scope, opener):

        response = opener.open(
            'http://oauth.vk.com/oauth/authorize?' +
            'redirect_uri=http://oauth.vk.com/blank.html&response_type=token&' +
            'client_id=%s&scope=%s&display=wap' % (client_id, ",".join(scope))
        )
        html_dock = response.read().decode("utf-8")
        parser = FormParser()
        parser.feed(html_dock)
        parser.close()
        if not parser.form_parsed or parser.url is None or "pass" not in parser.params or "email" not in parser.params:
            raise RuntimeError("Something wrong")
        parser.params["email"] = email
        parser.params["pass"] = password
        if parser.method == "POST":
            response = opener.open(parser.url, urllib.parse.urlencode(parser.params).encode())
        else:
            raise NotImplementedError("Method '%s'" % parser.method)
        return response.read(), response.geturl()

    # Permission request form
    def give_access(html_dock, browser):
        parser = FormParser()
        parser.feed(html_dock.decode("utf-8"))
        parser.close()
        if not parser.form_parsed or parser.url is None:
            raise RuntimeError("Something wrong")
        if parser.method == "POST":
            response = browser.open(parser.url, urllib.parse.urlencode(parser.params).encode())
        else:
            raise NotImplementedError("Method '%s'" % parser.method)
        return response.geturl()

    if not isinstance(scope, list):
        scope = [scope]
    opener = request.build_opener(
        request.HTTPCookieProcessor(cooki.CookieJar()),
        request.HTTPRedirectHandler())
    doc, url = auth_user(email, password, client_id, scope, opener)
    if urlparse(url).path != "/blank.html":
        # Need to give access to requested scope
        url = give_access(doc, opener)
    if urlparse(url).path != "/blank.html":
        raise RuntimeError("Expected success here")
    answer = dict(split_key_value(kv_pair) for kv_pair in urlparse(url).fragment.split("&"))
    if "access_token" not in answer or "user_id" not in answer:
        raise RuntimeError("Missing some values in answer")
    return answer["access_token"], answer["user_id"]


def check_response(response):
    # noinspection PyGlobalUndefined
    global max_count_post
    if response.status_code == 200:
        if 'response' in response.text:
            is_response = True
            code_error = None
            error_msg = None
        else:
            error = json.loads(response.text)['error']
            is_response = False
            code_error = error['error_code']
            error_msg = error['error_msg']
    else:
        is_response = False
        code_error = response.reason
        error_msg = response.reason

    max_count_post = code_error == '214'

    return is_response, code_error, error_msg


def get_response(url, param_return='response'):
    while True:
        try:
            response = requests.get(url)  # verify=False
            break
        except requests.ConnectionError:
            print('нет инета, ребутнем ка роутер')
            logging.debug('нет инета, ребутнем ка роутер')

    is_response, code_error, error_msg = check_response(response)

    if is_response:
        _response = json.loads(response.text)[param_return]
    else:
        print(str(error_msg))
        logging.debug(str(error_msg))
        if error_msg != 'Request-URI Too Large':
            send_message(error_msg, '294143399')
        _response = None

    return _response


def fabric_query(method, params):
    query = "https://api.vk.com/method/" + method + '?'

    for key, value in params.items():
        query += '&' + key + '=' + value

    return query


def img_save(img_conten):
    captcha_file = open('test.jpeg', 'wb')
    captcha_file.write(img_conten)
    captcha_file.close()


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


def send_message(message, id_people, captcha_sid='0', captcha_key='0'):
    method = 'messages.send'
    params = {'user_id': str(id_people), 'message': message, 'access_token': access_token,
              'captcha_sid': captcha_sid, 'captcha_key': captcha_key}

    url = fabric_query(method, params)

    return get_response(url)


def get_user(user_ids):
    method = 'users.get'
    params = {'user_ids': str(user_ids), 'fields': 'sex', 'access_token': access_token}

    url = fabric_query(method, params)

    return get_response(url)


def wall_get(group_id, domain, count='10'):
    method = 'wall.get'
    params = {'owner_id': group_id, 'domain': domain, 'count': count, 'access_token': access_token}

    url = fabric_query(method, params)

    return get_response(url)


def wall_post(group_id, message, attachments):
    message_tag = message + ' |%23баян |%23bayan |%23мемы |%23memes'
    method = 'wall.post'
    params = {'owner_id': '-' + group_id, 'message': message_tag, 'attachments': attachments,
              'from_group': '1', 'access_token': access_token}

    url = fabric_query(method, params)

    post_id = get_response(url)

    if post_id is not None:
        return post_id['post_id']
    else:
        return None


def get_most_like_post(wall_records, group_name):
    # noinspection PyGlobalUndefined
    global now_img_hash, now_post_id

    index_record = []
    for record in wall_records:
        not_only_photo = False
        if type(record) is int:
            continue
        else:
            if 'copy_owner_id' in record:
                continue
            if 'attachments' in record and '/' not in record['text']:
                if record['likes']['count'] >= 500:
                    if record['attachments'].__len__() <= 10:
                        for attach in record['attachments']:
                            if attach['type'] != 'photo':
                                not_only_photo = True
                                break
                        if not_only_photo:
                            print('в этом посте не только фотки')
                            logging.debug('в этом посте не только фотки')
                            continue
                        else:
                            match = None

                            for attach in record['attachments']:
                                try:
                                    img_content = requests.get(attach['photo']['src_big'])
                                    match = find_match(img_content.content, record)
                                    if match is not None:
                                        break
                                except Exception as e:
                                    print('по каким то не понятным причинам не удалось скачать картинку для проверки')
                                    logging.debug('по каким то не понятным причинам не удалось скачать картинку для '
                                                  'проверки')
                                    logging.exception(e)
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
                                logging.debug('по каким то не понятным причинам не удалось скачать картинку для '
                                              'проверки')
                                logging.exception(e)

                                match = None
                            if match is None:
                                index_record.append([record['likes']['count'], record])
                        else:
                            print('в этом посте не только фотки')
                            logging.debug('в этом посте не только фотки')
                else:
                    print('у этого посте всего (' + str(record['likes']['count']) + ') лайков')
                    logging.debug('у этого посте всего (' + str(record['likes']['count']) +
                                  ') лайков')

    index_record.sort(key=lambda x: x[0])

    if index_record.__len__() == 0:
        print('в группе (' + group_name + ') ни чего интересного')
        logging.debug('в группе (' + group_name + ') ни чего интересного')
        _rec = None
    else:
        _rec = index_record[index_record.__len__() - 1]
        _rec[1]['text'] = _rec[1]['text'].replace('<br>', ' ')
        now_img_hash, now_post_id = _rec[1]['img_hash'], _rec[1]['post_id']

    return _rec


def get_upload_server(group_id):
    method = 'photos.getWallUploadServer'
    params = {'group_id': group_id, 'access_token': access_token}

    url = fabric_query(method, params)

    return get_response(url)['upload_url']


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
        msg = 'загрузили фотку'
        print(msg)
        logging.debug(msg)
    else:
        msg = 'эх хуй а не серв (' + check_response(response)[2] + ')'
        print(msg)
        logging.debug(msg)
        send_message(msg, '294143399')
        photo_id = None

    return photo_id


def save_wall_photo(group_id, params):
    method = 'photos.saveWallPhoto'
    params = {'group_id': group_id, 'photo': str(params['photo']), 'server': str(params['server']),
              'hash': str(params['hash']), 'access_token': access_token}

    url = fabric_query(method, params)

    return get_response(url)


def save_photo_for_post(post):
    photos = ''

    count = 0
    if 'attachments' in post[1]:
        for attach in post[1]['attachments']:
            count += 1
            try:
                path = 'photo_for_post/photo' + str(count) + '.jpeg'
                img_content = requests.get(attach['photo']['src_big'])

                img_file = open(path, 'wb')
                img_file.write(img_content.content)
                img_file.close()

                add_watermark(Image.open(path), path)

                photos += path
                if count < post[1]['attachments'].__len__():
                    photos += ','
            except Exception as e:
                print('не смогли сохранить пикчу для поста')
                logging.debug('не смогли сохранить пикчу для поста')
                logging.exception(e)

    return photos


def material_for_post(photos_path, upload_server):
    attachments = ''
    photos = []

    list_of_path = list(photos_path.split(','))
    for path in list_of_path:
        params_for_save = upload_photo_server(upload_server, path)
        photos.append(save_wall_photo('134916088', params_for_save))

    count = 0
    if photos.__len__() > 0:
        for photo in photos:
            count += 1
            attachments += photo[0]['id']
            if count < photos.__len__():
                attachments += ','

    return attachments


def find_match(img_content, post):
    size = 8, 8
    _hash = ''
    # match = find_match_in_base(str(post['id']) + str(post['from_id']), base_id)

    match = None
    session = Session()
    for id_post, in session.query(Post.id_post).filter(Post.id_post == str(post['id']) + str(post['from_id'])):
        match = id_post

    if match is None:
        img_save(img_content)

        image = Image.open("test.jpeg")  # Открываем изображение.
        image = image.resize(size, Image.BILINEAR)

        _hash = get_hash(image)

        del image

        if _hash is None:
            return 1

        # match = find_match_in_base(_hash, base, True)

        session = Session()
        for any_hash, in session.query(Hash.hash).filter(Hash.hash == _hash):
            match = any_hash

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
            print('а вот хуй его знает почему картинку не запостили')
            logging.debug('а вот хуй его знает почему картинку не запостили')
            logging.exception(e)
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


# comments


def comment_get(group_id, post_id):
    method = 'wall.getComments'
    params = {'owner_id': group_id, 'post_id': str(post_id), 'need_likes': '1',
              'count': str(random.randrange(20, 100)), 'access_token': access_token}

    url = fabric_query(method, params)

    return get_response(url)


def create_comment(owner_id, post_id, message, reply_to_comment, attachments, access_token_for_comment):
    method = 'wall.createComment'
    params = {'owner_id': '-' + str(owner_id), 'post_id': str(post_id), 'message': message,
              'count': '50', 'access_token': access_token_for_comment}

    if reply_to_comment is not None:
        params.update({'reply_to_comment': str(reply_to_comment)})

    if attachments is not None:
        params.update({'attachments': str(attachments)})

    url = fabric_query(method, params)

    return get_response(url)


def build_structure_comments(comments):
    mapping = [['1', '1']]

    for comment in comments:
        searched = False
        if isinstance(comment, dict):
            if '/' not in comment['text']:
                for old_id in mapping:
                    if old_id[0] == str(comment['from_id']):
                        comment['from_id'] = old_id[1]
                        searched = True

                if searched is False:
                    # new_id = akk_for_comment[random.randrange(0, akk_for_comment.__len__())]['id'] choice
                    new_id = random.choice(akk_for_comment)['id']
                    mapping.append([str(comment['from_id']), new_id])
                    comment['from_id'] = new_id

            else:
                comments.remove(comment)
                break

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
                                        break

                            text_split = text_split.replace('<br>', '\n')
                            comment['text'] = text_split

                            if comment['from_id'] == comment_for_search['from_id']:
                                comment['from_id'], mapping = new_id_func(comment['from_id'], mapping)
                            break
            else:
                comment['text'] = comment['text'].replace('<br>', '\n')

    return comments


def new_id_func(old_id_str, mapping):
    # new_id_str = akk_for_comment[random.randrange(0, akk_for_comment.__len__())]['id']
    new_id_str = random.choice(akk_for_comment)['id']
    if old_id_str == new_id_str:
        new_id_str, mapping = new_id_func(old_id_str, mapping)
    else:
        mapping.append([old_id_str, new_id_str])

    return new_id_str, mapping


def create_life(structure_comments, post_id, owner_id, group_id, domain):
    if structure_comments.__len__() > 1:
        session = Session()
        for comment in structure_comments:
            if isinstance(comment, dict):
                for akk in akk_for_comment:
                    if comment['from_id'] == akk['id']:
                        if 'reply_to_cid' in comment:
                            for created_comment in structure_comments:
                                if isinstance(created_comment, dict):
                                    if created_comment['cid'] == comment['reply_to_cid']:
                                        comment_reply = create_comment(owner_id, post_id, comment['text'],
                                                                       created_comment['new_cid'],
                                                                       comment['attachments'] if
                                                                       'attachments' in comment else None,
                                                                       akk['token'])
                                        if comment_reply is not None:
                                            comment['new_cid'] = str(comment_reply['cid'])
                                        else:
                                            comment['new_cid'] = ''
                                        break
                        else:
                            comment_reply = create_comment(owner_id, post_id, comment['text'],
                                                           None,
                                                           comment['attachments'] if 'attachments' in comment else None,
                                                           akk['token'])
                            if comment_reply is not None:
                                comment['new_cid'] = str(comment_reply['cid'])
                            else:
                                comment['new_cid'] = ''

                        if 'new_cid' not in comment:
                            comment['new_cid'] = ''

                        utcnow = datetime.utcnow()
                        session.add(Comments(body=comment['text'],
                                             timestamp=utcnow + timedelta(seconds=1),
                                             id_group=group_id,
                                             domain=domain))
                        print('Коментнул пост ' + str(akk['id']))
                        logging.debug('Коментнул пост ' + str(akk['id']))
                        time.sleep(random.randrange(10, 25))
                        break

        session.commit()

    else:
        print('У поста нет комментов')
        logging.debug('У поста нет комментов')


# comments

def init_var():
    session = Session()
    fake_users_ = session.query(FakeUsers).all()
    for fake in fake_users_:
        user = get_user(fake.id_fake_user)
        if 'deactivated' not in user[0]:
            access_token_for_comment, user_id_for_comment = auth(fake.login_fake_user, fake.pass_fake_user, "4826374",
                                                                 'audio,groups,friends,photos,wall,'
                                                                 'notify,messages')

            akk_for_comment.append({'id': fake.id_fake_user, 'login': fake.login_fake_user, 'pass': fake.pass_fake_user,
                                    'name': fake.name_fake_user, 'token': access_token_for_comment, 'active': True})

        session.query(FakeUsers).filter_by(id=fake.id).update({"active": 'deactivated' not in user[0],
                                                               "sex": user[0]['sex']})

    session.commit()

    groups_ = session.query(Groups).all()
    for group in groups_:
        list_groups.append([group.id_group, group.short_name])


def main():
    # noinspection PyGlobalUndefined
    global access_token, user_id, max_count_post

    while True:
        access_token, user_id = auth('+79227343940', "uchkuduktrikolodca2016", "4826374",
                                     'audio,groups,friends,photos,wall,notify,messages')
        if access_token != '':
            break

    init_var()

    while True:

        for group_id, domain in list_groups:
            wall_record = wall_get(group_id, domain)
            post = get_most_like_post(wall_record, domain)
            if post is None:
                continue
            else:
                upload_server = get_upload_server('134916088')
                if upload_server is None:
                    continue
                else:
                    photos_path = save_photo_for_post(post)
                    attachments = material_for_post(photos_path, upload_server)
                    posted_id = wall_post('134916088', post[1]['text'], attachments)

                    time_to_last_post = datetime.now().minute
                    if posted_id is not None:
                        """add_hash_in_base(now_post_id, base_id)
                        add_hash_in_base(now_img_hash, base)
                        save_base()"""
                        utcnow = datetime.utcnow()
                        session = Session()
                        session.add_all([Post(id_post=now_post_id,
                                              timestamp=utcnow + timedelta(seconds=1),
                                              time=datetime.time(datetime.now()),
                                              id_group=domain),
                                         Hash(hash=now_img_hash,
                                              timestamp=utcnow + timedelta(seconds=1))])
                        session.commit()

                        comments = comment_get(group_id, post[1]['id'], )
                        structure_comments = build_structure_comments(comments)
                        create_life(structure_comments, posted_id, '134916088', group_id, domain)

                        time_to_sleep = 25 - (datetime.now().minute - time_to_last_post)
                        logging.debug('25 - (' + str(datetime.now().minute) + '-' + str(time_to_last_post) + ')')
                        print('между постами рекомендуется выдержать время, в среднем ' + str(time_to_sleep) + ' минут')
                        logging.debug('между постами рекомендуется выдержать время, в среднем ' + str(time_to_sleep)
                                      + ' минут')
                        print(datetime.now())
                        if time_to_sleep > 0:
                            time.sleep(time_to_sleep * 60)


main()


# TODO: еще раз прорефакторить код
# TODO: добавить возможность постить просто текст
# TODO: сохранять похожие в папку
# TODO: все запросы к апи повторять
# TODO: научить определять области темные/светлые для ватермарка
# TODO: вызов реквеста в рекурсии
# TODO: все обращения к api vk сделать классом с **kwargs
# TODO: запись статистики в базу
# TODO: комментаторов разделить по гендерному признаку
