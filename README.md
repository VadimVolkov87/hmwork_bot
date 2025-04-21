## homework_bot
Приложение "homework_bot" предназначено для получения статуса проверки проектов учащегося Яндекс Практикума за последние 2 недели, отправки сообщений в телеграм бот пользователя с логированием ошибок и сбоев.

## Стек приложения
Приложение создано на основе:

* Python 3.9.13
* pyTelegramBotAPI 4.14.1
* python-dotenv 0.20.0
* requests 2.26.0

## Для запуска проекта необходимо
Клонировать репозиторий:

```bash
git clone https://github.com/VadimVolkov87/homework_bot.git
```

Перейти в корневую папку приложения:

```bash
cd homework_bot
```

Создать и активировать виртуальное окружение:

```bash
python -m venv venv
```

```bash
source venv/Scripts/activate
```

Установить пакеты из файла зависимостей:

```bash
pip install -r requirements.txt
```

В корне проекта создать файл .env

Внести в файл следующие переменные:

* PRACTICUM_TOKEN - токен для авторизации в API Практикум Домашка
* TELEGRAM_TOKEN - токен для работы с API бота
* TELEGRAM_CHAT_ID - ID телеграм аккаунта в который необходимо отсылать сообщения

Запустить приложение:

```bash
python homework.py
```

## Автор проекта

[Вадим Волков](https://github.com/VadimVolkov87/)
