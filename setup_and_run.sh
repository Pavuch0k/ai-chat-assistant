#!/bin/bash

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка что скрипт не запущен от root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}Не запускайте скрипт через sudo!${NC}"
    echo "Запустите: ./setup_and_run.sh"
    echo "Скрипт сам запросит sudo для установки пакетов"
    exit 1
fi

echo "=========================================="
echo "AI Chat Assistant - Установка и запуск"
echo "=========================================="

# Функция проверки команды
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 установлен"
        return 0
    else
        echo -e "${RED}✗${NC} $1 не установлен"
        return 1
    fi
}

# Функция установки PostgreSQL
install_postgresql() {
    echo -e "${YELLOW}Установка PostgreSQL...${NC}"
    if [[ -f /etc/debian_version ]]; then
        sudo apt update
        sudo apt install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
        sudo -u postgres psql -c "CREATE DATABASE ai_chat;" || true
        sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" || true
    elif [[ -f /etc/redhat-release ]]; then
        sudo yum install -y postgresql-server postgresql-contrib
        sudo postgresql-setup --initdb
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
        sudo -u postgres psql -c "CREATE DATABASE ai_chat;" || true
        sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" || true
    fi
}

# Функция установки Qdrant
install_qdrant() {
    echo -e "${YELLOW}Установка Qdrant...${NC}"
    QDRANT_VERSION="v1.6.1"
    QDRANT_DIR="$HOME/qdrant"
    
    if [ ! -f "$QDRANT_DIR/qdrant" ]; then
        mkdir -p $QDRANT_DIR
        cd $QDRANT_DIR
        
        # Определяем архитектуру
        ARCH=$(uname -m)
        if [ "$ARCH" = "x86_64" ]; then
            ARCH="x86_64"
        elif [ "$ARCH" = "aarch64" ]; then
            ARCH="arm64"
        else
            echo -e "${RED}Неподдерживаемая архитектура: $ARCH${NC}"
            exit 1
        fi
        
        echo "Скачивание Qdrant для $ARCH..."
        wget -q https://github.com/qdrant/qdrant/releases/download/${QDRANT_VERSION}/qdrant-${ARCH}-unknown-linux-gnu.tar.gz || \
        curl -L -o qdrant.tar.gz https://github.com/qdrant/qdrant/releases/download/${QDRANT_VERSION}/qdrant-${ARCH}-unknown-linux-gnu.tar.gz
        
        tar -xzf qdrant*.tar.gz
        chmod +x qdrant
        rm -f qdrant*.tar.gz
        cd -
    fi
    
    echo -e "${GREEN}✓${NC} Qdrant готов"
}

# Проверка Python
echo "Проверка зависимостей..."
if ! check_command python3; then
    echo -e "${RED}Python 3 не установлен. Установите его вручную.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Версия Python: $PYTHON_VERSION"

# Проверка pip
if ! check_command pip3; then
    echo -e "${YELLOW}Установка pip...${NC}"
    sudo apt install -y python3-pip || sudo yum install -y python3-pip
fi

# Проверка и установка python3-venv (проверяем ensurepip, а не просто venv)
echo -e "${YELLOW}Проверка python3-venv...${NC}"
if ! python3 -c "import ensurepip" 2>/dev/null; then
    echo -e "${YELLOW}Установка python3-venv...${NC}"
    if [[ -f /etc/debian_version ]]; then
        sudo apt update
        sudo apt install -y python3.10-venv || sudo apt install -y python3-venv
    elif [[ -f /etc/redhat-release ]]; then
        sudo yum install -y python3-venv
    fi
    echo -e "${GREEN}✓${NC} python3-venv установлен"
else
    echo -e "${GREEN}✓${NC} python3-venv доступен"
fi

# Проверка PostgreSQL
if ! check_command psql; then
    install_postgresql
fi

# Проверка что PostgreSQL запущен
if ! sudo systemctl is-active --quiet postgresql; then
    echo -e "${YELLOW}Запуск PostgreSQL...${NC}"
    sudo systemctl start postgresql
fi

# Проверка Qdrant
if [ ! -f "$HOME/qdrant/qdrant" ]; then
    install_qdrant
fi

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Создание виртуального окружения...${NC}"
    python3 -m venv venv 2>&1
    VENV_EXIT_CODE=$?
    if [ $VENV_EXIT_CODE -ne 0 ]; then
        echo -e "${RED}Ошибка создания виртуального окружения (код: $VENV_EXIT_CODE)${NC}"
        echo -e "${YELLOW}Попытка установки python3-venv...${NC}"
        if [[ -f /etc/debian_version ]]; then
            sudo apt update
            sudo apt install -y python3.10-venv || sudo apt install -y python3-venv
        elif [[ -f /etc/redhat-release ]]; then
            sudo yum install -y python3-venv
        fi
        echo -e "${YELLOW}Повторная попытка создания виртуального окружения...${NC}"
        python3 -m venv venv 2>&1
        VENV_EXIT_CODE=$?
        if [ $VENV_EXIT_CODE -ne 0 ]; then
            echo -e "${RED}Не удалось создать виртуальное окружение (код: $VENV_EXIT_CODE)${NC}"
            echo "Попробуйте установить вручную: sudo apt install -y python3.10-venv"
            exit 1
        fi
    fi
    echo -e "${GREEN}✓${NC} Виртуальное окружение создано"
fi

# Активация виртуального окружения
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓${NC} Виртуальное окружение активировано"
elif [ -d "venv" ]; then
    echo -e "${YELLOW}Виртуальное окружение существует, но activate не найден${NC}"
    echo "Попытка пересоздания..."
    rm -rf venv
    python3 -m venv venv
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✓${NC} Виртуальное окружение активировано"
    else
        echo -e "${RED}Ошибка: виртуальное окружение не создано${NC}"
        exit 1
    fi
else
    echo -e "${RED}Ошибка: виртуальное окружение не создано${NC}"
    exit 1
fi

# Обновление pip
echo -e "${YELLOW}Обновление pip...${NC}"
pip install --upgrade pip --timeout=300 --retries=5

# Установка зависимостей
echo -e "${YELLOW}Установка зависимостей Python (это может занять несколько минут)...${NC}"
pip install -r backend/requirements_local.txt --timeout=300 --retries=5 --default-timeout=300

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Создание .env файла...${NC}"
    cat > .env << 'EOF'
# Database
POSTGRES_DB=ai_chat
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_chat

# Qdrant
QDRANT_URL=http://localhost:6333

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_PROXY_URL=http://196.18.1.14:8000
OPENAI_PROXY_USERNAME=your_proxy_username
OPENAI_PROXY_PASSWORD=your_proxy_password

# App
APP_ENV=development
DEBUG=True
EOF
    echo -e "${GREEN}✓${NC} .env файл создан"
fi

# Создание директории для загрузок
mkdir -p backend/uploads

# Инициализация БД
echo -e "${YELLOW}Инициализация базы данных...${NC}"
cd backend
export $(cat ../.env | grep -v '^#' | xargs)
python3 -c "from app.db.database import engine; from app.models.db_models import Base; Base.metadata.create_all(bind=engine); print('База данных инициализирована')"
cd ..

# Запуск Qdrant в фоне
echo -e "${YELLOW}Запуск Qdrant...${NC}"
if ! pgrep -f "qdrant" > /dev/null; then
    nohup $HOME/qdrant/qdrant > /tmp/qdrant.log 2>&1 &
    sleep 3
    echo -e "${GREEN}✓${NC} Qdrant запущен"
else
    echo -e "${GREEN}✓${NC} Qdrant уже запущен"
fi

# Запуск backend через gunicorn
echo -e "${YELLOW}Запуск backend...${NC}"
cd backend
export $(cat ../.env | grep -v '^#' | xargs)

echo ""
echo -e "${GREEN}=========================================="
echo "Система запущена!"
echo "==========================================${NC}"
echo ""
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Админка: http://localhost:8000/admin"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --reload
