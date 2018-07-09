from telekinesis import Telekinesis, initialize

import multiprocessing
import gunicorn.app.base
from gunicorn.six import iteritems

import argparse
import logging
import os


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Allow remote execution of scripts')
    parser.add_argument('-a', '--admin', type=str, help='Username for the admin account', required=True)
    parser.add_argument('-p', '--password', type=str, help='Password for the admin account', required=True)
    parser.add_argument('--log-dir', type=str, help='Storage for Telekinesis logs', default='.')
    parser.add_argument('--data-dir', type=str, help='Storage for Telekinesis logs', default='.')
    parser.add_argument('--port', type=str, help='Storage for Telekinesis logs', default='80')
    args = parser.parse_args()

    logging.basicConfig(
        filename=os.path.join(args.log_dir, 'telekinesis.log'),
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    initialize(args.admin, args.password, args.data_dir)
    options = {
        'bind': '%s:%s' % ('0.0.0.0', args.port),
        'workers': number_of_workers(),
    }
    StandaloneApplication(Telekinesis, options).run()
