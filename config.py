import os

# Получаем токен из переменных окружения (Railway) или используем локальный
API_TOKEN = os.getenv('API_TOKEN', '7684724135:AAEWhZ1vf9F5yFh__jKMA8ljnQ0ReojAEIU')
DB_PATH = os.getenv('DB_PATH', 'bots.db') 