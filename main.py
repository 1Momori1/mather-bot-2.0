import telebot
from telebot import types
import sqlite3
import subprocess
import sys
import os

from handlers import bot

if __name__ == '__main__':
    print('✅ Telegram-бот-менеджер успешно запущен! Ожидаю команды в Telegram...')
    bot.polling(none_stop=True) 