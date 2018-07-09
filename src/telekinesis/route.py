from __future__ import absolute_import

import logging
import json

from flask import Flask, request, Response, jsonify

from .methods import \
    script_create, \
    script_read, \
    script_update, \
    script_destroy, \
    script_execute, \
    scripts_read, \
    user_create, \
    user_read, \
    user_delete, \
    permission_create, \
    permission_delete, \
    login, \
    directory


app = Flask(__name__)


@app.before_request
def pre_request():
    logging.info('Handling request {} {}'.format(request.method, request.path))


@app.after_request
def post_request(response: Response):
    logging.info('Returned code {}'.format(response.status_code))
    response.headers.set('Access-Control-Allow-Origin', '*')
    response.headers.set('Access-Control-Allow-Headers', 'Cookie, content-type')
    return response


@app.errorhandler(404)
def handle_missing_route(err):
    logging.warning('Returning 404 for request on path {} {}'.format(request.method, request.path))
    resp = jsonify({'errors': 'unknown path or method: {} {}'.format(request.method, request.path)})
    resp.status_code = 404
    return resp


@app.errorhandler(500)
def handle_error(err):
    logging.error('Error on request {} {}'.format(request.method, request.path))
    logging.error('Headers: {}'.format(json.dumps(dict(request.headers.items()))))
    logging.error('Raw data: {}'.format(str(request.get_data())))
    return jsonify({'errors': 'An unknown error has occurred'}), 500


@app.route('/', methods=['GET'])
def route_directory():
    return directory()


@app.route('/script', methods=['PUT', 'OPTIONS'])
def route_script():
    if request.method == 'OPTIONS':
        return '', 200, {'Access-Control-Allow-Methods': 'PUT, OPTIONS'}
    else:
        return {
            'PUT': script_create,
        }.get(request.method)()


@app.route('/script/<int:script_id>', methods=['GET', 'PATCH', 'DELETE', 'POST', 'OPTIONS'])
def route_script_id(script_id):
    if request.method == 'OPTIONS':
        return '', 200, {'Access-Control-Allow-Methods': 'GET, PATCH, DELETE, POST, OPTIONS'}
    else:
        return {
            'GET': script_read,
            'PATCH': script_update,
            'DELETE': script_destroy,
            'POST': script_execute,
        }.get(request.method)(script_id=script_id)


@app.route('/script/<int:script_id>/<string:token>', methods=['GET', 'PATCH', 'DELETE', 'POST', 'OPTIONS'])
def route_script_id_token(script_id, token):
    request.token = token
    if request.method == 'OPTIONS':
        return '', 200, {'Access-Control-Allow-Methods': 'GET, PATCH, DELETE, POST, OPTIONS'}
    else:
        return {
            'GET': script_read,
            'PATCH': script_update,
            'DELETE': script_destroy,
            'POST': script_execute,
        }.get(request.method)(script_id=script_id)


@app.route('/scripts', methods=['GET', 'OPTIONS'])
def route_scripts():
    if request.method == 'OPTIONS':
        return '', 200, {'Access-Control-Allow-Methods': 'GET, OPTIONS'}
    else:
        return {
            'GET': scripts_read,
        }.get(request.method)()


@app.route('/user', methods=['PUT', 'OPTIONS'])
def route_user():
    if request.method == 'OPTIONS':
        return '', 200, {'Access-Control-Allow-Methods': 'PUT, OPTIONS'}
    else:
        return {
            'PUT': user_create,
        }.get(request.method)()


@app.route('/user/<string:username>', methods=['GET', 'DELETE', 'OPTIONS'])
def route_user_name(username):
    if request.method == 'OPTIONS':
        return '', 200, {'Access-Control-Allow-Methods': 'GET, DELETE, OPTIONS'}
    else:
        return {
            'GET': user_read,
            'DELETE': user_delete,
        }.get(request.method)(username=username)


@app.route('/permission', methods=['PUT', 'DELETE', 'OPTIONS'])
def route_permission():
    if request.method == 'OPTIONS':
        return '', 200, {'Access-Control-Allow-Methods': 'PUT, DELETE, OPTIONS'}
    else:
        return {
            'PUT': permission_create,
            'DELETE': permission_delete,
        }.get(request.method)()


@app.route('/login', methods=['POST'])
def route_login():
    return login()
