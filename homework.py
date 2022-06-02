"""
-Перед запуском проверяет наличие токенов:
PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID;
-Отправляет запрос на ENDPOINT;
-Проверяет полученный ответ на корректность;
-Из полученного ответа извлекает значения двух ключей:
homework_name и status;
-Отправляет пользователю значение двух ключей выше,
либо сообщение об ошибке.
"""

import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_SECRET_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_SECRET_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_SECRET_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    handlers=[logging.StreamHandler()],
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s'
)
logger = logging.getLogger(__name__)

error_sent_messages = []


class APIAnswerError(Exception):
    """Кастомная ошибка при незапланированной работе API."""
    pass


def send_message(bot, message):
    """Отправляет сообщение пользователю."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Отправлено сообщение: "{message}"')
    except Exception as error:
        logging.error(f'Ошибка отправки сообщения, ошибка: {error}')


def log_and_inform(bot, message):
    """Логирует ошибки уровня ERROR.
    Однократно отправляет информацию об ошибках в телеграм,
    если отправка возможна.
    """
    logger.error(message)
    if message not in error_sent_messages:
        try:
            send_message(bot, message)
            error_sent_messages.append(message)
        except Exception as error:
            logger.info('Не удалось отправить сообщение об ошибке, '
                        f'{error}')


def get_api_answer(current_timestamp):
    """Делает запрос к ENDPOINT."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception:
        message = 'Поведение API не соответствует ожидаемому'
        raise APIAnswerError(message)
    try:
        if response.status_code != HTTPStatus.OK:
            message = 'Код статуса ответа отличается от 200:OK'
            raise Exception(message)
    except Exception:
        message = 'API ведет себя незапланированно'
        raise APIAnswerError(message)
    return response.json()


def check_response(response):
    """Проверяет полученный ответ на корректность."""
    if not isinstance(response, dict):
        message = 'Ответ API вернул не словарь'
        raise TypeError(message)
    if ['homeworks'][0] not in response:
        message = 'В ответе API нет домашней работы'
        raise IndexError(message)
    homework = response['homeworks']
    return homework[0]


def parse_status(homework):
    """Парсит ответ API по ключам homework_name и status."""
    keys = ['status', 'homework_name']
    for key in keys:
        if key not in homework:
            message = f'Ключ {key} отсутствует в ответе API'
            raise KeyError(message)
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        message = 'Неизвестный статус домашней работы'
        raise KeyError(message)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return None not in tokens


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    check_result = check_tokens()
    if check_result is False:
        message = 'Проблемы с переменными окружения'
        logger.critical(message)
        raise SystemExit(message)

    while True:
        try:
            response = get_api_answer(current_timestamp)
            if 'current_date' in response:
                current_timestamp = response['current_date']
            homework = check_response(response)
            if homework is not None:
                message = parse_status(homework)
                if message is not None:
                    send_message(bot, message)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            log_and_inform(bot, message)
            time.sleep(RETRY_TIME)
        else:
            logger.error('Сбой в работе программы')


if __name__ == '__main__':
    main()
