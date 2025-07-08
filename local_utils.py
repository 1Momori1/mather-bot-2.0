import subprocess
import sys
import os


def start_local_bot(script_path):
    try:
        p = subprocess.Popen([sys.executable, script_path])
        return True, None
    except Exception as e:
        return False, str(e)


def stop_local_bot(name):
    try:
        os.system(f'pkill -f "{name}"')
        return True, None
    except Exception as e:
        return False, str(e)


def is_local_bot_running(script_path):
    script_name = os.path.basename(script_path)
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.check_output(['tasklist'], shell=True).decode()
            return script_name in result
        else:  # Unix/Linux/Termux
            result = subprocess.check_output(['ps', 'aux']).decode()
            return script_name in result
    except Exception:
        return False 