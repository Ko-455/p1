#!/bin/bash
# Скрипт для тестирования SSH-подключения
# Кейс 2: Подключение к удаленному серверу

echo "========================================="
echo "Тестирование SSH-подключения"
echo "========================================="
echo ""

# Запрос параметров подключения
read -p "Введите адрес сервера (user@host или IP): " SERVER

if [ -z "$SERVER" ]; then
    echo "❌ Адрес сервера не указан."
    exit 1
fi

# Запрос порта
read -p "Введите порт SSH (по умолчанию 22): " PORT
PORT=${PORT:-22}

echo ""
echo "Параметры подключения:"
echo "  Сервер: $SERVER"
echo "  Порт: $PORT"
echo ""

# Проверка доступности хоста
echo "[1/4] Проверка доступности хоста..."
HOST_ONLY=$(echo $SERVER | cut -d'@' -f2)
if ping -c 1 -W 2 "$HOST_ONLY" &> /dev/null; then
    echo "✅ Хост доступен"
else
    echo "⚠️  Хост не отвечает на ping (возможно, ping заблокирован)"
fi

# Проверка доступности порта
echo ""
echo "[2/4] Проверка доступности порта $PORT..."
if timeout 5 bash -c "cat < /dev/null > /dev/tcp/$HOST_ONLY/$PORT" 2>/dev/null; then
    echo "✅ Порт $PORT открыт"
else
    echo "❌ Порт $PORT недоступен"
    echo "Возможные причины:"
    echo "  - SSH-сервер не запущен"
    echo "  - Неверный порт"
    echo "  - Заблокирован firewall"
    exit 1
fi

# Проверка SSH с verbose режимом
echo ""
echo "[3/4] Тестовое подключение с детальной информацией..."
echo "Нажмите Ctrl+C для прерывания если потребуется..."
sleep 2
ssh -v -p "$PORT" "$SERVER" "echo 'SSH подключение успешно!'; whoami; hostname"

if [ $? -eq 0 ]; then
    echo ""
    echo "[4/4] Проверка ключей и конфигурации..."
    echo ""
    echo "✅ SSH-подключение работает корректно!"
    echo ""
    echo "Полезные команды для этого сервера:"
    echo "  - Обычное подключение: ssh -p $PORT $SERVER"
    echo "  - Выполнить команду: ssh -p $PORT $SERVER 'команда'"
    echo "  - Копировать файл на сервер: scp -P $PORT файл $SERVER:путь"
    echo "  - Копировать с сервера: scp -P $PORT $SERVER:путь файл"
else
    echo ""
    echo "❌ Подключение не удалось."
    echo ""
    echo "Возможные проблемы:"
    echo "  - Неверный логин или пароль"
    echo "  - Проблемы с SSH-ключами"
    echo "  - Пользователь не имеет доступа"
    echo ""
    echo "Для отладки используйте:"
    echo "  ssh -vvv -p $PORT $SERVER"
fi

