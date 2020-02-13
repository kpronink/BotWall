from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
Comments = Table('Comments', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String),
    Column('timestamp', Date),
    Column('id_group', String),
)

Post = Table('Post', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('id_post', String),
    Column('timestamp', Date),
    Column('time', Time),
    Column('id_group', String),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['Comments'].create()
    post_meta.tables['Post'].columns['time'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['Comments'].drop()
    post_meta.tables['Post'].columns['time'].drop()
