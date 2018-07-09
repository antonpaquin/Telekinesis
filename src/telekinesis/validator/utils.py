from copy import deepcopy


def required(elem: dict) -> dict:
    d = deepcopy(elem)
    d['required'] = True
    return d


def coerce_bool(b):
    if isinstance(b, str):
        return b.lower() in {'true', 't', '1', 'yes', 'y'}
    elif isinstance(b, int):
        return b > 0
    return bool(b)
