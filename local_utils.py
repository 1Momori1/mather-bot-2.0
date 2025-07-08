import subprocess
import sys
import os


def start_local_bot(script_path):
    try:
        # Лог сохраняется в logs/<имя_бота>.log
        script_name = os.path.basename(script_path)
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f'{script_name}.log')
        with open(log_path, 'a'):
            pass  # создать файл, если не существует
        p = subprocess.Popen([sys.executable, script_path], stdout=open(log_path, 'a'), stderr=subprocess.STDOUT)
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


def get_local_bot_log(script_path, lines=20):
    script_name = os.path.basename(script_path)
    log_path = os.path.join('logs', f'{script_name}.log')
    if not os.path.exists(log_path):
        return 'Лог-файл не найден.'
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        log_lines = f.readlines()
    return ''.join(log_lines[-lines:]) if log_lines else 'Лог пуст.' 