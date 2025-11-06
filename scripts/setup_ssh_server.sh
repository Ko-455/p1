#!/bin/bash
# Скрипт автоматической установки и настройки SSH-сервера
# Кейс 1: Установка и настройка SSH-сервера

echo "========================================="
echo "Установка и настройка SSH-сервера"
echo "========================================="
echo ""

# Проверка прав суперпользователя
if [ "$EUID" -ne 0 ]; then 
    echo "Пожалуйста, запустите скрипт с правами sudo:"
    echo "sudo bash $0"
    exit 1
fi

# Шаг 1: Обновление системы
echo "[Шаг 1/6] Обновление системы..."
apt-get update -y
apt-get upgrade -y

# Шаг 2: Установка OpenSSH Server
echo "[Шаг 2/6] Установка OpenSSH Server..."
apt-get install openssh-server -y

# Шаг 3: Запуск SSH-сервера
echo "[Шаг 3/6] Запуск SSH-сервера..."
systemctl start ssh

# Шаг 4: Включение автозапуска
echo "[Шаг 4/6] Включение автозапуска SSH..."
systemctl enable ssh

# Шаг 5: Проверка статуса
echo "[Шаг 5/6] Проверка статуса SSH-сервера..."
systemctl status ssh --no-pager

# Шаг 6: Проверка порта
echo "[Шаг 6/6] Проверка, что SSH слушает порт 22..."
ss -tulpn | grep :22

echo ""
echo "========================================="
echo "✅ SSH-сервер успешно установлен и настроен!"
echo "========================================="
echo ""
echo "Полезные команды:"
echo "  - Проверить статус: sudo systemctl status ssh"
echo "  - Перезапустить: sudo systemctl restart ssh"
echo "  - Остановить: sudo systemctl stop ssh"
echo "  - Конфигурация: sudo nano /etc/ssh/sshd_config"
echo ""

# Показать IP-адрес для подключения
echo "IP-адреса этого сервера:"
hostname -I

