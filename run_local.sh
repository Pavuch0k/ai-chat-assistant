#!/bin/bash

# Скрипт для локального запуска без Docker

echo "Запуск AI Chat Assistant локально..."

# Активация виртуального окружения если есть
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Установка зависимостей если нужно
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r backend/requirements.txt
fi

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo "Создание .env файла из примера..."
    cp .env.example .env
    echo "Пожалуйста, отредактируйте .env файл и укажите ваш OPENAI_API_KEY"
fi

# Экспорт переменных окружения
export $(cat .env | grep -v '^#' | xargs)

# Запуск через gunicorn
cd backend
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --reload
