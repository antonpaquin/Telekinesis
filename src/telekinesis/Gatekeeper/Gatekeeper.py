import os
from datetime import datetime
from hashlib import sha512
import base64
import uuid
import sqlite3
import logging

from .utils import load_sql, SqlConn

root_name = os.path.dirname(__file__)
sql = load_sql(os.path.join(root_name, 'gatekeeper.sql'))


logger = logging.getLogger(__name__)


class GatekeeperException(Exception):
    def __init__(self, msg):
        logger.error(msg)
        super().__init__(msg)


class Gatekeeper:
    def __init__(self, db_location: str):
        self.db_location = db_location

        dirname = os.path.dirname(db_location)
        if not os.path.isdir(dirname):
            raise GatekeeperException('Path to directory: {} does not exist'.format(dirname))

        if not os.path.isfile(db_location):
            self._create_database()


    def _create_database(self):
        try:
            with SqlConn(self.db_location) as cur:
                cur.execute(sql['create_users'])
                cur.execute(sql['create_sessions'])
                cur.execute(sql['create_permission_types'])
                cur.execute(sql['create_permissions'])
        except Exception as e:
            raise GatekeeperException('Could not create database: {}'.format(str(e)))


    @staticmethod
    def _get_pass_hash(password: str, salt: bytes):
        hasher = sha512()
        hasher.update(password.encode('utf-8'))
        hasher.update(salt)
        return hasher.hexdigest()


    @staticmethod
    def _validate(key: str, value: str):
        try:
            if not isinstance(value, str):
                raise GatekeeperException('param "{}" must be type "str"'.format(key))
            if not len(value) > 0:
                raise GatekeeperException('param "{}" must have length > 0'.format(key))
            if not len(value) < 10000:
                raise GatekeeperException('param "{}" must have length < 10000'.format(key))
        except Exception as e:
            if isinstance(e, GatekeeperException):
                raise e
            else:
                raise GatekeeperException('Unknown error validating param "{}", {}'.format(key, str(e)))


    @staticmethod
    def _validate_nomin(key: str, value: str):
        try:
            if not isinstance(value, str):
                raise GatekeeperException('param "{}" must be type "str"'.format(key))
            if not len(value) < 10000:
                raise GatekeeperException('param "{}" must have length < 10000'.format(key))
        except Exception as e:
            if isinstance(e, GatekeeperException):
                raise e
            else:
                raise GatekeeperException('Unknown error validating param "{}", {}'.format(key, str(e)))


    @staticmethod
    def _validate_expiry(expiry: datetime):
        try:
            if not isinstance(expiry, datetime):
                raise GatekeeperException('param "expiry" must be type "datetime"')
        except Exception as e:
            if isinstance(e, GatekeeperException):
                raise e
            else:
                raise GatekeeperException('Unknown error validating param "expiry", {}'.format(str(e)))


    def create_user(self, user: str, password: str):
        self._validate('user', user)
        self._validate_nomin('password', password)

        salt = os.urandom(128)
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        pass_hash = self._get_pass_hash(password, salt)

        try:
            with SqlConn(self.db_location) as cur:
                cur.execute(sql['create_user'], (user, pass_hash, salt_b64))
        except sqlite3.IntegrityError as e:
            if e.args[0] == 'UNIQUE constraint failed: users.uname':
                raise GatekeeperException('User already exists')
            else:
                raise e


    def change_user_password(self, user: str, password: str):
        self._validate('user', user)
        self._validate_nomin('password', password)

        salt = os.urandom(128)
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        pass_hash = self._get_pass_hash(password, salt)

        with SqlConn(self.db_location) as cur:
            cur.execute(sql['change_password'], (pass_hash, salt_b64, user))


    def login(self, user: str, password: str) -> bool:
        self._validate('user', user)
        self._validate_nomin('password', password)

        if password == '':
            return False

        with SqlConn(self.db_location) as cur:
            cur.execute(sql['get_pass_hash'], (user,))
            results = cur.fetchone()

        if not results:
            return False

        pass_hash, salt_b64 = results
        salt = base64.b64decode(salt_b64)

        return pass_hash == self._get_pass_hash(password, salt)


    def delete_user(self, user: str):
        self._validate('user', user)

        with SqlConn(self.db_location) as cur:
            cur.execute(sql['delete_user'], (user,))


    def create_session(self, user: str, expiry: datetime) -> str:
        self._validate('user', user)
        self._validate_expiry(expiry)

        token = uuid.uuid4().hex
        with SqlConn(self.db_location) as cur:
            cur.execute(sql['expire_sessions_user'], (user,))
            cur.execute(sql['create_session'], (token, expiry, user))

        return token


    def expire_sessions_date(self, expiry: datetime = None):
        if not expiry:
            expiry = datetime.now()

        self._validate_expiry(expiry)

        with SqlConn(self.db_location) as cur:
            cur.execute(sql['expire_sessions'], (expiry,))


    def expire_sessions_user(self, user: str):
        self._validate('user', user)

        with SqlConn(self.db_location) as cur:
            cur.execute(sql['expire_sessions_user'], (user,))


    def apply_permission(self, user: str, permission: str):
        self._validate('user', user)
        self._validate('permission', permission)

        try:
            with SqlConn(self.db_location) as cur:
                cur.execute(sql['add_permission'], (user, permission))
        except sqlite3.IntegrityError as e:
            if e.args[0] == 'FOREIGN KEY constraint failed':
                raise GatekeeperException('No such user')
            elif e.args[0] == 'NOT NULL constraint failed: permissions.ptype':
                raise GatekeeperException('No such permission')
            elif e.args[0] == 'UNIQUE constraint failed: permissions.uname, permissions.ptype':
                pass  # The permission already is present; be less pedantic and do nothing
            else:
                raise e


    def get_permissions(self, user: str):
        self._validate('user', user)

        with SqlConn(self.db_location) as cur:
            cur.execute(sql['get_permissions'], (user,))
            rows = cur.fetchall()

        return [row[0] for row in rows]


    def remove_permission(self, user: str, permission: str):
        self._validate('user', user)
        self._validate('permission', permission)

        with SqlConn(self.db_location) as cur:
            cur.execute(sql['remove_permission'], (user, permission))


    def create_permission(self, permission: str):
        self._validate('permission', permission)

        with SqlConn(self.db_location) as cur:
            cur.execute(sql['add_permission_type'], (permission,))


    def delete_permission(self, permission: str):
        self._validate('permission', permission)

        with SqlConn(self.db_location) as cur:
            cur.execute(sql['delete_permission_type'], (permission,))


    def check_permission(self, session: str, permission: str, expiry: datetime = None) -> bool:
        self._validate_nomin('session', session)
        self._validate('permission', permission)

        if not expiry:
            expiry = datetime.now()

        self._validate_expiry(expiry)

        if session == '':
            return False

        with SqlConn(self.db_location) as cur:
            cur.execute(sql['check_token_permission'], (session, permission, expiry))
            results = cur.fetchone()
        return bool(results)


    def get_session_user(self, session: str, expiry: datetime = None) -> str:
        self._validate_nomin('session', session)

        if not expiry:
            expiry = datetime.now()

        self._validate_expiry(expiry)

        if session == '':
            return None

        with SqlConn(self.db_location) as cur:
            cur.execute(sql['get_session_user'], (session, expiry))
            results = cur.fetchone()

        if not results:
            return None

        return results[0]
