import telebot
from telebot import types
from db import init_db, add_local_bot, add_ssh_bot, get_bots, get_bot_by_id, update_bot_status, delete_bot
from local_utils import start_local_bot, stop_local_bot, is_local_bot_running
from ssh_utils import start_ssh_bot, stop_ssh_bot, is_ssh_bot_running
from config import API_TOKEN, WHITE_LIST_IDS

bot = telebot.TeleBot(API_TOKEN)

init_db()

def check_access(message_or_call):
    user_id = message_or_call.from_user.id
    if user_id not in WHITE_LIST_IDS:
        if hasattr(message_or_call, 'message'):
            bot.send_message(message_or_call.message.chat.id, '⛔️ Доступ запрещён. Обратитесь к администратору.')
        else:
            bot.send_message(message_or_call.chat.id, '⛔️ Доступ запрещён. Обратитесь к администратору.')
        return False
    return True

def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('➕ Добавить бота', callback_data='add_bot'))
    markup.add(types.InlineKeyboardButton('📋 Список ботов', callback_data='list_bots'))
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
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Локальный', callback_data=f'type_local_{name}'))
    markup.add(types.InlineKeyboardButton('SSH', callback_data=f'type_ssh_{name}'))
    bot.send_message(message.chat.id, 'Выберите тип бота:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
def process_bot_type(call):
    if not check_access(call):
        return
    data = call.data.split('_')
    bot_type = data[1]
    name = '_'.join(data[2:])
    if bot_type == 'local':
        msg = bot.send_message(call.message.chat.id, 'Введите путь к скрипту бота:')
        bot.register_next_step_handler(msg, lambda m: process_bot_path(m, name, 'local'))
    else:
        msg = bot.send_message(call.message.chat.id, 'Введите host (IP) устройства:')
        bot.register_next_step_handler(msg, lambda m: process_ssh_host(m, name))

def process_ssh_host(message, name):
    if not check_access(message):
        return
    host = message.text.strip()
    msg = bot.send_message(message.chat.id, 'Введите порт (обычно 22):')
    bot.register_next_step_handler(msg, lambda m: process_ssh_port(m, name, host))

def process_ssh_port(message, name, host):
    if not check_access(message):
        return
    try:
        port = int(message.text.strip())
    except:
        port = 22
    msg = bot.send_message(message.chat.id, 'Введите логин:')
    bot.register_next_step_handler(msg, lambda m: process_ssh_user(m, name, host, port))

def process_ssh_user(message, name, host, port):
    if not check_access(message):
        return
    user = message.text.strip()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Пароль', callback_data=f'ssh_auth_pass_{name}_{host}_{port}_{user}'))
    markup.add(types.InlineKeyboardButton('SSH-ключ', callback_data=f'ssh_auth_key_{name}_{host}_{port}_{user}'))
    bot.send_message(message.chat.id, 'Выберите способ аутентификации:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('ssh_auth_pass_'))
def ssh_auth_pass_callback(call):
    if not check_access(call):
        return
    _, _, name, host, port, user = call.data.split('_', 5)
    msg = bot.send_message(call.message.chat.id, 'Введите пароль:')
    bot.register_next_step_handler(msg, lambda m: process_ssh_password(m, name, host, int(port), user))

@bot.callback_query_handler(func=lambda call: call.data.startswith('ssh_auth_key_'))
def ssh_auth_key_callback(call):
    if not check_access(call):
        return
    _, _, name, host, port, user = call.data.split('_', 5)
    msg = bot.send_message(call.message.chat.id, 'Введите путь к приватному ключу (например, /home/user/.ssh/id_rsa):')
    bot.register_next_step_handler(msg, lambda m: process_ssh_key(m, name, host, int(port), user))

def process_ssh_password(message, name, host, port, user):
    if not check_access(message):
        return
    password = message.text.strip()
    msg = bot.send_message(message.chat.id, 'Введите путь к скрипту на удалённом устройстве:')
    bot.register_next_step_handler(msg, lambda m: process_bot_path(m, name, 'ssh', host, port, user, password, None))

def process_ssh_key(message, name, host, port, user):
    if not check_access(message):
        return
    ssh_key_path = message.text.strip()
    msg = bot.send_message(message.chat.id, 'Введите путь к скрипту на удалённом устройстве:')
    bot.register_next_step_handler(msg, lambda m: process_bot_path(m, name, 'ssh', host, port, user, None, ssh_key_path))

def process_bot_path(message, name, bot_type, host=None, port=None, user=None, password=None, ssh_key_path=None):
    if not check_access(message):
        return
    path = message.text.strip()
    try:
        if bot_type == 'local':
            add_local_bot(name, path)
        else:
            add_ssh_bot(name, path, host, port, user, password, ssh_key_path)
        bot.send_message(message.chat.id, f'✅ Бот "{name}" добавлен!')
    except Exception as e:
        bot.send_message(message.chat.id, f'❌ Ошибка: {e}')
    bot.send_message(message.chat.id, 'Меню:', reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == 'list_bots')
def show_bots_list_callback(call):
    if not check_access(call):
        return
    show_bots_list(call.message)

def show_bots_list(message):
    if not check_access(message):
        return
    bots = get_bots()
    if not bots:
        bot.send_message(message.chat.id, 'Боты не добавлены.', reply_markup=main_menu())
        return
    for bot_row in bots:
        bot_id, name, script_path, status, bot_type, host, port, user, ssh_key_path = bot_row
        if bot_type == 'local':
            real_status = 'running' if is_local_bot_running(script_path) else 'stopped'
        else:
            full_row = get_bot_by_id(bot_id)
            _, _, _, _, _, _, _, _, password, ssh_key_path = full_row
            real_status = 'running' if is_ssh_bot_running(host, port, user, password, script_path, ssh_key_path) else 'stopped'
        text = f"🤖 <b>{name}</b>\nПуть: <code>{script_path}</code>\nСтатус: <b>{real_status}</b>\nТип: <b>{bot_type}</b>"
        markup = types.InlineKeyboardMarkup()
        if real_status == 'stopped':
            markup.add(types.InlineKeyboardButton('▶️ Запустить', callback_data=f'start_{bot_id}'))
        else:
            markup.add(types.InlineKeyboardButton('⏹️ Остановить', callback_data=f'confirm_stop_{bot_id}'))
            markup.add(types.InlineKeyboardButton('🔄 Перезапустить', callback_data=f'confirm_restart_{bot_id}'))
        markup.add(types.InlineKeyboardButton('🗑️ Удалить', callback_data=f'confirm_delete_{bot_id}'))
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    bot.send_message(message.chat.id, 'Меню:', reply_markup=main_menu())

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
    _, name, script_path, status, bot_type, host, port, user, password, ssh_key_path = bot_row
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
    _, name, script_path, status, bot_type, host, port, user, password, ssh_key_path = bot_row
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