#!/data/data/com.termux/files/usr/bin/bash

# Автоматическая установка Mather Bot на Android
# Запуск: bash install_mobile.sh

echo "📱 Установка Mather Bot на Android..."
echo "=================================="

# Обновление системы
echo "🔄 Обновление системы..."
pkg update && pkg upgrade -y

# Установка необходимых пакетов
echo "📦 Установка пакетов..."
pkg install python git wget curl termux-api -y

# Создание папки для проекта
echo "📁 Создание папки проекта..."
cd ~
if [ -d "mather-bot" ]; then
    echo "⚠️ Папка mather-bot уже существует, удаляем..."
    rm -rf mather-bot
fi

# Клонирование репозитория
echo "📥 Клонирование репозитория..."
git clone https://github.com/1Momori1/mather-bot.git
cd mather-bot

# Установка зависимостей Python
echo "🐍 Установка Python зависимостей..."
pip install -r requirements.txt

# Создание скрипта автозапуска
echo "🚀 Создание скрипта автозапуска..."
cat > ~/start_mather_bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash

# Переходим в папку бота
cd ~/mather-bot

# Проверяем, не запущен ли уже бот
if ! pgrep -f "python mobile_main.py" > /dev/null; then
    echo "$(date): Starting Mather Bot Mobile..."
    python mobile_main.py > ~/bot_mobile.log 2>&1 &
    termux-notification --title "Mather Bot" --content "Bot started successfully"
else
    echo "$(date): Bot is already running"
fi
EOF

chmod +x ~/start_mather_bot.sh

# Создание скрипта остановки
echo "⏹️ Создание скрипта остановки..."
cat > ~/stop_mather_bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash

echo "$(date): Stopping Mather Bot..."
pkill -f "python mobile_main.py"
sleep 2
termux-notification --title "Mather Bot" --content "Bot stopped"
EOF

chmod +x ~/stop_mather_bot.sh

# Создание скриапта мониторинга
echo "👁️ Создание скрипта мониторинга..."
cat > ~/monitor_mather_bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash

while true; do
    if ! pgrep -f "python mobile_main.py" > /dev/null; then
        echo "$(date): Bot crashed, restarting..."
        cd ~/mather-bot
        python mobile_main.py > ~/bot_mobile.log 2>&1 &
        termux-notification --title "Mather Bot" --content "Bot restarted automatically"
    fi
    sleep 300  # Проверка каждые 5 минут
done
EOF

chmod +x ~/monitor_mather_bot.sh

# Настройка автозапуска при старте Termux
echo "🔄 Настройка автозапуска..."
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start_mather_bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/mather-bot
python mobile_main.py > ~/bot_mobile.log 2>&1 &
EOF

chmod +x ~/.termux/boot/start_mather_bot.sh

# Установка Termux:Boot
echo "📱 Установка Termux:Boot..."
pkg install termux-boot -y

# Создание алиасов
echo "⚡ Создание алиасов..."
echo 'alias bot-start="~/start_mather_bot.sh"' >> ~/.bashrc
echo 'alias bot-stop="~/stop_mather_bot.sh"' >> ~/.bashrc
echo 'alias bot-status="ps aux | grep \"python mobile_main.py\"'" >> ~/.bashrc
echo 'alias bot-logs="tail -f ~/bot_mobile.log"' >> ~/.bashrc
echo 'alias bot-monitor="nohup ~/monitor_mather_bot.sh > ~/monitor.log 2>&1 &"' >> ~/.bashrc

# Создание файла с инструкциями
echo "📖 Создание инструкций..."
cat > ~/mather-bot/MOBILE_README.txt << 'EOF'
📱 Mather Bot Mobile - Инструкции

🚀 Запуск:
- bot-start          - запустить бота
- bot-stop           - остановить бота
- bot-status         - проверить статус
- bot-logs           - посмотреть логи
- bot-monitor        - запустить мониторинг

📱 Автозапуск:
- Установите Termux:Boot из F-Droid
- Включите автозапуск: termux-boot enable
- Бот будет запускаться автоматически

🔧 Настройка:
1. Отредактируйте config.py - вставьте ваш токен
2. Запустите: bot-start
3. Отправьте /start в Telegram

📊 Мониторинг:
- Логи: ~/bot_mobile.log
- Мониторинг: ~/monitor.log
- База данных: ~/mather-bot/bots.db

💡 Советы:
- Используйте Termux из F-Droid (не Google Play)
- Включите автозапуск для работы 24/7
- Мониторьте использование батареи
EOF

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте токен: nano ~/mather-bot/config.py"
echo "2. Запустите бота: bot-start"
echo "3. Отправьте /start в Telegram"
echo ""
echo "📖 Подробные инструкции: cat ~/mather-bot/MOBILE_README.txt"
echo ""
echo "🎉 Готово! Ваш бот готов к работе на мобильном устройстве!" 