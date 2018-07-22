from telekinesis import Telekinesis, initialize

import multiprocessing
import gunicorn.app.base
from gunicorn.six import iteritems

import argparse
import logging
import os
import json


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def get_config(parser):
    cl_args = dict(parser.parse_args()._get_kwargs())

    if cl_args['config']:
        try:
            with open(cl_args['config'], 'r') as f_config:
                f_args = json.load(f_config)
        except json.decoder.JSONDecodeError as err:
            print('Could not parse JSON config: syntax error -- {}'.format(err))
            exit(1)
    else:
        f_args = {}

    defaults = {
        'admin': None,
        'password': None,
        'log_dir': '.',
        'data_dir': '.',
        'port': '80',
        'ssh': '',
        'run_as_user': '',
        'run_as_password': '',
    }

    data = {}

    for field in defaults.keys():
        if field in cl_args and cl_args[field]:  # Take from command line first priority
            data[field] = cl_args[field]
        elif field in f_args and f_args[field]:  # Next try the config file
            data[field] = f_args[field]
        elif defaults[field] is not None:  # If defaults is not None, take the default
            data[field] = defaults[field]
        else:  # Otherwise, throw an error
            parser.error('{} is required'.format(field))

    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Allow remote execution of scripts')
    parser.add_argument('-a', '--admin', type=str, help='Username for the admin account', default='')
    parser.add_argument('-p', '--password', type=str, help='Password for the admin account', default='')
    parser.add_argument('--log-dir', type=str, help='Storage for Telekinesis logs', default='')
    parser.add_argument('--data-dir', type=str, help='Storage for Telekinesis logs', default='')
    parser.add_argument('--port', type=str, help='Storage for Telekinesis logs', default='')
    parser.add_argument('--ssh', type=str, help='Params to SSH into a target before executing a script', default='')
    parser.add_argument('-c', '--config', type=str, help='Use config file for telekinesis setup. Command line arguments take priority.', default='')
    args = get_config(parser)

    if not (args['ssh'] or (args['run_as_user'] and args['run_as_password'])):
        print('Telekinesis will execute scripts as the current user. This is potentially unsafe -- they will be able '
              'to access local files and edit the permissions database. It is recommended to run as an unprivileged '
              'user, or to change the execution environment (e.g. to a container) via SSH')

    logging.basicConfig(
        filename=os.path.join(args['log_dir'], 'telekinesis.log'),
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    initialize(
        admin_username=args['admin'],
        admin_password=args['password'],
        data_dir=args['data_dir'],
        security={
            'security_type': 'ssh' if args['ssh'] else 'user' if (args['run_as_user'] and args['run_as_password']) else 'none',
            'ssh_args': args['ssh'],
            'username': args['run_as_user'],
            'password': args['run_as_password'],
        },
    )

    options = {
        'bind': '%s:%s' % ('0.0.0.0', args['port']),
        'workers': number_of_workers(),
    }
    StandaloneApplication(Telekinesis, options).run()
