import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiosqlite
from db import init_db, get_bots, add_bot, update_bot_status, delete_bot, get_bot_stats, backup_database, get_recent_activity, get_bot_by_id
from process_manager import start_bot, stop_bot, restart_bot
from logger import log_action, log_error, log_system, log_bot_status
from system_info import format_system_info, get_uptime
import config
import os

# API_TOKEN теперь в config.py

bot = Bot(token=config.API_TOKEN)
dp = Dispatcher()

# --- FSM для добавления бота ---
class AddBotStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_script_path = State()
    waiting_for_token = State()

# --- FSM для подтверждения удаления ---
class DeleteBotStates(StatesGroup):
    waiting_for_confirmation = State()

# --- Клавиатура главного меню ---
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🤖 Добавить бота", callback_data="add_bot")
    builder.button(text="📊 Статистика", callback_data="stats")
    builder.button(text="🖥️ Система", callback_data="system")
    builder.button(text="📋 Список ботов", callback_data="list_bots")
    builder.button(text="💾 Резервная копия", callback_data="backup")
    builder.adjust(2)
    return builder.as_markup()

# --- Клавиатура для управления ботом ---
def get_bot_control_keyboard(bot_id, status):
    builder = InlineKeyboardBuilder()
    if status == 'stopped':
        builder.button(text="▶️ Запустить", callback_data=f"start_{bot_id}")
    else:
        builder.button(text="⏹️ Остановить", callback_data=f"stop_{bot_id}")
        builder.button(text="🔄 Перезапустить", callback_data=f"restart_{bot_id}")
    
    builder.button(text="🗑️ Удалить", callback_data=f"delete_{bot_id}")
    builder.button(text="📈 Информация", callback_data=f"info_{bot_id}")
    builder.adjust(2)
    return builder.as_markup()

# --- Клавиатура отмены ---
def get_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_add")
    return builder.as_markup()

# --- Клавиатура подтверждения удаления ---
def get_confirm_delete_keyboard(bot_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"confirm_delete_{bot_id}")
    builder.button(text="❌ Отмена", callback_data="cancel_delete")
    builder.adjust(2)
    return builder.as_markup()

async def show_bots_menu(message):
    bots = await get_bots()
    if not bots:
        await message.answer('🤖 Боты не добавлены.', reply_markup=get_main_menu())
        return
    
    await message.answer('📋 **Список ваших ботов:**')
    for bot_data in bots:
        bot_id, name, script_path, token, status, created_at, last_started, start_count = bot_data
        text = f"""
🤖 **{name}**
📁 Путь: `{script_path}`
📊 Статус: **{status}**
📅 Создан: {created_at}
🚀 Запусков: {start_count}
"""
        if last_started:
            text += f"⏰ Последний запуск: {last_started}"
        
        await message.answer(text, reply_markup=get_bot_control_keyboard(bot_id, status), parse_mode='Markdown')
    
    await message.answer('🎛️ **Главное меню:**', reply_markup=get_main_menu(), parse_mode='Markdown')

async def show_stats(message):
    stats = await get_bot_stats()
    text = f"""
📊 **Статистика ботов:**

🤖 Всего ботов: **{stats['total_bots']}**
▶️ Запущено: **{stats['running_bots']}**
⏹️ Остановлено: **{stats['stopped_bots']}**
"""
    
    if stats['most_active']:
        name, count = stats['most_active']
        text += f"🏆 Самый активный: **{name}** ({count} запусков)"
    
    await message.answer(text, reply_markup=get_main_menu(), parse_mode='Markdown')

async def show_system_info(message):
    system_info = format_system_info()
    uptime = get_uptime()
    
    text = f"{system_info}\n⏱️ Время работы системы: **{uptime}**"
    
    await message.answer(text, reply_markup=get_main_menu(), parse_mode='Markdown')

async def show_bot_info(bot_id, message):
    bot_data = await get_bot_by_id(bot_id)
    if not bot_data:
        await message.answer('❌ Бот не найден')
        return
    
    bot_id, name, script_path, token, status, created_at, last_started, start_count = bot_data
    
    text = f"""
🤖 **Информация о боте:**

📝 **Имя:** {name}
📁 **Путь:** `{script_path}`
📊 **Статус:** {status}
📅 **Создан:** {created_at}
🚀 **Запусков:** {start_count}
"""
    
    if last_started:
        text += f"⏰ **Последний запуск:** {last_started}"
    
    if token:
        text += f"\n🔑 **Токен:** `{token[:10]}...`"
    
    await message.answer(text, reply_markup=get_main_menu(), parse_mode='Markdown')

@dp.message()
async def cmd_start(message: types.Message):
    if message.text == '/start':
        log_action("start", f"User {message.from_user.id} started bot")
        await show_bots_menu(message)

@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    
    # Проверяем, что callback_query.data не None
    if not callback_query.data:
        return
    
    if callback_query.data == 'add_bot':
        log_action("add_bot", f"User {callback_query.from_user.id} started adding bot")
        await state.set_state(AddBotStates.waiting_for_name)
        await bot.send_message(
            callback_query.from_user.id, 
            '📝 Введите имя для нового бота:',
            reply_markup=get_cancel_keyboard()
        )
    
    elif callback_query.data == 'stats':
        log_action("stats", f"User {callback_query.from_user.id} requested stats")
        await show_stats(callback_query.message)
    
    elif callback_query.data == 'system':
        log_action("system", f"User {callback_query.from_user.id} requested system info")
        await show_system_info(callback_query.message)
    
    elif callback_query.data == 'list_bots':
        log_action("list_bots", f"User {callback_query.from_user.id} requested bot list")
        await show_bots_menu(callback_query.message)
    
    elif callback_query.data == 'backup':
        log_action("backup", f"User {callback_query.from_user.id} requested backup")
        backup_path = await backup_database()
        if backup_path:
            await bot.send_message(callback_query.from_user.id, f'✅ Резервная копия создана: `{backup_path}`', parse_mode='Markdown')
        else:
            await bot.send_message(callback_query.from_user.id, '❌ Ошибка создания резервной копии')
    
    elif callback_query.data == 'cancel_add':
        await state.clear()
        await bot.send_message(callback_query.from_user.id, '❌ Добавление бота отменено.')
    
    elif callback_query.data.startswith('start_'):
        try:
            bot_id = int(callback_query.data.split('_')[1])
        except (ValueError, IndexError):
            await bot.send_message(callback_query.from_user.id, '❌ Ошибка: неверный ID бота')
            return
            
        bots = await get_bots()
        target_bot = None
        for b in bots:
            if b[0] == bot_id:
                target_bot = b
                break
        
        if target_bot:
            log_bot_status(target_bot[1], "start_attempt", f"User {callback_query.from_user.id}")
            success = await start_bot(bot_id, target_bot[2])
            if success:
                await update_bot_status(bot_id, 'running')
                log_bot_status(target_bot[1], "started", "success")
                await bot.send_message(callback_query.from_user.id, f'✅ Бот "{target_bot[1]}" запущен!')
            else:
                log_bot_status(target_bot[1], "start_failed", "error")
                await bot.send_message(callback_query.from_user.id, f'❌ Ошибка запуска бота "{target_bot[1]}"')
        else:
            await bot.send_message(callback_query.from_user.id, '❌ Бот не найден')
    
    elif callback_query.data.startswith('stop_'):
        try:
            bot_id = int(callback_query.data.split('_')[1])
        except (ValueError, IndexError):
            await bot.send_message(callback_query.from_user.id, '❌ Ошибка: неверный ID бота')
            return
            
        bots = await get_bots()
        target_bot = None
        for b in bots:
            if b[0] == bot_id:
                target_bot = b
                break
        
        if target_bot:
            log_bot_status(target_bot[1], "stop_attempt", f"User {callback_query.from_user.id}")
            success = await stop_bot(bot_id)
            if success:
                await update_bot_status(bot_id, 'stopped')
                log_bot_status(target_bot[1], "stopped", "success")
                await bot.send_message(callback_query.from_user.id, f'⏹️ Бот "{target_bot[1]}" остановлен!')
            else:
                log_bot_status(target_bot[1], "stop_failed", "error")
                await bot.send_message(callback_query.from_user.id, f'❌ Ошибка остановки бота "{target_bot[1]}"')
        else:
            await bot.send_message(callback_query.from_user.id, '❌ Бот не найден')
    
    elif callback_query.data.startswith('restart_'):
        try:
            bot_id = int(callback_query.data.split('_')[1])
        except (ValueError, IndexError):
            await bot.send_message(callback_query.from_user.id, '❌ Ошибка: неверный ID бота')
            return
            
        bots = await get_bots()
        target_bot = None
        for b in bots:
            if b[0] == bot_id:
                target_bot = b
                break
        
        if target_bot:
            log_bot_status(target_bot[1], "restart_attempt", f"User {callback_query.from_user.id}")
            success = await restart_bot(bot_id, target_bot[2])
            if success:
                await update_bot_status(bot_id, 'running')
                log_bot_status(target_bot[1], "restarted", "success")
                await bot.send_message(callback_query.from_user.id, f'🔄 Бот "{target_bot[1]}" перезапущен!')
            else:
                log_bot_status(target_bot[1], "restart_failed", "error")
                await bot.send_message(callback_query.from_user.id, f'❌ Ошибка перезапуска бота "{target_bot[1]}"')
        else:
            await bot.send_message(callback_query.from_user.id, '❌ Бот не найден')
    
    elif callback_query.data.startswith('delete_'):
        try:
            bot_id = int(callback_query.data.split('_')[1])
        except (ValueError, IndexError):
            await bot.send_message(callback_query.from_user.id, '❌ Ошибка: неверный ID бота')
            return
        
        bot_data = await get_bot_by_id(bot_id)
        if bot_data:
            await state.set_state(DeleteBotStates.waiting_for_confirmation)
            await state.update_data(bot_id=bot_id, bot_name=bot_data[1])
            await bot.send_message(
                callback_query.from_user.id,
                f'⚠️ Вы уверены, что хотите удалить бота "{bot_data[1]}"?\n\nЭто действие нельзя отменить!',
                reply_markup=get_confirm_delete_keyboard(bot_id)
            )
        else:
            await bot.send_message(callback_query.from_user.id, '❌ Бот не найден')
    
    elif callback_query.data.startswith('confirm_delete_'):
        try:
            bot_id = int(callback_query.data.split('_')[2])
        except (ValueError, IndexError):
            await bot.send_message(callback_query.from_user.id, '❌ Ошибка: неверный ID бота')
            return
        
        data = await state.get_data()
        bot_name = data.get('bot_name', 'Неизвестный бот')
        
        await delete_bot(bot_id)
        log_action("delete_bot", f"User {callback_query.from_user.id} deleted bot {bot_name}")
        await bot.send_message(callback_query.from_user.id, f'🗑️ Бот "{bot_name}" удален!')
        await state.clear()
    
    elif callback_query.data == 'cancel_delete':
        await state.clear()
        await bot.send_message(callback_query.from_user.id, '❌ Удаление отменено.')
    
    elif callback_query.data.startswith('info_'):
        try:
            bot_id = int(callback_query.data.split('_')[1])
        except (ValueError, IndexError):
            await bot.send_message(callback_query.from_user.id, '❌ Ошибка: неверный ID бота')
            return
        
        await show_bot_info(bot_id, callback_query.message)

# --- Обработчики FSM для добавления бота ---
@dp.message(AddBotStates.waiting_for_name)
async def process_bot_name(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer('❌ Пожалуйста, введите текстовое сообщение')
        return
        
    await state.update_data(name=message.text)
    await state.set_state(AddBotStates.waiting_for_script_path)
    await message.answer(
        '📁 Введите путь к скрипту бота (например: C:\\bots\\my_bot.py):',
        reply_markup=get_cancel_keyboard()
    )

@dp.message(AddBotStates.waiting_for_script_path)
async def process_script_path(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer('❌ Пожалуйста, введите текстовое сообщение')
        return
        
    script_path = message.text.strip()
    
    if not os.path.exists(script_path):
        await message.answer(
            '❌ Файл не найден! Проверьте путь и попробуйте снова:',
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(script_path=script_path)
    await state.set_state(AddBotStates.waiting_for_token)
    await message.answer(
        '🔑 Введите токен бота (или отправьте "нет" если токен не нужен):',
        reply_markup=get_cancel_keyboard()
    )

@dp.message(AddBotStates.waiting_for_token)
async def process_token(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer('❌ Пожалуйста, введите текстовое сообщение')
        return
        
    token = message.text.strip()
    if token.lower() == 'нет':
        token = None
    
    data = await state.get_data()
    name = data.get('name')
    script_path = data.get('script_path')
    
    if not name or not script_path:
        await message.answer('❌ Ошибка: данные бота не найдены. Попробуйте снова.')
        await state.clear()
        return
    
    try:
        await add_bot(name, script_path, token)
        log_action("bot_added", f"User {message.from_user.id} added bot {name}")
        await message.answer(f'✅ Бот "{name}" успешно добавлен!', reply_markup=get_main_menu())
    except Exception as e:
        log_error("add_bot_failed", f"User {message.from_user.id}, bot {name}: {str(e)}")
        await message.answer(f'❌ Ошибка добавления бота: {str(e)}', reply_markup=get_main_menu())
    
    await state.clear()

async def main():
    log_system("Bot starting...")
    print("🤖 Бот запускается...")
    await init_db()
    print("✅ База данных инициализирована")
    log_system("Database initialized")
    print("🚀 Бот готов к работе!")
    log_system("Bot ready for work")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 