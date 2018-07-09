from .utils import required, coerce_bool

_script_id = {
    'type': 'integer',
    'min': 0,
    'required': False,
}
_script_id_required = required(_script_id)

_script = {
    'type': 'string',
    'minlength': 0,
    'maxlength': 10000,
    'required': False,
}
_script_required = required(_script)

_description = {
    'type': 'string',
    'minlength': 0,
    'maxlength': 10000,
    'required': False,
}
_description_required = required(_description)

_fork = {
    'type': 'boolean',
    'coerce': coerce_bool,
    'required': False,
}
_fork_required = required(_fork)


script_create = {
    'script': _script_required,
    'description': _description_required,
    'fork': _fork_required,
}

script_read = {
    'script_id': _script_id_required,
}

script_update = {
    'script_id': _script_id_required,
    'script': _script,
    'description': _description,
    'fork': _fork,
}

script_delete = {
    'script_id': _script_id_required,
}

script_execute = {
    'script_id': _script_id_required,
}
