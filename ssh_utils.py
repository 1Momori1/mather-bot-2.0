import paramiko
import os

def start_ssh_bot(host, port, user, password, script_path, ssh_key_path=None):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if ssh_key_path:
            ssh.connect(host, port=port, username=user, key_filename=ssh_key_path)
        else:
            ssh.connect(host, port=port, username=user, password=password)
        ssh.exec_command(f'nohup python3 {script_path} > /dev/null 2>&1 &')
        ssh.close()
        return True, None
    except Exception as e:
        return False, str(e)

def stop_ssh_bot(host, port, user, password, name, ssh_key_path=None):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if ssh_key_path:
            ssh.connect(host, port=port, username=user, key_filename=ssh_key_path)
        else:
            ssh.connect(host, port=port, username=user, password=password)
        ssh.exec_command(f'pkill -f "{name}"')
        ssh.close()
        return True, None
    except Exception as e:
        return False, str(e)

def is_ssh_bot_running(host, port, user, password, script_path, ssh_key_path=None):
    script_name = os.path.basename(script_path)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if ssh_key_path:
            ssh.connect(host, port=port, username=user, key_filename=ssh_key_path)
        else:
            ssh.connect(host, port=port, username=user, password=password)
        stdin, stdout, stderr = ssh.exec_command(f'ps aux | grep {script_name} | grep -v grep')
        output = stdout.read().decode()
        ssh.close()
        return script_name in output
    except Exception:
        return False 