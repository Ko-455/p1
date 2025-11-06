#!/bin/bash
# Скрипт генерации SSH-ключей и настройки безпарольного входа
# Кейс 4: Работа с ключами SSH

echo "========================================="
echo "Генерация SSH-ключей"
echo "========================================="
echo ""

# Запрос email для комментария
read -p "Введите ваш email для комментария к ключу: " EMAIL

if [ -z "$EMAIL" ]; then
    EMAIL="user@localhost"
fi

# Выбор типа ключа
echo ""
echo "Выберите тип ключа:"
echo "1) RSA 4096 бит (традиционный, широко поддерживается)"
echo "2) Ed25519 (современный, более быстрый и безопасный)"
read -p "Ваш выбор (1 или 2): " KEY_TYPE

case $KEY_TYPE in
    1)
        KEY_ALGORITHM="rsa"
        KEY_BITS=4096
        KEY_FILE="$HOME/.ssh/id_rsa"
        ;;
    2)
        KEY_ALGORITHM="ed25519"
        KEY_BITS=""
        KEY_FILE="$HOME/.ssh/id_ed25519"
        ;;
    *)
        echo "Неверный выбор. Используется RSA 4096."
        KEY_ALGORITHM="rsa"
        KEY_BITS=4096
        KEY_FILE="$HOME/.ssh/id_rsa"
        ;;
esac

# Создание директории .ssh если её нет
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Проверка существующих ключей
if [ -f "$KEY_FILE" ]; then
    echo ""
    echo "⚠️  Ключ $KEY_FILE уже существует!"
    read -p "Хотите перезаписать? (y/N): " OVERWRITE
    if [ "$OVERWRITE" != "y" ] && [ "$OVERWRITE" != "Y" ]; then
        echo "Операция отменена."
        exit 0
    fi
fi

# Генерация ключа
echo ""
echo "Генерация ключа..."
if [ -n "$KEY_BITS" ]; then
    ssh-keygen -t "$KEY_ALGORITHM" -b "$KEY_BITS" -C "$EMAIL" -f "$KEY_FILE"
else
    ssh-keygen -t "$KEY_ALGORITHM" -C "$EMAIL" -f "$KEY_FILE"
fi

# Проверка успешности
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ SSH-ключи успешно сгенерированы!"
    echo "========================================="
    echo ""
    echo "Приватный ключ: $KEY_FILE"
    echo "Публичный ключ: ${KEY_FILE}.pub"
    echo ""
    echo "Содержимое публичного ключа:"
    echo "-----------------------------------"
    cat "${KEY_FILE}.pub"
    echo "-----------------------------------"
    echo ""
    
    # Предложение скопировать ключ на сервер
    read -p "Хотите скопировать ключ на удаленный сервер? (y/N): " COPY_KEY
    if [ "$COPY_KEY" = "y" ] || [ "$COPY_KEY" = "Y" ]; then
        read -p "Введите адрес сервера (user@host): " SERVER
        if [ -n "$SERVER" ]; then
            echo "Копирование ключа на $SERVER..."
            ssh-copy-id -i "${KEY_FILE}.pub" "$SERVER"
            
            if [ $? -eq 0 ]; then
                echo ""
                echo "✅ Ключ успешно скопирован на сервер!"
                echo "Теперь вы можете подключиться без пароля:"
                echo "  ssh $SERVER"
            else
                echo "❌ Ошибка при копировании ключа."
            fi
        fi
    fi
    
    echo ""
    echo "Дополнительные команды:"
    echo "  - Добавить ключ в ssh-agent: ssh-add $KEY_FILE"
    echo "  - Скопировать ключ на сервер: ssh-copy-id -i ${KEY_FILE}.pub user@host"
    echo "  - Подключиться с ключом: ssh -i $KEY_FILE user@host"
else
    echo "❌ Ошибка при генерации ключей."
    exit 1
fi

