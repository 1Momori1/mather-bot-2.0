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