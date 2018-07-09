from __future__ import absolute_import

from datetime import datetime
from copy import deepcopy

from ..Gatekeeper import Gatekeeper, GatekeeperException


def attach_auth(authorization: Gatekeeper):
    global auth
    auth = authorization


class User:
    def __init__(self, username=None, password=None, permissions=None):
        self.username = username
        self.password = password

        if permissions is None:
            self.permissions = []
        else:
            self.permissions = permissions

    def _clone(self, other: 'User'):
        self.username = other.username
        self.password = other.password
        self.permissions = deepcopy(other.permissions)

    @staticmethod
    def get(username) -> 'User':
        try:
            permissions = auth.get_permissions(username)
        except GatekeeperException:
            return None

        return User(username=username, permissions=permissions)

    def get_session(self, expiry=None):
        if expiry is None:
            expiry = datetime(year=9000, month=1, day=1)

        if auth.login(user=self.username, password=self.password):
            return auth.create_session(user=self.username, expiry=expiry)

    def store(self):
        auth.create_user(user=self.username, password=self.password)

    def delete(self):
        auth.delete_user(user=self.username)

    def refresh(self):
        self._clone(self.get(self.username))

    def add_permission(self, permission: str):
        auth.apply_permission(user=self.username, permission=permission)

    def remove_permission(self, permission: str):
        auth.remove_permission(user=self.username, permission=permission)

    def as_dict(self) -> dict:
        return {
            'username': self.username,
            'permissions': self.permissions,
        }

    @staticmethod
    def from_dict(data: dict) -> 'User':
        return User(
            username=data['username'],
            password=data['password'],
        )

    @staticmethod
    def public(script_id: str):
        return '#script.public.{}'.format(script_id)
