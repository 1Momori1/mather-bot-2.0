import telebot
from telebot import types
import sqlite3
import subprocess
import sys
import os

from handlers import bot
from db import get_bots, update_bot_status
from local_utils import is_local_bot_running, start_local_bot, stop_local_bot
from ssh_utils import is_ssh_bot_running, start_ssh_bot, stop_ssh_bot
from config import WHITE_LIST_IDS
import threading
import time
from datetime import datetime

def monitor_bots():
    while True:
        bots = get_bots()
        for bot_row in bots:
            bot_id, name, script_path, status, bot_type, host, port, user, ssh_key_path, group_name, schedule = bot_row
            # Проверка живости (как раньше)
            if bot_type == 'local':
                real_running = is_local_bot_running(script_path)
            else:
                full_row = bot_row if len(bot_row) > 11 else None
                if not full_row:
                    continue
                _, _, _, _, _, _, _, _, password, ssh_key_path, _, schedule = full_row
                real_running = is_ssh_bot_running(host, port, user, password, script_path, ssh_key_path)
            if status == 'running' and not real_running:
                for admin_id in WHITE_LIST_IDS:
                    try:
                        bot.send_message(admin_id, f'❗️ Бот "{name}" неожиданно завершил работу!')
                    except Exception:
                        pass
                update_bot_status(bot_id, 'stopped')
            if status == 'stopped' and real_running:
                update_bot_status(bot_id, 'running')
            # --- Планировщик ---
            if schedule:
                now = datetime.now().strftime('%H:%M')
                if now == schedule:
                    if not real_running:
                        # запуск по расписанию
                        if bot_type == 'local':
                            start_local_bot(script_path)
                        else:
                            full_row = bot_row if len(bot_row) > 11 else None
                            if not full_row:
                                continue
                            _, _, _, _, _, _, _, _, password, ssh_key_path, _, schedule = full_row
                            start_ssh_bot(host, port, user, password, script_path, ssh_key_path)
                        update_bot_status(bot_id, 'running')
                        for admin_id in WHITE_LIST_IDS:
                            try:
                                bot.send_message(admin_id, f'⏰ Бот "{name}" запущен по расписанию ({schedule})')
                            except Exception:
                                pass
        time.sleep(60)

if __name__ == '__main__':
    print('✅ Telegram-бот-менеджер успешно запущен! Ожидаю команды в Telegram...')
    threading.Thread(target=monitor_bots, daemon=True).start()
    bot.polling(none_stop=True) 