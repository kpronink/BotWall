from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
Stats = Table('Stats', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('subscribed', Integer),
    Column('unsubscribed', Integer),
    Column('views', Integer),
    Column('visitors', Integer),
    Column('reach_subscribers', Integer),
    Column('reach', Integer),
    Column('day', String),
)

StatsAge = Table('StatsAge', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('value', String),
    Column('visitors', Integer),
    Column('day', String),
)

StatsCities = Table('StatsCities', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String),
    Column('value', String),
    Column('visitors', Integer),
    Column('day', String),
)

StatsCountries = Table('StatsCountries', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('code', String),
    Column('name', String),
    Column('value', String),
    Column('visitors', Integer),
    Column('day', String),
)

StatsSex = Table('StatsSex', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('value', String),
    Column('visitors', Integer),
    Column('day', String),
)

StatsSexAge = Table('StatsSexAge', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('value', String),
    Column('visitors', Integer),
    Column('day', String),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['Stats'].create()
    post_meta.tables['StatsAge'].create()
    post_meta.tables['StatsCities'].create()
    post_meta.tables['StatsCountries'].create()
    post_meta.tables['StatsSex'].create()
    post_meta.tables['StatsSexAge'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['Stats'].drop()
    post_meta.tables['StatsAge'].drop()
    post_meta.tables['StatsCities'].drop()
    post_meta.tables['StatsCountries'].drop()
    post_meta.tables['StatsSex'].drop()
    post_meta.tables['StatsSexAge'].drop()
