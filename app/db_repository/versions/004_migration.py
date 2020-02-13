from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
FakeUsers = Table('FakeUsers', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('id_fake_user', String),
    Column('login_fake_user', String),
    Column('pass_fake_user', String),
    Column('name_fake_user', String),
)

Groups = Table('Groups', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('id_group', String),
    Column('short_name', String),
)

Users = Table('Users', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('nickname', String(length=64)),
    Column('email', String(length=120)),
    Column('password', String(length=120)),
)

Hash = Table('Hash', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('Hash', VARCHAR),
    Column('timestamp', DATE),
)

Hash = Table('Hash', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('hash', String),
    Column('timestamp', Date),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['FakeUsers'].create()
    post_meta.tables['Groups'].create()
    post_meta.tables['Users'].create()
    pre_meta.tables['Hash'].columns['Hash'].drop()
    post_meta.tables['Hash'].columns['hash'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['FakeUsers'].drop()
    post_meta.tables['Groups'].drop()
    post_meta.tables['Users'].drop()
    pre_meta.tables['Hash'].columns['Hash'].create()
    post_meta.tables['Hash'].columns['hash'].drop()
