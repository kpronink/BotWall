#!flask/bin/python
from migrate.versioning import api
from new_bot_wall_post.app.config import SQLALCHEMY_DATABASE_URI
from new_bot_wall_post.app.config import SQLALCHEMY_MIGRATE_REPO

import os.path

from new_bot_wall_post.app.models import Base, engine

Base.metadata.create_all(engine)

if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
