import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    filename='bot_errors.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s',
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 300
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}


def get_api_answer(url, current_timestamp):
    """Обращается к API Практикум.Домашка.
    Получает даннные о последней отправленной на ревью работе.
    """
    current_timestamp = current_timestamp or int(time.time())
    payload = {'from_date': current_timestamp}
    response = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params=payload)
    if response.status_code != 200:
        logging.error('Unexpected server response', exc_info=True)
        raise Exception('Invalid rewiew status')
    return response.json()


def check_response(response):
    """Проверяет содержимое ответа после запроса к API."""
    homeworks = response.get('homeworks')
    if not homeworks:
        logging.error('Response is empty', exc_info=True)
        raise Exception('Invalid response')
    homework = homeworks[0]
    status = homework['status']
    if status in HOMEWORK_STATUSES:
        return homework
    logging.error('Invalid rewiew status', exc_info=True)
    raise Exception('Invalid rewiew status')


def parse_status(homework):
    """Оценивает данные, полученные от API.
    Возвращает ответ в зависимости от полученного статуса.
    """
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_STATUSES[homework['status']]
    if homework_name is None:
        logging.error('Result does not '
                      'contains any homework names',
                      exc_info=True)
        raise Exception("Invalid results")
    return f'Изменился статус проверки работы "{homework_name}".\n\n{verdict}'


def send_message(bot, message):
    """Обращается к API Телеграмма и после отправляет Боту сообщение."""
    logging.info('Message was successfully sent')
    try:
        bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception:
        logging.error('Something went wrong. '
                      'Bot is unavalible',
                      exc_info=True)


def main():
    """Управляет логикой работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            get_api_answer_main = get_api_answer(ENDPOINT, current_timestamp)
            check_response_main = check_response(get_api_answer_main)
            if check_response_main:
                parse_status_result = parse_status(check_response_main)
                send_message(bot, parse_status_result)
            time.sleep(RETRY_TIME)
        except Exception:
            logging.error('Something went wrong. '
                          'Bot is unavalible',
                          exc_info=True)
            bot.send_message(
                chat_id=CHAT_ID,
                text='HELP ME! Something went wrong'
            )
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
