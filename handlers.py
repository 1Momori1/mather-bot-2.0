import telebot
from telebot import types
import json
from db import init_db, add_local_bot, add_ssh_bot, get_bots, get_bot_by_id, update_bot_status, delete_bot, update_bot_schedule
from local_utils import start_local_bot, stop_local_bot, is_local_bot_running, get_local_bot_log
from ssh_utils import start_ssh_bot, stop_ssh_bot, is_ssh_bot_running, get_ssh_bot_log
from config import API_TOKEN, WHITE_LIST_IDS

bot = telebot.TeleBot(API_TOKEN)

init_db()

def notify_admins(text):
    for admin_id in WHITE_LIST_IDS:
        try:
            bot.send_message(admin_id, text, parse_mode='HTML')
        except Exception:
            pass

def check_access(message_or_call):
    user_id = message_or_call.from_user.id
    if user_id not in WHITE_LIST_IDS:
        if hasattr(message_or_call, 'message'):
            bot.send_message(message_or_call.message.chat.id, '⛔️ Доступ запрещён. Обратитесь к администратору.')
        else:
            bot.send_message(message_or_call.chat.id, '⛔️ Доступ запрещён. Обратитесь к администратору.')
        notify_admins(f'⚠️ Попытка неавторизованного доступа!\nID: <code>{user_id}</code>')
        return False
    return True

def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('➕ Добавить бота', callback_data='add_bot'))
    markup.add(types.InlineKeyboardButton('📋 Все боты', callback_data='list_bots_all'))
    markup.add(types.InlineKeyboardButton('🖥️ Локальные', callback_data='list_bots_local'))
    markup.add(types.InlineKeyboardButton('🌐 SSH', callback_data='list_bots_ssh'))
    markup.add(types.InlineKeyboardButton('⏰ Экспорт', callback_data='export_bots'))
    markup.add(types.InlineKeyboardButton('📥 Импорт', callback_data='import_bots'))
    markup.add(types.InlineKeyboardButton('ℹ️ Помощь', callback_data='help'))
    return markup

@bot.message_handler(commands=['start'])
def start_message(message):
    if not check_access(message):
        return
    bot.send_message(message.chat.id, 'Добро пожаловать! Менеджер ботов:', reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == 'add_bot')
def add_bot_callback(call):
    if not check_access(call):
        return
    msg = bot.send_message(call.message.chat.id, 'Введите имя нового бота:')
    bot.register_next_step_handler(msg, process_bot_name)

def process_bot_name(message):
    name = message.text.strip()
    msg = bot.send_message(message.chat.id, 'Введите название группы/устройства (например, Ноутбук, Телефон):')
    bot.register_next_step_handler(msg, lambda m: process_bot_group(m, name))

def process_bot_group(message, name):
    group_name = message.text.strip()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Локальный', callback_data=f'type_local_{name}_{group_name}'))
    markup.add(types.InlineKeyboardButton('SSH', callback_data=f'type_ssh_{name}_{group_name}'))
    bot.send_message(message.chat.id, 'Выберите тип бота:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
def process_bot_type(call):
    data = call.data.split('_')
    bot_type = data[1]
    name = data[2]
    group_name = '_'.join(data[3:])
    if bot_type == 'local':
        msg = bot.send_message(call.message.chat.id, 'Введите путь к скрипту бота:')
        bot.register_next_step_handler(msg, lambda m: process_bot_path(m, name, 'local', None, None, None, None, None, group_name))
    else:
        msg = bot.send_message(call.message.chat.id, 'Введите host (IP) устройства:')
        bot.register_next_step_handler(msg, lambda m: process_ssh_host(m, name, group_name))

def process_ssh_host(message, name, group_name):
    host = message.text.strip()
    msg = bot.send_message(message.chat.id, 'Введите порт (обычно 22):')
    bot.register_next_step_handler(msg, lambda m: process_ssh_port(m, name, host, group_name))

def process_ssh_port(message, name, host, group_name):
    try:
        port = int(message.text.strip())
    except:
        port = 22
    msg = bot.send_message(message.chat.id, 'Введите логин:')
    bot.register_next_step_handler(msg, lambda m: process_ssh_user(m, name, host, port, group_name))

def process_ssh_user(message, name, host, port, group_name):
    user = message.text.strip()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Пароль', callback_data=f'ssh_auth_pass_{name}_{host}_{port}_{user}_{group_name}'))
    markup.add(types.InlineKeyboardButton('SSH-ключ', callback_data=f'ssh_auth_key_{name}_{host}_{port}_{user}_{group_name}'))
    bot.send_message(message.chat.id, 'Выберите способ аутентификации:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('ssh_auth_pass_'))
def ssh_auth_pass_callback(call):
    _, _, name, host, port, user, group_name = call.data.split('_', 6)
    msg = bot.send_message(call.message.chat.id, 'Введите пароль:')
    bot.register_next_step_handler(msg, lambda m: process_ssh_password(m, name, host, int(port), user, group_name))

@bot.callback_query_handler(func=lambda call: call.data.startswith('ssh_auth_key_'))
def ssh_auth_key_callback(call):
    _, _, name, host, port, user, group_name = call.data.split('_', 6)
    msg = bot.send_message(call.message.chat.id, 'Введите путь к приватному ключу (например, /home/user/.ssh/id_rsa):')
    bot.register_next_step_handler(msg, lambda m: process_ssh_key(m, name, host, int(port), user, group_name))

def process_ssh_password(message, name, host, port, user, group_name):
    password = message.text.strip()
    msg = bot.send_message(message.chat.id, 'Введите путь к скрипту на удалённом устройстве:')
    bot.register_next_step_handler(msg, lambda m: process_bot_path(m, name, 'ssh', host, port, user, password, None, group_name))

def process_ssh_key(message, name, host, port, user, group_name):
    ssh_key_path = message.text.strip()
    msg = bot.send_message(message.chat.id, 'Введите путь к скрипту на удалённом устройстве:')
    bot.register_next_step_handler(msg, lambda m: process_bot_path(m, name, 'ssh', host, port, user, None, ssh_key_path, group_name))

def process_bot_path(message, name, bot_type, host=None, port=None, user=None, password=None, ssh_key_path=None, group_name=None):
    path = message.text.strip()
    try:
        if bot_type == 'local':
            add_local_bot(name, path, group_name)
        else:
            add_ssh_bot(name, path, host, port, user, password, ssh_key_path, group_name)
        bot.send_message(message.chat.id, f'✅ Бот "{name}" добавлен!')
    except Exception as e:
        bot.send_message(message.chat.id, f'❌ Ошибка: {e}')
    bot.send_message(message.chat.id, 'Меню:', reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == 'list_bots')
def show_bots_list_callback(call):
    if not check_access(call):
        return
    show_bots_list(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'list_bots_all')
def show_all_bots_callback(call):
    show_bots_list(call.message, filter_type='all')

@bot.callback_query_handler(func=lambda call: call.data == 'list_bots_local')
def show_local_bots_callback(call):
    show_bots_list(call.message, filter_type='local')

@bot.callback_query_handler(func=lambda call: call.data == 'list_bots_ssh')
def show_ssh_bots_callback(call):
    show_bots_list(call.message, filter_type='ssh')

def show_bots_list(message, filter_type='all'):
    if not check_access(message):
        return
    bots = get_bots()
    if not bots:
        bot.send_message(message.chat.id, 'Боты не добавлены.', reply_markup=main_menu())
        return
    # Группировка по group_name
    groups = {}
    for bot_row in bots:
        bot_id, name, script_path, status, bot_type, host, port, user, ssh_key_path, group_name, schedule = bot_row
        if filter_type != 'all' and bot_type != filter_type:
            continue
        group = group_name or 'Без группы'
        if group not in groups:
            groups[group] = []
        groups[group].append(bot_row)
    for group, group_bots in groups.items():
        bot.send_message(message.chat.id, f'📦 <b>{group}</b>', parse_mode='HTML')
        for bot_row in group_bots:
            bot_id, name, script_path, status, bot_type, host, port, user, ssh_key_path, group_name, schedule = bot_row
            if bot_type == 'local':
                real_status = 'running' if is_local_bot_running(script_path) else 'stopped'
            else:
                full_row = get_bot_by_id(bot_id)
                _, _, _, _, _, _, _, _, password, ssh_key_path, _, schedule = full_row
                real_status = 'running' if is_ssh_bot_running(host, port, user, password, script_path, ssh_key_path) else 'stopped'
            text = f"🤖 <b>{name}</b>\nПуть: <code>{script_path}</code>\nСтатус: <b>{real_status}</b>\nТип: <b>{bot_type}</b>"
            if schedule:
                text += f"\n⏰ <b>Расписание:</b> {schedule}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('📄 Логи', callback_data=f'logs_{bot_id}'))
            markup.add(types.InlineKeyboardButton('⏰ Расписание', callback_data=f'schedule_{bot_id}'))
            if real_status == 'stopped':
                markup.add(types.InlineKeyboardButton('▶️ Запустить', callback_data=f'start_{bot_id}'))
            else:
                markup.add(types.InlineKeyboardButton('⏹️ Остановить', callback_data=f'confirm_stop_{bot_id}'))
                markup.add(types.InlineKeyboardButton('🔄 Перезапустить', callback_data=f'confirm_restart_{bot_id}'))
            markup.add(types.InlineKeyboardButton('🗑️ Удалить', callback_data=f'confirm_delete_{bot_id}'))
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    bot.send_message(message.chat.id, 'Меню:', reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith('logs_'))
def logs_callback(call):
    bot_id = int(call.data.split('_')[1])
    bot_row = get_bot_by_id(bot_id)
    if not bot_row:
        bot.send_message(call.message.chat.id, '❌ Бот не найден')
        return
    _, name, script_path, _, bot_type, host, port, user, password, ssh_key_path, _ = bot_row
    if bot_type == 'local':
        log_text = get_local_bot_log(script_path)
    else:
        log_text = get_ssh_bot_log(host, port, user, password, script_path, ssh_key_path)
    if not log_text:
        log_text = 'Лог пуст.'
    # Ограничим длину сообщения Telegram (4096 символов)
    if len(log_text) > 4000:
        log_text = log_text[-4000:]
    bot.send_message(call.message.chat.id, f'📄 Логи бота <b>{name}</b>:\n<pre>{log_text}</pre>', parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('schedule_'))
def schedule_callback(call):
    bot_id = int(call.data.split('_')[1])
    bot_row = get_bot_by_id(bot_id)
    if not bot_row:
        bot.send_message(call.message.chat.id, '❌ Бот не найден')
        return
    _, name, *_ , schedule = bot_row
    msg = f'Текущее расписание для <b>{name}</b>: {schedule or "не задано"}\n\nВведите новое расписание в формате HH:MM (например, 09:00),\nили отправьте "удалить", чтобы убрать расписание.'
    bot.send_message(call.message.chat.id, msg, parse_mode='HTML')
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: process_schedule_input(m, bot_id))

def process_schedule_input(message, bot_id):
    text = message.text.strip()
    if text.lower() == 'удалить':
        update_bot_schedule(bot_id, None)
        bot.send_message(message.chat.id, 'Расписание удалено.')
    else:
        # простая валидация HH:MM
        import re
        if re.match(r'^\d{2}:\d{2}$', text):
            update_bot_schedule(bot_id, text)
            bot.send_message(message.chat.id, f'Расписание установлено: {text}')
        else:
            bot.send_message(message.chat.id, 'Некорректный формат. Введите время в формате HH:MM или "удалить".')
            bot.register_next_step_handler_by_chat_id(message.chat.id, lambda m: process_schedule_input(m, bot_id))
    show_bots_list(message)

# --- Подтверждения ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_stop_'))
def confirm_stop_callback(call):
    bot_id = int(call.data.split('_')[2])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('✅ Да, остановить', callback_data=f'stop_{bot_id}'))
    markup.add(types.InlineKeyboardButton('❌ Нет', callback_data='cancel'))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_delete_'))
def confirm_delete_callback(call):
    bot_id = int(call.data.split('_')[2])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('✅ Да, удалить', callback_data=f'delete_{bot_id}'))
    markup.add(types.InlineKeyboardButton('❌ Нет', callback_data='cancel'))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_restart_'))
def confirm_restart_callback(call):
    bot_id = int(call.data.split('_')[2])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('✅ Да, перезапустить', callback_data=f'restart_{bot_id}'))
    markup.add(types.InlineKeyboardButton('❌ Нет', callback_data='cancel'))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel_callback(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.answer_callback_query(call.id, 'Действие отменено')

# --- Перезапуск ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('restart_'))
def restart_bot_callback(call):
    bot_id = int(call.data.split('_')[1])
    stop_bot(call.message, bot_id)
    start_bot(call.message, bot_id)
    bot.answer_callback_query(call.id, 'Бот перезапущен!')
    bot_row = get_bot_by_id(bot_id)
    if bot_row:
        _, name, *_ = bot_row
        notify_admins(f'🔄 <b>Бот "{name}"</b> перезапущен пользователем <code>{call.from_user.id}</code>')

@bot.callback_query_handler(func=lambda call: call.data.startswith('start_'))
def start_bot_callback(call):
    if not check_access(call):
        return
    bot_id = int(call.data.split('_')[1])
    start_bot(call.message, bot_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('stop_'))
def stop_bot_callback(call):
    if not check_access(call):
        return
    bot_id = int(call.data.split('_')[1])
    stop_bot(call.message, bot_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def delete_bot_callback(call):
    if not check_access(call):
        return
    bot_id = int(call.data.split('_')[1])
    delete_bot_handler(call.message, bot_id)

def start_bot(message, bot_id):
    if not check_access(message):
        return
    bot_row = get_bot_by_id(bot_id)
    if not bot_row:
        bot.send_message(message.chat.id, '❌ Бот не найден')
        return
    _, name, script_path, status, bot_type, host, port, user, password, ssh_key_path, group_name = bot_row
    if status == 'running':
        bot.send_message(message.chat.id, f'Бот "{name}" уже запущен!')
        return
    if bot_type == 'local':
        ok, err = start_local_bot(script_path)
    else:
        ok, err = start_ssh_bot(host, port, user, password, script_path, ssh_key_path)
    if ok:
        update_bot_status(bot_id, 'running')
        bot.send_message(message.chat.id, f'▶️ Бот "{name}" запущен!')
        notify_admins(f'▶️ <b>Бот "{name}"</b> запущен пользователем <code>{message.from_user.id}</code>')
    else:
        bot.send_message(message.chat.id, f'❌ Ошибка запуска: {err}')
    show_bots_list(message)

def stop_bot(message, bot_id):
    if not check_access(message):
        return
    bot_row = get_bot_by_id(bot_id)
    if not bot_row:
        bot.send_message(message.chat.id, '❌ Бот не найден')
        return
    _, name, script_path, status, bot_type, host, port, user, password, ssh_key_path, group_name = bot_row
    if status == 'stopped':
        bot.send_message(message.chat.id, f'Бот "{name}" уже остановлен!')
        return
    if bot_type == 'local':
        ok, err = stop_local_bot(name)
    else:
        ok, err = stop_ssh_bot(host, port, user, password, name, ssh_key_path)
    if ok:
        update_bot_status(bot_id, 'stopped')
        bot.send_message(message.chat.id, f'⏹️ Бот "{name}" остановлен!')
        notify_admins(f'⏹️ <b>Бот "{name}"</b> остановлен пользователем <code>{message.from_user.id}</code>')
    else:
        bot.send_message(message.chat.id, f'❌ Ошибка остановки: {err}')
    show_bots_list(message)

def delete_bot_handler(message, bot_id):
    if not check_access(message):
        return
    bot_row = get_bot_by_id(bot_id)
    if not bot_row:
        bot.send_message(message.chat.id, '❌ Бот не найден')
        return
    _, name, *_ = bot_row
    delete_bot(bot_id)
    bot.send_message(message.chat.id, f'🗑️ Бот "{name}" удалён!')
    show_bots_list(message)

@bot.callback_query_handler(func=lambda call: call.data == 'export_bots')
def export_bots_callback(call):
    bots = get_bots()
    bots_data = []
    for b in bots:
        bots_data.append({
            'name': b[1], 'script_path': b[2], 'type': b[4], 'host': b[5], 'port': b[6], 'user': b[7],
            'ssh_key_path': b[8], 'group_name': b[9], 'schedule': b[10]
        })
    with open('bots_export.json', 'w', encoding='utf-8') as f:
        json.dump(bots_data, f, ensure_ascii=False, indent=2)
    with open('bots_export.json', 'rb') as f:
        bot.send_document(call.message.chat.id, f, caption='Экспорт всех ботов (JSON)')

@bot.callback_query_handler(func=lambda call: call.data == 'import_bots')
def import_bots_callback(call):
    bot.send_message(call.message.chat.id, 'Отправьте файл JSON для импорта ботов.')
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_import_file)

def process_import_file(message):
    if not message.document:
        bot.send_message(message.chat.id, 'Пришлите файл в формате JSON.')
        return
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    try:
        bots_data = json.loads(downloaded_file.decode('utf-8'))
        for b in bots_data:
            if b.get('type') == 'local':
                add_local_bot(b['name'], b['script_path'], b.get('group_name'), b.get('schedule'))
            else:
                add_ssh_bot(b['name'], b['script_path'], b.get('host'), b.get('port'), b.get('user'), None, b.get('ssh_key_path'), b.get('group_name'), b.get('schedule'))
        bot.send_message(message.chat.id, f'Импортировано {len(bots_data)} ботов.')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка импорта: {e}')
    show_bots_list(message)

@bot.callback_query_handler(func=lambda call: call.data == 'help')
def help_callback(call):
    help_text = (
        'ℹ️ <b>Справка по менеджеру ботов</b>\n\n'
        '• <b>➕ Добавить бота</b> — добавить нового бота (локальный или SSH, с указанием группы/устройства).\n'
        '• <b>📋 Все боты</b> — показать всех ботов с группировкой по устройствам.\n'
        '• <b>🖥️ Локальные</b> — только локальные боты.\n'
        '• <b>🌐 SSH</b> — только SSH-боты.\n'
        '• <b>📄 Логи</b> — последние строки лога выбранного бота.\n'
        '• <b>▶️ Запустить</b> — запустить выбранного бота.\n'
        '• <b>⏹️ Остановить</b> — остановить бота (с подтверждением).\n'
        '• <b>🔄 Перезапустить</b> — перезапустить бота (с подтверждением).\n'
        '• <b>🗑️ Удалить</b> — удалить бота (с подтверждением).\n'
        '\n'
        '<b>Группы</b> — позволяют удобно разделять ботов по устройствам или задачам.\n'
        '\n'
        'Доступ к управлению имеют только пользователи из белого списка.\n'
        '\n'
        'Все действия доступны только через кнопки!\n'
        '\n'
        'Если появились вопросы или нужна помощь — обратись к администратору.'
    )
    bot.send_message(call.message.chat.id, help_text, parse_mode='HTML') 