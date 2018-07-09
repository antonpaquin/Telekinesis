from __future__ import absolute_import

import os

from ..utils import SqlConn, load_sql


def attach_sql(connection: SqlConn):
    global conn
    conn = connection


sql = load_sql(os.path.join(os.path.dirname(__file__), 'script.sql'))


class Script:
    def __init__(self, script_id=None, script=None, description=None, fork=None, public_token=None):
        self.script_id = script_id
        self.script = script
        self.description = description
        self.fork = fork
        self.public_token = public_token

    def _clone(self, other: 'Script'):
        self.script_id = other.script_id
        self.script = other.script
        self.description = other.description
        self.fork = other.fork
        self.public_token = other.public_token

    @staticmethod
    def get(script_id) -> 'Script':
        with conn as cur:
            cur.execute(sql['get_script_by_id'], (script_id,))
            row = cur.fetchone()

        if not row:
            return None
        else:
            return Script(script_id=row[0], script=row[1], description=row[2], fork=row[3], public_token=row[4])

    @staticmethod
    def get_all() -> ['Script']:
        with conn as cur:
            cur.execute(sql['get_all_scripts'])
            rows = cur.fetchall()

        return [Script(*row) for row in rows]

    def store(self):
        with conn as cur:
            cur.execute(sql['put_script'], (self.script, self.description, self.fork, self.public_token))
            cur.execute(sql['get_last_id'])
            row = cur.fetchone()

        self.script_id = row[0]

    def update(self):
        with conn as cur:
            cur.execute(sql['update_script'], (self.script, self.description, self.fork, self.public_token, self.script_id))

    def delete(self):
        with conn as cur:
            cur.execute(sql['delete_script'], (self.script_id,))

    def refresh(self):
        self._clone(self.get(self.script_id))

    def as_dict(self) -> dict:
        return {
            'script_id': self.script_id,
            'script': self.script,
            'description': self.description,
            'fork': self.fork,
            'public_token': self.public_token,
        }

    @staticmethod
    def from_dict(data: dict) -> 'Script':
        return Script(
            script_id=data.get('script_id', None),
            script=data['script'],
            description=data['description'],
            fork=data['fork'],
        )

    def update_from_dict(self, data: dict):
        if 'script_id' in data:
            self.script_id = data['script_id']
        if 'script' in data:
            self.script = data['script']
        if 'description' in data:
            self.description = data['description']
        if 'fork' in data:
            self.fork = data['fork']
        if 'public_token' in data:
            self.public_token = data['public_token']
