import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_SECRET_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_SECRET_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_SECRET_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

error_sent_messages = []


def send_message(bot, message):
    """Отправляет сообщение пользователю в телеграм."""
    logging.info('Начал отправку сообщения')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Отправлено сообщение: "{message}"')
    except telegram.error.TelegramError as error:
        raise exceptions.SendMessageException(error) from error


def get_api_answer(current_timestamp):
    """Делает запрос к ENDPOINT."""
    timestamp = current_timestamp or int(time.time())
    params = dict(
        url=ENDPOINT,
        headers=HEADERS,
        params={'from_date': timestamp}
    )
    logging.info(
        f'Начал запрос к {ENDPOINT} с параметрами {params}')
    try:
        response = requests.get(**params)
        if response.status_code != HTTPStatus.OK:
            message = (f'Код статуса ответа: {response.status_code},'
                       f'причина {response.reason}')
            raise exceptions.APIAnswerError(message)
        return response.json()
    except Exception as e:
        message = 'API ведет себя незапланированно'
        raise exceptions.ConnectionError(message) from e


def check_response(response: dict) -> list:
    """Проверяет полученный ответ на корректность."""
    logging.info('Начал проверку ответа API')
    if not isinstance(response, dict):
        message = f'Ответ API вернул не словарь: {response}'
        raise TypeError(message)
    if 'homeworks' not in response or 'current_date' not in response:
        message = f'В ответе API нет домашней работы: {response}'
        raise exceptions.EmptyAPIAnswer(message)
    homework = response.get('homeworks')
    if not isinstance(homework, list):
        message = f'Неверный формат данных: {response}'
        raise KeyError(message)
    return homework


def parse_status(homework: dict):
    """Парсит ответ API по ключам homework_name и status."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if 'homework_name' not in homework:
        message = f'Неизвестное имя домашней работы: {homework_name}'
        raise KeyError(message)
    if homework_status not in HOMEWORK_VERDICTS:
        message = f'Неизвестный статус домашней работы: {homework_status}'
        raise ValueError(message)
    return (f'Изменился статус проверки работы "{homework_name}".'
            f'{HOMEWORK_VERDICTS[homework_status]}')


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    logging.info('Запуск')
    if not check_tokens():
        message = 'Отсутствует переменные окружения'
        logging.critical(message)
        sys.exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    status = ''
    error_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            homework = check_response(response)
            if homework != status:
                message = parse_status(homework[0])
                if message is not None:
                    send_message(bot, message)
                status = homework
        except Exception as error:
            logging.error(error)
            message = str(error)
            if message != error_message:
                send_message(bot, message)
                error_message = message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '%(asctime)s,'
            '%(levelname)s,'
            '%(message)s,'
            '%(funcName)s,'
            '%(lineno)d'
        ),
        handlers=[logging.FileHandler(
            'main.log',
            mode='w'
        ),
            logging.StreamHandler(sys.stdout)]
    )
    main()
