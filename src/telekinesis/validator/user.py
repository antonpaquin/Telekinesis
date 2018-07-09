from .utils import required


def prevent_internal_usernames(field, value, error):
    if not isinstance(value, str):
        error(field, 'Username must be a string')

    if value.startswith('#'):
        error(field, 'Username may not start with \'#\'')


_username = {
    'type': 'string',
    'minlength': 1,
    'maxlength': 100,
    'required': False,
    'validator': prevent_internal_usernames,
}
_username_required = required(_username)

_password = {
    'type': 'string',
    'minlength': 1,
    'maxlength': 100,
    'required': False,
}
_password_required = required(_password)


user_create = {
    'username': _username_required,
    'password': _password_required,
}

user_read = {
    'username': _username_required,
}

user_delete = {
    'username': _username_required,
}

user_login = {
    'username': _username_required,
    'password': _password_required,
}
