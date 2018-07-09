from functools import wraps
import logging
import json

from flask import request, jsonify
import cerberus


def validated_by(schema, pathargs=None):
    if pathargs is None:
        pathargs = []

    def annotator(f):
        @wraps(f)
        def myfun(**kwargs):
            logging.debug('Beginning validation on request')
            try:
                data = request.get_json(force=True)
            except:
                data = {}
            for arg in pathargs:
                data[arg] = kwargs[arg]

            v = cerberus.Validator()
            if not v.validate(data, schema):
                errors = v.errors
                logging.warning('Request failed validation: data={}, errors={}'.format(
                    json.dumps(data),
                    json.dumps(errors),
                ))
                return jsonify({'errors': errors}), 400

            logging.debug('Validation succeeded')
            document = v.document

            return f(**document)
        return myfun
    return annotator


def attach_authorizer(authorizer):
    global auth
    auth = authorizer


def authorized_by(permission, field=None):
    global auth

    def annotator(f):
        @wraps(f)
        def myfun(**kwargs):
            logging.debug('Beginning authorization on request')
            if callable(permission) and field:
                p = permission(kwargs[field])
            else:
                p = permission

            if hasattr(request, 'token'):
                logging.info('Authorizing via token')
                session_token = request.token
            else:
                session_token = request.cookies.get('session', '')

            if not auth.check_permission(session_token, p):
                logging.warning('Authorization failed for token {} on permission {}'.format(session_token, p))
                return jsonify({
                    'errors': 'Insufficient permission: requires permission {}'.format(p)
                }), 401

            logging.debug('Authorization succeeded')
            return f(**kwargs)
        return myfun
    return annotator
