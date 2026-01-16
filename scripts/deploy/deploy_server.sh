#!/bin/bash
# Скрипт для выполнения на сервере одной командой
# Запуск: ssh root@45.84.227.40 'bash -s' < deploy_server.sh

set -e

PROJECT_DIR="/opt/ai-chat"
DOMAIN_MAIN="ai.devorb.ru"
DOMAIN_ADMIN="ai-admin.devorb.ru"

echo "=========================================="
echo "Развертывание AI Chat Assistant"
echo "=========================================="

# Создание пользователя если не существует
if ! id "aichat" &>/dev/null; then
    useradd -m -s /bin/bash aichat
    echo "aichat ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/yum, /usr/bin/systemctl" >> /etc/sudoers.d/aichat
    chmod 0440 /etc/sudoers.d/aichat
    echo "✓ Пользователь aichat создан"
else
    echo "✓ Пользователь aichat уже существует"
fi

# Клонирование/обновление проекта
if [ -d "$PROJECT_DIR" ]; then
    cd $PROJECT_DIR && git pull
    echo "✓ Проект обновлен"
else
    git clone https://github.com/Pavuch0k/ai-chat-assistant.git $PROJECT_DIR
    echo "✓ Проект склонирован"
fi

chown -R aichat:aichat $PROJECT_DIR

# Создание .env файла
cat > $PROJECT_DIR/.env << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_chat

# Qdrant
QDRANT_URL=http://localhost:6333

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_PROXY_URL=http://194.33.32.143:8000
OPENAI_PROXY_USERNAME=cwKWZA
OPENAI_PROXY_PASSWORD=C1qhZD

# App
APP_ENV=production
DEBUG=False
EOF
chown aichat:aichat $PROJECT_DIR/.env
echo "✓ .env файл создан"

# Запуск установки от имени пользователя aichat
echo "Запуск установки..."
cd $PROJECT_DIR
su - aichat -c "cd $PROJECT_DIR && nohup bash scripts/run/setup_and_run.sh > ~/install.log 2>&1 &"
sleep 5
echo "✓ Установка запущена в фоне"

# Настройка Nginx
cat > /etc/nginx/sites-available/ai-chat << NGINX_CONFIG
# Основной домен - виджет
server {
    listen 80;
    server_name $DOMAIN_MAIN;
    
    root $PROJECT_DIR/frontend;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    location /src/ {
        alias $PROJECT_DIR/frontend/src/;
    }
    
    # Прокси для API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}

# Админ панель
server {
    listen 80;
    server_name $DOMAIN_ADMIN;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
NGINX_CONFIG

ln -sf /etc/nginx/sites-available/ai-chat /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
echo "✓ Nginx настроен"

echo ""
echo "=========================================="
echo "Развертывание завершено!"
echo "=========================================="
echo ""
echo "Просмотр логов установки:"
echo "  tail -f /home/aichat/install.log"
echo ""
echo "Домены:"
echo "  - Виджет: http://$DOMAIN_MAIN"
echo "  - Админка: http://$DOMAIN_ADMIN"
echo ""
