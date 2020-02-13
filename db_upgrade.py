#!flask/bin/python
from migrate.versioning import api
from new_bot_wall_post.app.config import SQLALCHEMY_DATABASE_URI
from new_bot_wall_post.app.config import SQLALCHEMY_MIGRATE_REPO
api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
print('Current database version: ' + str(api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)))
