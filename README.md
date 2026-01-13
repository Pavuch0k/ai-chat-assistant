# AI Chat Assistant

AI чат-ассистент с RAG и интеграцией CRM.

## Структура проекта

```
ai-chat/
├── backend/          # FastAPI приложение
│   └── app/
│       ├── api/      # API endpoints
│       ├── core/     # Конфигурация
│       ├── models/   # Модели данных
│       ├── services/ # Бизнес-логика
│       ├── db/       # Работа с БД
│       ├── ai/       # AI сервисы
│       └── utils/    # Утилиты
├── frontend/         # Виджет для сайта
├── docker/           # Docker файлы
└── docker-compose.yml
```

## Запуск

```bash
docker-compose up -d
```
