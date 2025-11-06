

## Содержание

1. [Кейс 1: Установка SSH-сервера](#кейс-1-установка-ssh-сервера)
2. [Кейс 2: Подключение к серверу](#кейс-2-подключение-к-серверу)
3. [Кейс 3: Копирование файлов (SCP)](#кейс-3-копирование-файлов-scp)
4. [Кейс 4: SSH-ключи](#кейс-4-ssh-ключи)


---

## Кейс 1: Установка SSH-сервера

### Установка

```bash
sudo apt-get update
sudo apt-get install openssh-server -y
```

### Управление службой

```bash
sudo systemctl start ssh
sudo systemctl enable ssh
sudo systemctl status ssh
```

### Проверка порта

```bash
sudo ss -tulpn | grep :22
```

### Базовая настройка

```bash
sudo nano /etc/ssh/sshd_config
```

Рекомендуемые параметры:
```
Port 22
PermitRootLogin no
PasswordAuthentication yes
PubkeyAuthentication yes
```

После изменений:
```bash
sudo systemctl restart ssh
```

---

## Кейс 2: Подключение к серверу

### Узнать IP сервера

```bash
hostname -I
```

### Подключение

```bash
ssh username@192.168.1.100
```

### Подключение через нестандартный порт

```bash
ssh -p 2222 username@192.168.1.100
```

### Выполнение команды без интерактивного режима

```bash
ssh username@192.168.1.100 "ls -la"
```

### Отключение

```bash
exit
```

---

## Кейс 3: Копирование файлов (SCP)

### Создание тестового файла

```bash
echo "Test content" > test_file.txt
```

### Копирование на сервер

```bash
scp test_file.txt username@192.168.1.100:/home/username/
```

### Копирование с сервера

```bash
scp username@192.168.1.100:/home/username/test_file.txt ./downloaded.txt
```

### Копирование директории

```bash
scp -r directory username@192.168.1.100:/home/username/
```

### Дополнительные опции

```bash
scp -p file user@host:/path/          # Сохранение атрибутов
scp -P 2222 file user@host:/path/     # Нестандартный порт
scp -l 1024 file user@host:/path/     # Ограничение скорости (Kbit/s)
```

---

## Кейс 4: SSH-ключи

### Генерация ключей

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

Или RSA:
```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

### Копирование ключа на сервер

```bash
ssh-copy-id username@192.168.1.100
```

Или вручную:
```bash
cat ~/.ssh/id_ed25519.pub | ssh username@192.168.1.100 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### Настройка прав

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### Подключение с ключом

```bash
ssh username@192.168.1.100
```

### SSH config

Создать `~/.ssh/config`:
```
Host myserver
    HostName 192.168.1.100
    User username
    IdentityFile ~/.ssh/id_ed25519
```

Использование:
```bash
ssh myserver
```

### Использование ssh-agent

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

