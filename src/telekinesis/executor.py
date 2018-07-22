import subprocess
import os
import base64
import shlex

from .models import Script


security = {}


def set_security(security_type, **kwargs):
    global security

    if security_type == 'none':
        security['type'] = 'none'

    elif security_type == 'user':
        security['type'] = 'user'
        security['username'] = kwargs['username']
        security['password'] = kwargs['password']

    elif security_type == 'ssh':
        security['type'] = 'ssh'
        security['ssh_args'] = shlex.split(kwargs['ssh_args'])


def run_script(script_obj: Script):
    script = script_obj.script
    fork = script_obj.fork

    working_dir = os.getenv('HOME')

    if security['type'] == 'none':
        sp = subprocess.Popen(
            args=script,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=working_dir,
        )

    elif security['type'] == 'user':
        sp = subprocess.Popen(
            args=["su", security['username']],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            cwd=working_dir,
        )
        sp.stdin.write(security['password'].encode('utf-8'))
        sp.stdin.write(bytes([10]))
        sp.stdin.write(script.encode('utf-8'))

    elif security['type'] == 'ssh':
        sp = subprocess.Popen(
            args=["ssh", "-T"] + security['ssh_args'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            cwd=working_dir,
        )
        sp.stdin.write(script.encode('utf-8'))

    else:
        sp = None

    if fork:
        return {
            'exit_status': '',
            'stdout': '',
            'stderr': '',
            'pid': sp.pid,
        }

    else:
        try:
            stdout, stderr = sp.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            sp.kill()
            return {
                'pid': sp.pid,
                'stdout': '',
                'stderr': '',
                'exit_status': '',
                'errors': 'Process did not terminate in a timely manner',
            }

        try:
            stdout = stdout.decode('utf-8')
        except UnicodeDecodeError:
            stdout = {
                'data': base64.b64encode(stdout).decode('utf-8'),
                'format': 'base64'
            }

        try:
            stderr = stderr.decode('utf-8')
        except UnicodeDecodeError:
            stderr = {
                'data': base64.b64encode(stderr).decode('utf-8'),
                'format': 'base64'
            }

        return {
            'pid': sp.pid,
            'stdout': stdout,
            'stderr': stderr,
            'exit_status': sp.returncode,
        }
