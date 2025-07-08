import telebot
from telebot import types
import sqlite3
import subprocess
import sys
import os

from handlers import bot

if __name__ == '__main__':
    bot.polling(none_stop=True) 