# коммент, чтобы обновить содержимое файла

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

PRACTICUM_TOKEN = os.getenv('TOKEN_PRACTIKUM')
TELEGRAM_TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 300
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}


def get_api_answer(api_url, current_timestamp):
    """Обращается к API Практикум.Домашка.
    Получает даннные о последней отправленной на ревью работы.
    """
    current_timestamp = current_timestamp or int(time.time())
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    api_url = ENDPOINT
    response = requests.get(
        api_url,
        headers=headers,
        params=payload)
    if response.status_code != 200:
        raise Exception('Invalid server respond')
    logging.error('Ответ сервера не совпал с ожидаемым')
    return response.json()


def check_response(response):
    """Проверяет содержимое ответа после запроса к API."""
    homeworks = response.get('homeworks')
    if homeworks is None:
        raise Exception('Invalid response: response is empty')
    logging.info('Полученный ответ не содержит данных.')
    for homework in homeworks:
        status = homework.get('status')
        if status in HOMEWORK_STATUSES.keys():
            return homeworks
        raise Exception('Invalid rewiew status')
    logging.info('Полученный статус неизвестен.')
    return homeworks


def parse_status(homework):
    """Оценивает данные, полученные от API.
    Возвращает ответ в зависимости от полученного статуса.
    """
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_STATUSES.get(homework.get('status'))
    if homework_name is None:
        raise Exception("No homework name")
    logging.error('В полученном ответе не содержится '
                  'названия работы.')
    if verdict is None:
        raise Exception("No verdict")
    logging.error('В полученном ответе не соержится '
                  'статус работы.')
    for status in verdict:
        if status == verdict:
            verdict = HOMEWORK_STATUSES.get(homework.get('status'))
    return f'Изменился статус проверки работы "{homework_name}".\n\n{verdict}'


def send_message(bot, message):
    """Обращается к API Телеграмма и после отправляет Богу сообщение."""
    logging.info('Сообщение успешно отправлено')
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    """Управляет логикой работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    url = ENDPOINT
    while True:
        try:
            get_api_answer_main = get_api_answer(url, current_timestamp)
            check_response_main = check_response(get_api_answer_main)
            if check_response_main:
                for homework in check_response_main:
                    parse_status_result = parse_status(homework)
                    send_message(bot, parse_status_result)
            time.sleep(RETRY_TIME)
        except Exception:
            logging.error('Что-то пошло не так, Бот недоступен.')
            bot.send_message(
                chat_id=CHAT_ID,
                text='Что-то пошло не так.'
            )
            time.sleep(RETRY_TIME)
            continue


if __name__ == '__main__':
    main()
