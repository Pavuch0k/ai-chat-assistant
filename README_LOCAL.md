# Локальный запуск без Docker

## Требования

- Python 3.11+
- PostgreSQL (локально или удаленно)
- Qdrant (локально или удаленно)

## Установка

1. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Установите зависимости:
```bash
pip install --upgrade pip
pip install -r backend/requirements_local.txt
```

3. Настройте .env файл:
```bash
cp .env.example .env
# Отредактируйте .env и укажите ваши настройки
```

4. Убедитесь что PostgreSQL запущен:
```bash
# Если PostgreSQL локально:
sudo systemctl start postgresql

# Или используйте удаленный PostgreSQL
```

5. Убедитесь что Qdrant запущен:
```bash
# Если Qdrant локально:
# Скачайте и запустите Qdrant с официального сайта
# Или используйте удаленный Qdrant
```

## Запуск

### Вариант 1: Через gunicorn (рекомендуется)
```bash
chmod +x run_local.sh
./run_local.sh
```

### Вариант 2: Через uvicorn напрямую
```bash
cd backend
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Вариант 3: Через gunicorn вручную
```bash
cd backend
source ../venv/bin/activate
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --reload
```

## Настройка .env для локального запуска

```env
# Database (локальный PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_chat

# Qdrant (локальный или удаленный)
QDRANT_URL=http://localhost:6333

# OpenAI
OPENAI_API_KEY=ваш_ключ
OPENAI_PROXY_URL=http://196.18.1.14:8000
OPENAI_PROXY_USERNAME=60yNdR
OPENAI_PROXY_PASSWORD=kZBwN4

# App
APP_ENV=development
DEBUG=True
```

## Запуск Frontend

Frontend можно запустить через простой HTTP сервер:

```bash
cd frontend
python3 -m http.server 8080
```

Или через nginx если установлен.

## Проверка

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Админка: http://localhost:8000/admin
- Frontend: http://localhost:8080
