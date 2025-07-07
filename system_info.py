import psutil
import platform
import sys
from datetime import datetime
import time

def get_system_info():
    """Получение информации о системе"""
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Память
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used // (1024**3)  # GB
        memory_total = memory.total // (1024**3)  # GB
        
        # Диск
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used = disk.used // (1024**3)  # GB
        disk_total = disk.total // (1024**3)  # GB
        
        # Система
        system = platform.system()
        python_version = sys.version.split()[0]
        
        return {
            'cpu_percent': cpu_percent,
            'cpu_count': cpu_count,
            'memory_percent': memory_percent,
            'memory_used': memory_used,
            'memory_total': memory_total,
            'disk_percent': disk_percent,
            'disk_used': disk_used,
            'disk_total': disk_total,
            'system': system,
            'python_version': python_version
        }
    except Exception as e:
        return {
            'error': f'Ошибка получения системной информации: {str(e)}'
        }

def format_system_info():
    """Форматированная информация о системе"""
    info = get_system_info()
    
    if 'error' in info:
        return f"❌ {info['error']}"
    
    return f"""
🖥️ **Системная информация:**

💻 **Процессор:**
   • Загрузка: {info['cpu_percent']}%
   • Ядра: {info['cpu_count']}

🧠 **Память:**
   • Использовано: {info['memory_used']} GB / {info['memory_total']} GB
   • Загрузка: {info['memory_percent']}%

💾 **Диск:**
   • Использовано: {info['disk_used']} GB / {info['disk_total']} GB
   • Загрузка: {info['disk_percent']}%

🔧 **Система:**
   • ОС: {info['system']}
   • Python: {info['python_version']}
"""

def get_uptime():
    """Время работы системы"""
    try:
        uptime_seconds = int(time.time() - psutil.boot_time())
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        return f"{hours}ч {minutes}м"
    except:
        return "Неизвестно" 