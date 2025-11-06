#!/bin/bash
# Примеры использования SCP для копирования файлов
# Кейс 3: Копирование файлов с помощью SCP

echo "========================================="
echo "Примеры использования SCP"
echo "========================================="
echo ""

# Проверка аргументов
if [ $# -eq 0 ]; then
    echo "Этот скрипт демонстрирует различные примеры использования SCP."
    echo ""
    echo "Использование: $0 user@host"
    echo ""
    echo "Пример: $0 alex@192.168.1.100"
    echo ""
    echo "Основные команды SCP:"
    echo ""
    echo "1. Копирование файла на сервер:"
    echo "   scp файл user@host:/путь/на/сервере"
    echo ""
    echo "2. Копирование файла с сервера:"
    echo "   scp user@host:/путь/к/файлу ./локальный-файл"
    echo ""
    echo "3. Копирование директории (рекурсивно):"
    echo "   scp -r директория user@host:/путь/"
    echo ""
    echo "4. Копирование с сохранением атрибутов:"
    echo "   scp -p файл user@host:/путь/"
    echo ""
    echo "5. Копирование через нестандартный порт:"
    echo "   scp -P 2222 файл user@host:/путь/"
    echo ""
    echo "6. Копирование нескольких файлов:"
    echo "   scp файл1 файл2 файл3 user@host:/путь/"
    echo ""
    echo "7. Копирование с ограничением скорости (1024 Kbit/s):"
    echo "   scp -l 1024 файл user@host:/путь/"
    echo ""
    echo "8. Копирование с verbose режимом:"
    echo "   scp -v файл user@host:/путь/"
    echo ""
    exit 0
fi

SERVER=$1
REMOTE_USER=$(echo $SERVER | cut -d'@' -f1)
REMOTE_HOST=$(echo $SERVER | cut -d'@' -f2)

echo "Сервер: $SERVER"
echo ""

# Создание тестовых файлов и директорий
echo "[1/5] Создание тестовых файлов..."
mkdir -p test_scp
echo "Тестовый файл 1 - $(date)" > test_scp/file1.txt
echo "Тестовый файл 2 - $(date)" > test_scp/file2.txt
echo "Тестовый файл 3 - $(date)" > test_scp/file3.txt

mkdir -p test_scp/subdirectory
echo "Файл в поддиректории - $(date)" > test_scp/subdirectory/subfile.txt

echo "✅ Созданы тестовые файлы в директории test_scp/"
ls -lR test_scp/

# Копирование одного файла на сервер
echo ""
echo "[2/5] Копирование одного файла на сервер..."
scp test_scp/file1.txt "$SERVER:/tmp/"

if [ $? -eq 0 ]; then
    echo "✅ Файл file1.txt скопирован на сервер в /tmp/"
else
    echo "❌ Ошибка копирования"
    exit 1
fi

# Копирование нескольких файлов
echo ""
echo "[3/5] Копирование нескольких файлов..."
scp test_scp/file1.txt test_scp/file2.txt test_scp/file3.txt "$SERVER:/tmp/"

if [ $? -eq 0 ]; then
    echo "✅ Файлы скопированы на сервер"
else
    echo "❌ Ошибка копирования"
fi

# Копирование директории рекурсивно
echo ""
echo "[4/5] Копирование директории рекурсивно..."
scp -r test_scp "$SERVER:/tmp/"

if [ $? -eq 0 ]; then
    echo "✅ Директория test_scp/ скопирована на сервер"
else
    echo "❌ Ошибка копирования"
fi

# Копирование файла с сервера обратно
echo ""
echo "[5/5] Копирование файла с сервера обратно..."
scp "$SERVER:/tmp/file1.txt" ./downloaded_file.txt

if [ $? -eq 0 ]; then
    echo "✅ Файл успешно скопирован с сервера"
    echo "Содержимое скачанного файла:"
    cat downloaded_file.txt
else
    echo "❌ Ошибка копирования с сервера"
fi

# Проверка на сервере
echo ""
echo "[Проверка] Проверка файлов на сервере..."
ssh "$SERVER" "ls -lh /tmp/file*.txt /tmp/test_scp/ 2>/dev/null"

echo ""
echo "========================================="
echo "✅ Демонстрация SCP завершена!"
echo "========================================="
echo ""
echo "Для очистки тестовых файлов:"
echo "  Локально: rm -rf test_scp/ downloaded_file.txt"
echo "  На сервере: ssh $SERVER 'rm -rf /tmp/test_scp /tmp/file*.txt'"

