import os
from PIL import Image


now_post_id = ''
now_img_hash = ''

max_count_post = False
session_vk = None
vk_api = None

akk_for_comment = []
list_groups = []
hash_list = []

id_owner_group = '103147642'
id_user_debug = '294143399'

w_watermark = Image.open('watermark_w.png')
b_watermark = Image.open('watermark_b.png')

basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

STRING_TYPES = (str, bytes, bytearray)

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'bot_wall_post.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False
