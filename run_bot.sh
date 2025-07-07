#!/bin/bash

# Скрипт для автоматического запуска и перезапуска бота
# Использование: ./run_bot.sh

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$BOT_DIR/bot_runner.log"

echo "$(date): Starting bot runner..." >> "$LOG_FILE"

# Функция для запуска бота
start_bot() {
    echo "$(date): Starting bot..." >> "$LOG_FILE"
    cd "$BOT_DIR"
    python3 main.py >> "$LOG_FILE" 2>&1
}

# Функция для остановки бота
stop_bot() {
    echo "$(date): Stopping bot..." >> "$LOG_FILE"
    pkill -f "python3 main.py"
    sleep 2
}

# Обработка сигналов для корректного завершения
trap 'echo "$(date): Received signal, stopping bot..." >> "$LOG_FILE"; stop_bot; exit 0' SIGTERM SIGINT

# Основной цикл
while true; do
    if ! pgrep -f "python3 main.py" > /dev/null; then
        echo "$(date): Bot not running, starting..." >> "$LOG_FILE"
        start_bot &
        sleep 5
    else
        echo "$(date): Bot is running, checking in 30 seconds..." >> "$LOG_FILE"
        sleep 30
    fi
done 