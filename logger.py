import logging
import os
from datetime import datetime

# Настройка логирования
def setup_logger():
    # Создаем папку для логов если её нет
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Настраиваем формат логов
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Основной логгер
    logger = logging.getLogger('bot_manager')
    logger.setLevel(logging.INFO)
    
    # Файловый обработчик
    file_handler = logging.FileHandler(
        f'logs/bot_manager_{datetime.now().strftime("%Y%m%d")}.log',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Форматтер
    formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Глобальный логгер
logger = setup_logger()

def log_action(action, details=""):
    """Логирование действий пользователя"""
    logger.info(f"ACTION: {action} - {details}")

def log_error(error, details=""):
    """Логирование ошибок"""
    logger.error(f"ERROR: {error} - {details}")

def log_system(message):
    """Логирование системных сообщений"""
    logger.info(f"SYSTEM: {message}")

def log_bot_status(bot_name, action, status=""):
    """Логирование статуса ботов"""
    logger.info(f"BOT: {bot_name} - {action} {status}") 