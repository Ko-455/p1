#!/bin/bash
# Скрипт для быстрого запуска системы мониторинга

echo "=========================================="
echo "Система мониторинга ресурсов ОС"
echo "=========================================="
echo ""
echo "ВНИМАНИЕ: Запускайте только в виртуальной машине!"
echo ""

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "ОШИБКА: Python3 не найден!"
    exit 1
fi

# Проверка наличия зависимостей
if ! python3 -c "import psutil" 2>/dev/null; then
    echo "Установка зависимостей..."
    pip3 install -r requirements.txt
fi

# Создание директорий для логов и отчётов
mkdir -p monitoring_logs reports

# Запуск системы
echo "Запуск системы мониторинга..."
python3 main_monitor.py --start-leak "$@"


