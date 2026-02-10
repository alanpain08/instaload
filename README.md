# Instagram Downloader Telegram Bot

Телеграм-бот для скачивания видео из Instagram по ссылке (Reels / Post / TV) и отправки пользователю в ответном сообщении.

## Что умеет бот

- Принимает текстовое сообщение со ссылкой на Instagram.
- Поддерживает ссылки вида:
  - `https://www.instagram.com/reel/...`
  - `https://www.instagram.com/p/...`
  - `https://www.instagram.com/tv/...`
- Извлекает `shortcode` из ссылки и скачивает медиа через `instaloader`.
- Отправляет найденный `.mp4` в Telegram с подписью из описания поста.
- Ограничивает частоту запросов для каждого пользователя (`RATE_LIMIT = 10` секунд).
- Чистит временные файлы после обработки запроса.
- Может работать:
  - без авторизации Instagram;
  - с авторизацией через `INSTAGRAM_USERNAME`/`INSTAGRAM_PASSWORD`;
  - с сохранённой сессией Instaloader (`session-<username>`).

## Стек

- Python 3.11
- [aiogram 2.x](https://docs.aiogram.dev/en/v2.25.1/)
- [instaloader](https://instaloader.github.io/)
- Docker / Docker Compose

## Структура проекта

- `bot.py` — основной код Telegram-бота.
- `config.py` — чтение переменных окружения из `.env`.
- `requirements.txt` — зависимости Python.
- `Dockerfile` — сборка Docker-образа.
- `docker-compose.yml` — запуск через Docker Compose.
- `downloads/` — временная папка для скачанных файлов (создаётся автоматически).

## Переменные окружения

Создайте файл `.env` в корне проекта:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота

# Опционально (если нужен логин в Instagram)
INSTAGRAM_USERNAME=ваш_логин
INSTAGRAM_PASSWORD=ваш_пароль
```

> `TELEGRAM_BOT_TOKEN` обязателен. Без него бот не запустится.

## Локальный запуск (без Docker)

### 1) Требования

- Python 3.11+
- `pip`

### 2) Установка зависимостей

```bash
python -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt
```

### 3) Настройка `.env`

Создайте `.env` по примеру выше.

### 4) Запуск

```bash
python bot.py
```

После запуска в логах появится статус входа в Instagram и сообщение о старте бота.

## Запуск через Docker (локально)

### Вариант 1: Docker Compose (рекомендуется)

```bash
docker compose up --build -d
```

Проверить логи:

```bash
docker compose logs -f bot
```

Остановить:

```bash
docker compose down
```

### Вариант 2: Docker CLI

Сборка образа:

```bash
docker build -t instaload-bot .
```

Запуск контейнера:

```bash
docker run -d \
  --name instaload-bot \
  --env-file .env \
  -v $(pwd)/downloads:/app/downloads \
  instaload-bot
```

Логи:

```bash
docker logs -f instaload-bot
```

Остановка и удаление:

```bash
docker rm -f instaload-bot
```

## Развертывание на сервере через Docker

Ниже универсальный сценарий для Linux-сервера (VPS).

### 1) Установите Docker и Compose

Для Ubuntu (пример):

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo systemctl enable --now docker
```

### 2) Склонируйте проект

```bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> instaload
cd instaload
```

### 3) Создайте `.env`

```bash
cp .env.example .env  # если добавите шаблон в репозитории
# или создайте файл вручную
nano .env
```

Минимум нужен `TELEGRAM_BOT_TOKEN`.

### 4) Запустите сервис

```bash
docker compose up --build -d
```

### 5) Проверьте состояние

```bash
docker compose ps
docker compose logs -f bot
```

### 6) Обновление после изменений

```bash
git pull
docker compose up --build -d
```

## Полезные замечания

- Если Instagram возвращает `401`, укажите `INSTAGRAM_USERNAME` и `INSTAGRAM_PASSWORD` в `.env` или используйте сохранённую сессию Instaloader.
- Если пост приватный или удалён, бот вернёт ошибку `Пост не найден`.
- Бот работает в режиме long polling (webhook не требуется).

## Возможные улучшения

- Добавить `.env.example`.
- Добавить `restart: unless-stopped` в `docker-compose.yml`.
- Добавить healthcheck для контейнера.
- Настроить systemd unit для автозапуска compose-проекта.
