#!/usr/bin/env python3
"""
Мобильная версия Mather Bot
Оптимизирована для работы на Android через Termux
"""

import asyncio
import os
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiosqlite
from db import init_db, get_bots, add_bot, update_bot_status, delete_bot, get_bot_stats
from process_manager import start_bot, stop_bot, restart_bot
from logger import log_action, log_error, log_system, log_bot_status
import config

# Настройки для мобильных устройств
MOBILE_MODE = True
CHECK_INTERVAL = 300  # 5 минут вместо 30 секунд для экономии батареи

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

# --- Упрощенная клавиатура для мобильных ---
def get_mobile_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить", callback_data="add_bot")
    builder.button(text="📊 Статистика", callback_data="stats")
    builder.button(text="📋 Список", callback_data="list_bots")
    builder.button(text="🔄 Перезапуск", callback_data="restart_all")
    builder.adjust(2)
    return builder.as_markup()

def get_bot_mobile_keyboard(bot_id, status):
    builder = InlineKeyboardBuilder()
    if status == 'stopped':
        builder.button(text="▶️", callback_data=f"start_{bot_id}")
    else:
        builder.button(text="⏹️", callback_data=f"stop_{bot_id}")
        builder.button(text="🔄", callback_data=f"restart_{bot_id}")
    
    builder.button(text="🗑️", callback_data=f"delete_{bot_id}")
    builder.adjust(3)
    return builder.as_markup()

def get_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_add")
    return builder.as_markup()

def get_confirm_delete_keyboard(bot_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data=f"confirm_delete_{bot_id}")
    builder.button(text="❌ Нет", callback_data="cancel_delete")
    builder.adjust(2)
    return builder.as_markup()

async def show_mobile_bots_list(message):
    bots = await get_bots()
    if not bots:
        await message.answer('🤖 Ботов нет', reply_markup=get_mobile_menu())
        return
    
    # Показываем только основные боты (первые 5)
    for i, bot_data in enumerate(bots[:5]):
        bot_id, name, script_path, token, status, created_at, last_started, start_count = bot_data
        text = f"🤖 **{name}**\n📊 {status} | 🚀 {start_count}"
        
        await message.answer(text, reply_markup=get_bot_mobile_keyboard(bot_id, status), parse_mode='Markdown')
    
    if len(bots) > 5:
        await message.answer(f"📋 Показано 5 из {len(bots)} ботов", reply_markup=get_mobile_menu())
    else:
        await message.answer("📱 Меню:", reply_markup=get_mobile_menu())

async def show_mobile_stats(message):
    stats = await get_bot_stats()
    text = f"""
📊 **Статистика:**
🤖 Всего: {stats['total_bots']}
▶️ Работает: {stats['running_bots']}
⏹️ Остановлено: {stats['stopped_bots']}
"""
    
    if stats['most_active']:
        name, count = stats['most_active']
        text += f"🏆 {name}: {count} запусков"
    
    await message.answer(text, reply_markup=get_mobile_menu(), parse_mode='Markdown')

async def restart_all_bots(message):
    bots = await get_bots()
    if not bots:
        await message.answer('🤖 Ботов нет для перезапуска', reply_markup=get_mobile_menu())
        return
    
    await message.answer('🔄 Перезапускаю всех ботов...')
    
    success_count = 0
    for bot_data in bots:
        bot_id, name, script_path, token, status, created_at, last_started, start_count = bot_data
        try:
            success = await restart_bot(bot_id, script_path)
            if success:
                await update_bot_status(bot_id, 'running')
                success_count += 1
        except Exception as e:
            log_error(f"restart_all_failed", f"Bot {name}: {str(e)}")
    
    await message.answer(f'✅ Перезапущено {success_count} из {len(bots)} ботов', reply_markup=get_mobile_menu())

@dp.message()
async def cmd_start(message: types.Message):
    if message.text == '/start':
        log_action("mobile_start", f"User {message.from_user.id} started mobile bot")
        await message.answer('📱 **Mather Bot Mobile**\nУправление ботами с телефона', parse_mode='Markdown')
        await show_mobile_bots_list(message)

@dp.callback_query()
async def process_mobile_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    
    if not callback_query.data:
        return
    
    if callback_query.data == 'add_bot':
        log_action("mobile_add_bot", f"User {callback_query.from_user.id}")
        await state.set_state(AddBotStates.waiting_for_name)
        await bot.send_message(
            callback_query.from_user.id, 
            '📝 Имя бота:',
            reply_markup=get_cancel_keyboard()
        )
    
    elif callback_query.data == 'stats':
        log_action("mobile_stats", f"User {callback_query.from_user.id}")
        await show_mobile_stats(callback_query.message)
    
    elif callback_query.data == 'list_bots':
        log_action("mobile_list", f"User {callback_query.from_user.id}")
        await show_mobile_bots_list(callback_query.message)
    
    elif callback_query.data == 'restart_all':
        log_action("mobile_restart_all", f"User {callback_query.from_user.id}")
        await restart_all_bots(callback_query.message)
    
    elif callback_query.data == 'cancel_add':
        await state.clear()
        await bot.send_message(callback_query.from_user.id, '❌ Отменено')
    
    elif callback_query.data.startswith('start_'):
        try:
            bot_id = int(callback_query.data.split('_')[1])
        except (ValueError, IndexError):
            await bot.send_message(callback_query.from_user.id, '❌ Ошибка')
            return
            
        bots = await get_bots()
        target_bot = None
        for b in bots:
            if b[0] == bot_id:
                target_bot = b
                break
        
        if target_bot:
            log_bot_status(target_bot[1], "mobile_start", f"User {callback_query.from_user.id}")
            success = await start_bot(bot_id, target_bot[2])
            if success:
                await update_bot_status(bot_id, 'running')
                await bot.send_message(callback_query.from_user.id, f'✅ {target_bot[1]} запущен')
            else:
                await bot.send_message(callback_query.from_user.id, f'❌ Ошибка запуска {target_bot[1]}')
        else:
            await bot.send_message(callback_query.from_user.id, '❌ Бот не найден')
    
    elif callback_query.data.startswith('stop_'):
        try:
            bot_id = int(callback_query.data.split('_')[1])
        except (ValueError, IndexError):
            await bot.send_message(callback_query.from_user.id, '❌ Ошибка')
            return
            
        bots = await get_bots()
        target_bot = None
        for b in bots:
            if b[0] == bot_id:
                target_bot = b
                break
        
        if target_bot:
            log_bot_status(target_bot[1], "mobile_stop", f"User {callback_query.from_user.id}")
            success = await stop_bot(bot_id)
            if success:
                await update_bot_status(bot_id, 'stopped')
                await bot.send_message(callback_query.from_user.id, f'⏹️ {target_bot[1]} остановлен')
            else:
                await bot.send_message(callback_query.from_user.id, f'❌ Ошибка остановки {target_bot[1]}')
        else:
            await bot.send_message(callback_query.from_user.id, '❌ Бот не найден')
    
    elif callback_query.data.startswith('restart_'):
        try:
            bot_id = int(callback_query.data.split('_')[1])
        except (ValueError, IndexError):
            await bot.send_message(callback_query.from_user.id, '❌ Ошибка')
            return
            
        bots = await get_bots()
        target_bot = None
        for b in bots:
            if b[0] == bot_id:
                target_bot = b
                break
        
        if target_bot:
            log_bot_status(target_bot[1], "mobile_restart", f"User {callback_query.from_user.id}")
            success = await restart_bot(bot_id, target_bot[2])
            if success:
                await update_bot_status(bot_id, 'running')
                await bot.send_message(callback_query.from_user.id, f'🔄 {target_bot[1]} перезапущен')
            else:
                await bot.send_message(callback_query.from_user.id, f'❌ Ошибка перезапуска {target_bot[1]}')
        else:
            await bot.send_message(callback_query.from_user.id, '❌ Бот не найден')
    
    elif callback_query.data.startswith('delete_'):
        try:
            bot_id = int(callback_query.data.split('_')[1])
        except (ValueError, IndexError):
            await bot.send_message(callback_query.from_user.id, '❌ Ошибка')
            return
        
        bot_data = await get_bot_by_id(bot_id)
        if bot_data:
            await state.set_state(DeleteBotStates.waiting_for_confirmation)
            await state.update_data(bot_id=bot_id, bot_name=bot_data[1])
            await bot.send_message(
                callback_query.from_user.id,
                f'⚠️ Удалить "{bot_data[1]}"?',
                reply_markup=get_confirm_delete_keyboard(bot_id)
            )
        else:
            await bot.send_message(callback_query.from_user.id, '❌ Бот не найден')
    
    elif callback_query.data.startswith('confirm_delete_'):
        try:
            bot_id = int(callback_query.data.split('_')[2])
        except (ValueError, IndexError):
            await bot.send_message(callback_query.from_user.id, '❌ Ошибка')
            return
        
        data = await state.get_data()
        bot_name = data.get('bot_name', 'Неизвестный')
        
        await delete_bot(bot_id)
        log_action("mobile_delete", f"User {callback_query.from_user.id} deleted {bot_name}")
        await bot.send_message(callback_query.from_user.id, f'🗑️ {bot_name} удален')
        await state.clear()
    
    elif callback_query.data == 'cancel_delete':
        await state.clear()
        await bot.send_message(callback_query.from_user.id, '❌ Отменено')

# --- Обработчики FSM для добавления бота ---
@dp.message(AddBotStates.waiting_for_name)
async def process_mobile_bot_name(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer('❌ Введите текст')
        return
        
    await state.update_data(name=message.text)
    await state.set_state(AddBotStates.waiting_for_script_path)
    await message.answer('📁 Путь к скрипту:', reply_markup=get_cancel_keyboard())

@dp.message(AddBotStates.waiting_for_script_path)
async def process_mobile_script_path(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer('❌ Введите текст')
        return
        
    script_path = message.text.strip()
    
    if not os.path.exists(script_path):
        await message.answer('❌ Файл не найден!', reply_markup=get_cancel_keyboard())
        return
    
    await state.update_data(script_path=script_path)
    await state.set_state(AddBotStates.waiting_for_token)
    await message.answer('🔑 Токен (или "нет"):', reply_markup=get_cancel_keyboard())

@dp.message(AddBotStates.waiting_for_token)
async def process_mobile_token(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer('❌ Введите текст')
        return
        
    token = message.text.strip()
    if token.lower() == 'нет':
        token = None
    
    data = await state.get_data()
    name = data.get('name')
    script_path = data.get('script_path')
    
    if not name or not script_path:
        await message.answer('❌ Ошибка данных')
        await state.clear()
        return
    
    try:
        await add_bot(name, script_path, token)
        log_action("mobile_bot_added", f"User {message.from_user.id} added {name}")
        await message.answer(f'✅ {name} добавлен!', reply_markup=get_mobile_menu())
    except Exception as e:
        log_error("mobile_add_failed", f"User {message.from_user.id}, {name}: {str(e)}")
        await message.answer(f'❌ Ошибка: {str(e)}', reply_markup=get_mobile_menu())
    
    await state.clear()

async def main():
    log_system("Mobile bot starting...")
    print("📱 Мобильный бот запускается...")
    
    # Создаем папки если их нет
    os.makedirs('logs', exist_ok=True)
    os.makedirs('backups', exist_ok=True)
    
    await init_db()
    print("✅ База данных готова")
    log_system("Mobile database ready")
    
    print("🚀 Мобильный бот готов!")
    log_system("Mobile bot ready")
    
    # Запускаем с увеличенным интервалом для экономии батареи
    await dp.start_polling(bot, polling_timeout=CHECK_INTERVAL)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n📱 Мобильный бот остановлен")
        log_system("Mobile bot stopped by user")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        log_error("mobile_crash", str(e)) 