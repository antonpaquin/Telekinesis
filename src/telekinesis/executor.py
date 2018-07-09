import subprocess
import os
import base64

from .models import Script


def run_script(script_obj: Script):
    script = script_obj.script
    fork = script_obj.fork

    working_dir = os.getenv('HOME')

    sp = subprocess.Popen(
        args=script,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        cwd=working_dir,
    )

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
