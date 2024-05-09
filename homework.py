"""Модуль робота для проверки статуса домашних работ в Практикум."""
import logging
import os
import sys
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telebot.apihelper as ta
from dotenv import load_dotenv
from exceptions import (EmptyResponseException, EnvironmentVariableException,
                        WrongResponseCodeException)
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


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s - %(funcName)s - %(lineno)d'
)
handler.setFormatter(formatter)
record_handler = RotatingFileHandler(
    __file__ + '.log', maxBytes=50000000, backupCount=1
)
logger.addHandler(record_handler)
record_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s - %(funcName)s - %(lineno)d'
)
record_handler.setFormatter(record_formatter)


def check_tokens():
    """Функция проверки доступности переменных окружения."""
    variables = {
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for variable in variables:
        flag = True
        if variables[variable] is None:
            flag = False
        if flag is False:
            raise EnvironmentVariableException(
                (f'Отсутствует обязательная переменная окружения:"{variable}".'
                 'Программа остановлена.')
            )


def send_message(bot, message):
    """Функция отсылки сообщения в Телеграмм."""
    global luck_sending
    luck_sending = True
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except ta.ApiException as error:
        luck_sending = False
        logger.error(f'{error}', exc_info=True)
    else:
        logger.debug(f'Бот отправил сообщение {message}')
    return luck_sending


def get_api_answer(timestamp):
    """Функция запроса к API-сервису Практикума."""
    date_for_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp}
    }
    try:
        logger.debug(
            ('Сделан запрос к эндпоинту {url}. '
             'Параметры запроса: '
             '{params}'.format_map(date_for_request))
        )
        response = requests.get(
            url=date_for_request['url'],
            headers=date_for_request['headers'],
            params=date_for_request['params']
        )
        response.raise_for_status()
    except requests.RequestException:
        raise ConnectionError(
            ('Сбой в работе программы: Эндпоинт {url}'
             ' недоступен.'.format(**date_for_request))
        )
    if response.status_code != HTTPStatus.OK:
        raise WrongResponseCodeException(
            (f'Сбой в работе программы: Эндпоинт {response.url} '
             f'недоступен. Ответ API {response.reason}. '
             f'Код ответа API: {response.status_code}')
        )
    return response.json()


def check_response(response):
    """Функция проверки ответа API на наличие данных."""
    logger.debug('Начата проверка ответа API')
    if isinstance(response, dict) is False:
        raise TypeError(
            f'Ответ не соотвествует ожидаемому: {type(response)}'
        )
    if 'homeworks' not in response:
        raise EmptyResponseException(
            'В ответе нет ключа "homeworks".'
        )
    homeworks = response.get('homeworks')
    if isinstance(homeworks, list) is False:
        raise TypeError(
            'Ответ не соответствует ожидаемому типу "list".'
        )
    return homeworks


def parse_status(homework):
    """Функция подготовки сообщения для отправки."""
    if 'status' not in homework:
        raise KeyError('Неопределённый статус домашней работы.')
    if 'homework_name' not in homework:
        raise KeyError('Неопределённый статус домашней работы.')
    global homework_previous_status
    status = homework.get('status')
    homework_name = homework.get('homework_name')
    if status not in HOMEWORK_VERDICTS:
        raise KeyError(
            (f'Статус работы "{homework_name}"'
             f'не соответствует стандартному: {status}.')
        )
    for status_name in HOMEWORK_VERDICTS:
        if status_name == status:
            verdict = HOMEWORK_VERDICTS[status_name]
            homework_previous_status = status
            return (f'Изменился статус проверки работы "{homework_name}".'
                    f'{verdict}')
    return 'Ничего нет'


def main():
    """Основная логика работы бота."""
    try:
        check_tokens()
    except EnvironmentVariableException as error:
        logger.critical(f'{error}', exc_info=True)
        message = f'{error}'
        sys.exit()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response=response)
            message = parse_status(homeworks[0])
        except Exception as error:
            logger.error(f'{error}', exc_info=True)
            message = f'{error}'
        try:
            if message != previous_message:
                send_message(bot=bot, message=message)
                if luck_sending is True:
                    previous_message = message
                    timestamp = response.get('current_date')
        except ta.ApiException as error:
            logger.error(f'{error}', exc_info=True)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
