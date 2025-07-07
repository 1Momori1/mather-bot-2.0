import asyncio
import subprocess
import sys

# Словарь для хранения процессов: {bot_id: process}
processes = {}

async def start_bot(bot_id, script_path):
    if bot_id in processes and processes[bot_id].poll() is None:
        return False  # Уже запущен
    # Запуск через PowerShell
    process = subprocess.Popen([
        sys.executable, script_path
    ], creationflags=subprocess.CREATE_NEW_CONSOLE)
    processes[bot_id] = process
    return True

async def stop_bot(bot_id):
    process = processes.get(bot_id)
    if process and process.poll() is None:
        process.terminate()
        process.wait()
        return True
    return False

async def restart_bot(bot_id, script_path):
    await stop_bot(bot_id)
    await asyncio.sleep(1)
    return await start_bot(bot_id, script_path) 