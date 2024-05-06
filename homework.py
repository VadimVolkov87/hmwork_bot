"""Модуль робота для проверки статуса домашних работ в Практикум."""
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

global homework_previous_status
homework_previous_status = 'No status'
global logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)


def check_tokens(variables):
    """Функция проверки доступности переменных окружения."""
    for variable in list(variables.keys()):
        if variables[variable] is None:
            logger.critical(
                f'''Отсутствует обязательная переменная окружения:
                "{variable}". Программа остановлена.''',
                exc_info=True
            )
            sys.exit()


def send_message(bot, message):
    """Функция отсылки сообщения в Телеграмм."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.debug('Бот отправил сообщение')
    except Exception as error:
        raise Exception(f'Сбой отправки сообщения в Телеграм {error}.')


def get_api_answer(timestamp=1549962000):
    """Функция запроса к API-сервису Практикума."""
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS,
                                params={'from_date': timestamp})
        response.raise_for_status()
    except requests.RequestException:
        raise requests.RequestException(
            f'''Сбой в работе программы: Эндпоинт {ENDPOINT}
недоступен. Код ответа API: {response.status_code}'''
        )
    else:
        if response.status_code != HTTPStatus.OK:
            raise Exception(f'''Сбой в работе программы: Эндпоинт {ENDPOINT}
недоступен. Код ответа API: {response.status_code}''')
    return response.json()


def check_response(response):
    """Функция проверки ответа API на наличие данных."""
    if type(response) is not dict:
        raise TypeError(f'''Ответ не соотвествует ожидаемому:
                        {type(response)}''')
    if 'homeworks' not in response:
        raise Exception(f'''В ответе нет ожидаемых ключей
                        {list(response.keys())}''')
    if type(response['homeworks']) is not list:
        raise TypeError(f'''Ответ не соответствует ожидаемому.
                        {type(response['homeworks'])}''')


def parse_status(homework):
    """Функция подготовки сообщения для отправки."""
    if ('status' not in homework) or (homework['status'] is None):
        raise Exception('Неопределённый статус домашней работы.')
    global homework_previous_status
    try:
        'homework_name' in list(homework.keys())
        status = homework['status']
        homework_name = homework['homework_name']
        if status not in HOMEWORK_VERDICTS:
            raise Exception(f'''Статус работы "{homework_name}"
            не соответствует стандартному: {status}.''')
        if homework_previous_status == status:
            logger.debug(f'Статус работы "{homework_name}"не изменился.')
            return f'Статус работы "{homework_name}" не изменился.'
        for verdict in list(HOMEWORK_VERDICTS.keys()):
            if verdict == status:
                verdict = HOMEWORK_VERDICTS[status]
                homework_previous_status = status
                return f'''Изменился статус проверки работы "{homework_name}".
                    {verdict}'''
    except Exception:
        raise Exception(f'''Статус работы "{homework_name}"
            не соответствует стандартному: {status}.''')


def main():
    """Основная логика работы бота."""
    environment_variables = {
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - RETRY_PERIOD
    global previous_message
    previous_message = ''

    while True:
        try:
            check_tokens(environment_variables)
            response = get_api_answer(timestamp)
            check_response(response=response)
            message = parse_status(response['homeworks'][0])
        except requests.RequestException as error:
            logger.error(f'{error}', exc_info=True)
            message = f'{error}'
        except TypeError as error:
            logger.error(f'{error}', exc_info=True)
            message = f'{error}'
        except Exception as error:
            logger.error(f'{error}', exc_info=True)
            message = f'{error}'
        try:
            if message != previous_message:
                send_message(bot=bot, message=message)
                previous_message = message
        except Exception as error:
            logger.error(f'{error}', exc_info=True)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
