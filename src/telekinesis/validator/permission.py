from .utils import required
from ..models import Permissions

from .user import _username_required
from copy import deepcopy


# The standard username validator prevents the #script.public.[x] username, which is used for internal purposes, but for
# deleting permissions on public users we have to allow that format of username for *only* permission.delete validation
# Thus we strip the custom validator
_username_required_allow_public = deepcopy(_username_required)
del _username_required_allow_public['validator']


def valid_permission(field, value, error):
    if not isinstance(value, str):
        error(field, "Must be type \"string\"")

    if value in {
        Permissions.script.create,
        Permissions.scripts.read,
        Permissions.user.create,
        Permissions.user.read,
        Permissions.user.destroy,
        Permissions.permission.create,
        Permissions.permission.destroy,
    }:
        return

    if not value.startswith("script."):
        error(field, "Invalid permission")

    units = value.split('.')

    if not len(units) == 3:
        error(field, "Invalid permission")

    if not units[1] in {
        "read",
        "update",
        "destroy",
        "execute",
    }:
        error(field, "Invalid permission")

    if not len(units[2]) > 0:
        error(field, "Invalid permission")


_permission = {
    'type': 'string',
    'minlength': 1,
    'maxlength': 255,
    'validator': valid_permission,
    'required': False,
}
_permission_required = required(_permission)

permission_create = {
    'username': _username_required,
    'permission': _permission_required
}

permission_delete = {
    'username': _username_required_allow_public,
    'permission': _permission_required,
}
