from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
Hash = Table('Hash', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('Hash', String),
    Column('timestamp', Date),
)

Post = Table('Post', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('id_post', String),
    Column('timestamp', Date),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['Hash'].create()
    post_meta.tables['Post'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['Hash'].drop()
    post_meta.tables['Post'].drop()
