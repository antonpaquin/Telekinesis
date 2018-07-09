from __future__ import absolute_import

from .user import User
from .script import Script
from .permission import Permissions

from .user import attach_auth as _user_attach_auth
from .script import attach_sql as _script_attach_sql

from ..utils import load_sql, SqlConn
from ..Gatekeeper import Gatekeeper
import os


def setup(auth: Gatekeeper, conn: SqlConn):
    _user_attach_auth(auth)
    _script_attach_sql(conn)

    if not os.path.isfile(conn.db_location):
        sql = load_sql(os.path.join(os.path.dirname(__file__), 'create_db.sql'))
        with conn as cur:
            cur.execute(sql['create_scripts'])
