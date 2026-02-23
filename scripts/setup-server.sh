#!/bin/bash

SERVER_IP="217.114.6.7"
SSH_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAwcYK7RbVvQ/fX6LYpiket1nmz9zgfqk/F7WW5Yh2Wk nik@archlinux"

echo "=== Настройка сервера $SERVER_IP ==="

# Копирование SSH-ключа
echo "[1/5] Копирование SSH-ключа..."
ssh-copy-id -o StrictHostKeyChecking=no root@$SERVER_IP

# Настройка SSH и установка Docker
echo "[2/5] Настройка безопасности и установка Docker..."
ssh root@$SERVER_IP << 'EOF'
    # Обновление пакетов
    apt update && apt upgrade -y
    
    # Добавление SSH-ключа
    mkdir -p /root/.ssh
    echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAwcYK7RbVvQ/fX6LYpiket1nmz9zgfqk/F7WW5Yh2Wk nik@archlinux" >> /root/.ssh/authorized_keys
    chmod 700 /root/.ssh
    chmod 600 /root/.ssh/authorized_keys
    
    # Отключение парольной аутентификации
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    systemctl restart sshd
    
    # Установка Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
EOF

# Установка GitLab
echo "[3/5] Установка GitLab..."
ssh root@$SERVER_IP << 'EOF'
    docker run --detach \
      --hostname gitlab.devorb.ru \
      --publish 443:443 --publish 80:80 --publish 2222:22 \
      --name gitlab \
      --restart always \
      --volume /srv/gitlab/config:/etc/gitlab \
      --volume /srv/gitlab/logs:/var/log/gitlab \
      --volume /srv/gitlab/data:/var/opt/gitlab \
      --shm-size 256m \
      registry.gitlab.com/omnibus/gitlab-ce:latest
EOF

echo "[4/5] Ожидание запуска GitLab (это займёт ~2-3 минуты)..."
sleep 10

echo "[5/5] Проверка статуса..."
ssh root@$SERVER_IP "docker ps --filter name=gitlab"

echo ""
echo "=== Готово! ==="
echo "GitLab доступен: http://$SERVER_IP"
echo "SSH для Git: порт 2222"
echo ""
echo "⚠️  ВАЖНО: Проверьте доступ по ключу перед закрытием сессии!"
echo "   ssh root@$SERVER_IP"
