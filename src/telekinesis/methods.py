from datetime import datetime
import os
import json
import logging

from flask import request, jsonify

from .Gatekeeper import Gatekeeper, GatekeeperException

from .validator import validated_by, authorized_by, attach_authorizer
from . import validator
from .models import Script, User, Permissions
from . import models
from .utils import SqlConn
from .executor import run_script


@validated_by(validator.script_create)
@authorized_by(Permissions.script.create)
def script_create(**jsn):
    logging.debug('Entering script_create')
    script = Script.from_dict(jsn)
    script.store()

    new_permissions = [
        Permissions.script.read(script.script_id),
        Permissions.script.update(script.script_id),
        Permissions.script.destroy(script.script_id),
        Permissions.script.execute(script.script_id),
    ]

    user = auth.get_session_user(request.cookies.get('session', ''))
    logging.info('User {} has created new script {}'.format(user, script.script_id))

    for p in new_permissions:
        auth.create_permission(p)
        auth.apply_permission(user, p)

    logging.info('Creating public user for script {}'.format(script.script_id))
    script_public_user = User.public(script.script_id)
    auth.create_user(script_public_user, '')
    auth.apply_permission(script_public_user, new_permissions[0])  # READ
    auth.apply_permission(script_public_user, new_permissions[3])  # EXECUTE

    public_token = auth.create_session(script_public_user, datetime(year=9000, month=1, day=1))
    script.public_token = public_token

    script.update()
    logging.info('New script was created successfully')

    return jsonify(script.as_dict()), 200


@validated_by(validator.script_read, pathargs=['script_id'])
@authorized_by(Permissions.script.read, field='script_id')
def script_read(script_id):
    logging.debug('Entering script_read on id {}'.format(script_id))
    script = Script.get(script_id)

    if not script:
        logging.warning('Searched for and found no script with id {}'.format(script_id))
        return jsonify({'errors': 'No such script {}'.format(script_id)}), 400

    return jsonify(script.as_dict()), 200


@validated_by(validator.script_update, pathargs=['script_id'])
@authorized_by(Permissions.script.update, field='script_id')
def script_update(script_id, **jsn):
    logging.debug('Entering script_update on id {}'.format(script_id))
    script = Script.get(script_id)

    if not script:
        logging.warning('Searched for and found no script with id {}'.format(script_id))
        return jsonify({'errors': 'No such script {}'.format(script_id)}), 400

    script.update_from_dict(jsn)
    script.update()
    logging.debug('Script was updated successfully')

    return jsonify(script.as_dict()), 200


@validated_by(validator.script_delete, pathargs=['script_id'])
@authorized_by(Permissions.script.destroy, field='script_id')
def script_destroy(script_id):
    logging.info('Entering script_destroy on id {}'.format(script_id))
    old_permissions = [
        Permissions.script.read(script_id),
        Permissions.script.update(script_id),
        Permissions.script.destroy(script_id),
        Permissions.script.execute(script_id),
    ]

    logging.info('Removing old permissions from deleted script {}'.format(script_id))
    for p in old_permissions:
        auth.delete_permission(p)

    logging.info('Removing old public user from script {}'.format(script_id))
    auth.delete_user(User.public(script_id))

    Script(script_id).delete()
    logging.info('Deletion successful')

    return '', 200


@validated_by(validator.script_execute, pathargs=['script_id'])
@authorized_by(Permissions.script.execute, field='script_id')
def script_execute(script_id):
    logging.debug('Entering script_execute on script {}'.format(script_id))
    script = Script.get(script_id)

    if not script:
        logging.warning('Searched for and found no script with id {}'.format(script_id))
        return jsonify({'errors': 'No such script {}'.format(script_id)}), 400

    resp = run_script(script)
    logging.debug('Script was run successfully')

    return jsonify(resp), 200


@authorized_by(Permissions.scripts.read)
def scripts_read():
    logging.debug('Entering scripts_read, reading list of all scripts')
    scripts = Script.get_all()

    res = []
    for script in scripts:
        res.append(script.as_dict())

    return jsonify(res), 200


@validated_by(validator.user_create)
@authorized_by(Permissions.user.create)
def user_create(**jsn):
    logging.info('Entering user_create, creating new user {}'.format(jsn['username']))
    User.from_dict(jsn).store()

    logging.debug('User was created successfully')
    return '', 200


@validated_by(validator.user_read, pathargs=['username'])
def user_read(username):
    logging.info('Entering user_read, requesting read on user {}'.format(username))
    session = request.cookies.get('session', '')
    session_username = auth.get_session_user(session)

    if not session_username:
        logging.debug('Invalid token, refused to read')
        return jsonify({
            'errors': 'Invalid or expired token'
        }), 401

    if not (auth.check_permission(session, Permissions.user.read) or username == session_username):
        logging.warning('Insufficient permission for user read by {} on {}'.format(session_username, username))
        return jsonify({
            'errors': 'Insufficient permission: requires permission {}'.format(Permissions.user.read)
        }), 401

    return jsonify(User.get(username).as_dict()), 200


@validated_by(validator.user_delete, pathargs=['username'])
def user_delete(username):
    logging.info('Entering user_delete on user {}'.format(username))
    session = request.cookies.get('session', '')
    session_username = auth.get_session_user(session)

    if not session_username:
        logging.debug('Invalid token, refused to read')
        return jsonify({
            'errors': 'Invalid or expired token'
        }), 401

    if not (auth.check_permission(session, Permissions.user.destroy) or username == session_username):
        logging.warning('Insufficient permission for user delete by {} on {}'.format(session_username, username))
        return jsonify({
            'errors': 'Insufficient permission: requires permission {}'.format(Permissions.user.destroy)
        }), 401

    return jsonify(User.get(username).as_dict()), 200


@validated_by(validator.permission_create)
def permission_create(**jsn):
    logging.info('Entering permission_create on user {}, permission {}'.format(jsn['username'], jsn['permission']))
    session = request.token if hasattr(request, 'token') else request.cookies.get('session', '')

    # Script[x] permissions are weird -- users with script.update.[x] can grant them to other users
    if jsn['permission'].startswith('script.') and jsn['permission'] != 'script.create':
        script_id = jsn['permission'].split('.')[2]
        logging.info('Script permission on script {} -- checking permission sharing first'.format(script_id))

        if (
                auth.check_permission(session, Permissions.script.update(script_id)) and
                auth.check_permission(session, jsn['permission'])
        ):
            logging.info('Permission sharing acceptable, applying')
            auth.apply_permission(jsn['username'], jsn['permission'])
            logging.info('Permission created')
            return '', 200
        else:
            logging.info('Permission sharing failed, falling back to standard permission.create')

    if not auth.check_permission(session, Permissions.permission.create):
        logging.warning('Insufficient permission to add permission {} on user {}'.format(
            jsn['username'], jsn['permission']))
        return jsonify({
            'errors': 'Insufficient permission: requires permission {}'.format(Permissions.permission.create)
        }), 401

    auth.apply_permission(jsn['username'], jsn['permission'])
    logging.info('Permission created')
    return '', 200


@validated_by(validator.permission_delete)
def permission_delete(**jsn):
    logging.info('Entering permission_delete on user {}, permission {}'.format(jsn['username'], jsn['permission']))
    session = request.token if hasattr(request, 'token') else request.cookies.get('session', '')

    # Can remove script[x] permissions from public users if script.update.[x] permitted
    if jsn['permission'].startswith('script.') and jsn['permission'] != 'script.create':
        script_id = jsn['permission'].split('.')[2]
        logging.info('Script permission on script {} -- checking public user management first'.format(script_id))

        if (
                auth.check_permission(session, Permissions.script.update(script_id)) and
                jsn['username'].startswith(User.public(''))
        ):
            logging.info('Removing updateable script permission from public user allowed, continuing')
            auth.remove_permission(jsn['user'], jsn['permission'])
            logging.info('Permission removed')
            return '', 200
        else:
            logging.info('Public user management failed, falling back to standard permission.destroy')

    if not auth.check_permission(session, Permissions.permission.destroy):
        logging.warning('Insufficient permission to remove permission {} from user {}'.format(
            jsn['username'], jsn['permission']))
        return jsonify({
            'errors': 'Insufficient permission: requires permission {}'.format(Permissions.permission.destroy)
        }), 401

    auth.remove_permission(jsn['username'], jsn['permission'])
    logging.info('Permission removed')
    return '', 200


@validated_by(validator.user_login)
def login(**jsn):
    if auth.login(jsn['username'], jsn['password']):
        logging.info('Logging in user {}'.format(jsn['username']))
        session = auth.create_session(jsn['username'], datetime(year=9000, month=1, day=1))
        return jsonify({'session': session}), 200, {'set-cookie': 'session={}'.format(session)}
    else:
        logging.warning('Invalid login attempt on user {}'.format(jsn['username']))
        return jsonify({'errors': 'Invalid credentials'}), 401


def directory():
    swagger_path = os.path.join(os.path.dirname(__file__), 'swaggerfile.json')
    with open(swagger_path, 'r') as swagger_f:
        swagger = swagger_f.read()
    return swagger, 200, {'content-type': 'application/json'}


def initialize(admin_username, admin_password, data_dir):
    global auth

    logging.info('Initializing database connection')

    auth = Gatekeeper(os.path.join(data_dir, 'security.db'))
    conn = SqlConn(os.path.join(data_dir, 'telekinesis.db'))

    models.setup(auth=auth, conn=conn)
    attach_authorizer(auth)

    logging.info('Attempting to get administrator')
    if not auth.login(admin_username, admin_password):
        logging.info('Administrator login failed, will try to create a new admin')
        try:
            auth.create_user(admin_username, admin_password)
        except GatekeeperException:
            logging.info('Administrator exists, old password changed')
            auth.change_user_password(admin_username, admin_password)

    bootstrap_permissions = [
        Permissions.script.create,
        Permissions.scripts.read,
        Permissions.user.create,
        Permissions.user.destroy,
        Permissions.user.read,
        Permissions.permission.create,
        Permissions.permission.destroy,
    ]

    user_permissions = auth.get_permissions(admin_username)

    logging.info('Ensuring required permissions exist')
    for p in bootstrap_permissions:
        if p not in user_permissions:
            logging.info('Admin lacks permission {}, will create or apply'.format(p))
            try:
                auth.apply_permission(admin_username, p)
            except GatekeeperException:
                logging.info('Permission does not exist, will create')
                auth.create_permission(p)
                auth.apply_permission(admin_username, p)
