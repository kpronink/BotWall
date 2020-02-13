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
    Column('active', Boolean),
    Column('token', String),
    Column('sex', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['FakeUsers'].columns['sex'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['FakeUsers'].columns['sex'].drop()
