#!/bin/bash

# Скрипт для деплоя бота на сервер

SERVER="root@194.87.202.93"
PASSWORD="khkXP@4M#XbH@Z"
REMOTE_DIR="/root/uvedomlenia_bot"

echo "🚀 Начинаю деплой бота на сервер..."

# Установка sshpass если нужно (для macOS: brew install hudochenkov/sshpass/sshpass)
# Для Linux обычно уже установлен

# Создаем директорию на сервере
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER "mkdir -p $REMOTE_DIR"

# Копируем файлы проекта (исключая .env, __pycache__, .git)
echo "📦 Копирую файлы проекта..."
sshpass -p "$PASSWORD" rsync -avz --exclude='.env' --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' --exclude='bot.log' --exclude='*.db' --exclude='.DS_Store' ./ $SERVER:$REMOTE_DIR/

# Копируем .env файл отдельно
echo "🔐 Копирую конфигурацию..."
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no .env $SERVER:$REMOTE_DIR/.env

# Устанавливаем зависимости и запускаем бота
echo "⚙️  Настраиваю окружение на сервере..."
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
cd /root/uvedomlenia_bot

# Устанавливаем Python зависимости
echo "📥 Устанавливаю зависимости..."
pip3 install --break-system-packages -q aiogram aiosqlite python-dotenv pytz apscheduler

# Останавливаем старый процесс бота если есть
pkill -f "python3 main.py" 2>/dev/null || true
sleep 2

# Запускаем бота в фоне
echo "🔄 Запускаю бота..."
nohup python3 main.py > bot.log 2>&1 &

sleep 3

# Проверяем статус
if ps aux | grep -q "[p]ython3 main.py"; then
    echo "✅ Бот успешно запущен!"
    echo "📋 Логи: tail -f /root/uvedomlenia_bot/bot.log"
else
    echo "❌ Ошибка запуска бота. Проверьте логи:"
    tail -20 bot.log
fi
ENDSSH

echo "✅ Деплой завершен!"

