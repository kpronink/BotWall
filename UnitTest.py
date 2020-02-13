import unittest
from datetime import datetime, timedelta
from new_bot_wall_post.app.models import Groups, FakeUsers
from new_bot_wall_post.app import config
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)

akk_for_comment = [{'id': '328825342', 'login': '+79049703251', 'pass': 'xdevphoto1216'},
                   {'id': '325932532', 'login': '+79090919794', 'pass': 'xdevphoto0916'},
                   {'id': '326786278', 'login': '+79123260552', 'pass': 'xdevphoto0716'},
                   {'id': '325306923', 'login': '+79090919538', 'pass': 'xdevphotomarazm1988'},
                   {'id': '332109076', 'login': '+79514609348', 'pass': 'xdevphoto0816'}]

id_for_comment = [['Амаяк', '328825342'], ['Анастасия', '325932532'], ['Бибоб', '326786278'], ['Lera', '325306923'],
                  ['Ziga', '332109076']]

list_groups = [['-95355317', '4ch_2ch'], ['-36775802', 'onlyorly'], ['-31234561', 'happycement'],
               ['-57590835', 'online.comics'], ['-91050183', 'dayvinchik'],
               ['-45091870', 'darcor'], ['-30022666', 'leprum'], ['-29439161', 'panda.panda'],
               ['-50554618', 'cartwork'],
               ['-35294456', 'stolbn'], ['-460389', 'borsch']]

session = Session()

"""
for akk in akk_for_comment:
    for name in id_for_comment:
        if akk['id'] == name[1]:
            session.add(FakeUsers(id_fake_user=akk['id'], login_fake_user=akk['login'], pass_fake_user=akk['pass'],
                                  name_fake_user=name[0]))
            break


for group in list_groups:
    session.add(Groups(id_group=group[0], short_name=group[1]))


session.commit()


akk_for_comment_ = []
fake_users_ = session.query(FakeUsers).all()
for fake in fake_users_:
    akk_for_comment_.append({'id': fake.id_fake_user, 'login': fake.login_fake_user, 'pass': fake.pass_fake_user,
                            'name': fake.name_fake_user})

print(akk_for_comment_)
"""