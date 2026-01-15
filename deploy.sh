#!/bin/bash

# Скрипт для развертывания проекта на сервере
# Использование: ./deploy.sh root@45.84.227.40

set -e

SERVER="${1:-root@45.84.227.40}"
PROJECT_DIR="/opt/ai-chat"
DOMAIN_MAIN="ai.devorb.ru"
DOMAIN_ADMIN="ai-admin.devorb.ru"

echo "=========================================="
echo "Развертывание AI Chat Assistant на сервере"
echo "=========================================="
echo "Сервер: $SERVER"
echo "Директория: $PROJECT_DIR"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для выполнения команд на сервере с выводом в реальном времени
ssh_exec() {
    ssh -o StrictHostKeyChecking=no "$SERVER" "$@"
}

# 1. Установка необходимых пакетов
echo -e "${YELLOW}Установка необходимых пакетов...${NC}"
ssh_exec "apt-get update -qq && apt-get install -y -qq git python3 python3-pip python3-venv postgresql postgresql-contrib curl wget nginx > /dev/null 2>&1 || yum install -y -q git python3 python3-pip postgresql postgresql-server curl wget nginx > /dev/null 2>&1"
echo -e "${GREEN}✓${NC} Пакеты установлены"

# 2. Клонирование/обновление проекта
echo -e "${YELLOW}Клонирование проекта...${NC}"
ssh_exec "
if [ -d '$PROJECT_DIR' ]; then
    cd $PROJECT_DIR && git pull
else
    git clone https://github.com/Pavuch0k/ai-chat-assistant.git $PROJECT_DIR
fi
"
echo -e "${GREEN}✓${NC} Проект обновлен"

# 3. Настройка PostgreSQL
echo -e "${YELLOW}Настройка PostgreSQL...${NC}"
ssh_exec "
sudo -u postgres psql -c \"CREATE DATABASE ai_chat;\" 2>/dev/null || true
sudo -u postgres psql -c \"CREATE USER postgres WITH PASSWORD 'postgres';\" 2>/dev/null || true
sudo -u postgres psql -c \"ALTER USER postgres WITH SUPERUSER;\" 2>/dev/null || true
sudo systemctl enable postgresql > /dev/null 2>&1
sudo systemctl start postgresql > /dev/null 2>&1
"
echo -e "${GREEN}✓${NC} PostgreSQL настроен"

# 4. Запуск setup_and_run.sh в фоне с выводом логов
echo -e "${YELLOW}Запуск приложения...${NC}"
ssh_exec "
cd $PROJECT_DIR
chmod +x setup_and_run.sh
nohup bash -c 'export TERM=xterm && ./setup_and_run.sh > /tmp/ai-chat.log 2>&1' &
sleep 5
"
echo -e "${GREEN}✓${NC} Приложение запущено"

# 5. Установка и настройка Nginx
echo -e "${YELLOW}Настройка Nginx...${NC}"
ssh_exec "
cat > /etc/nginx/sites-available/ai-chat << 'NGINX_CONFIG'
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

# Создаем симлинк если его нет
[ -f /etc/nginx/sites-enabled/ai-chat ] || ln -s /etc/nginx/sites-available/ai-chat /etc/nginx/sites-enabled/

# Удаляем default конфиг если есть
rm -f /etc/nginx/sites-enabled/default

# Проверяем конфигурацию и перезапускаем
nginx -t && systemctl restart nginx && systemctl enable nginx
"
echo -e "${GREEN}✓${NC} Nginx настроен"

# 6. Проверка статуса
echo ""
echo -e "${GREEN}=========================================="
echo "Развертывание завершено!"
echo "==========================================${NC}"
echo ""
echo "Проверка статуса сервисов:"
ssh_exec "
echo 'PostgreSQL:' && systemctl is-active postgresql
echo 'Nginx:' && systemctl is-active nginx
echo 'Qdrant:' && pgrep -f qdrant > /dev/null && echo 'running' || echo 'not running'
echo 'Backend:' && pgrep -f gunicorn > /dev/null && echo 'running' || echo 'not running'
"
echo ""
echo "Логи приложения (последние 20 строк):"
ssh_exec "tail -20 /tmp/ai-chat.log 2>/dev/null || echo 'Логи пока пусты'"
echo ""
echo -e "${YELLOW}Домены:${NC}"
echo "  - Виджет: http://$DOMAIN_MAIN"
echo "  - Админка: http://$DOMAIN_ADMIN"
echo ""
echo -e "${YELLOW}Просмотр логов в реальном времени:${NC}"
echo "  ssh $SERVER 'tail -f /tmp/ai-chat.log'"
echo ""
