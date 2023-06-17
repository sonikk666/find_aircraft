import json
import logging
import socket
import sys
import time
from http import HTTPStatus

import requests
from bs4 import BeautifulSoup

DEBUG = False
RETRY_TIME = 600 if not DEBUG else 10
LOGGING_LEVEL = logging.INFO if not DEBUG else logging.DEBUG
AIRCRAFT_COUNT = 2  # используется, если DEBUG = True

HEAD_URL = ('https://www.flightradar24.com')
SERVER_IP = socket.gethostbyname(socket.gethostname())  # IP-адрес этой машины
SERVER_PORT = 5050  # укажите желаемый открытый порт

# PATH_TO_LOG = '/home/<username>/<path_to_folder>/aircraft_logger.log'
# PATH_TO_JSON = '/home/<username>/<path_to_folder>/data.json'
PATH_TO_LOG = 'media/aircraft_logger.log'
PATH_TO_JSON = 'media/data.json'


class AircraftError(Exception):
    """Общий класс ошибок Aircraft."""
    pass


class SendError(AircraftError):
    """Общая ошибка передачи данных на сервер."""
    pass


def get_logger() -> logging.Logger:
    """Задаются параметры логирования."""
    logger = logging.getLogger(__name__)
    logger.setLevel(LOGGING_LEVEL)
    fileHandler = logging.FileHandler(
        PATH_TO_LOG, mode='a', encoding='UTF-8'
    )
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s - %(name)s'
    )
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    fileHandler.setFormatter(formatter)
    streamHandler.setFormatter(formatter)
    return logger


def time_of_function(func):
    """Декоратор для вычисления времени выполнения функции."""
    def wrapper():
        start_time = time.time()
        result = func()
        end_time = time.time()
        run_time_for_sec = round(end_time-start_time, 1)
        run_time_for_min = round((end_time-start_time)/60, 1)
        logger.debug(
            'Время выполнения программы составляет :'
            f'{run_time_for_sec} сек. или {run_time_for_min} мин.'
        )
        return result
    return wrapper


def get_new_soup(url: str) -> BeautifulSoup:
    """Получение нового набора данных с указанного url."""
    # Создать сессию и получить страницу
    required_headers = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/104.0.5112.102 Safari/537.36 '
            'OPR/90.0.4480.84 (Edition Yx 08)'
    }
    session = requests.session()
    response = session.get(url, headers=required_headers)

    # Если слишком много запросов в заданный период времени
    if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
        # Узнать количество времени для ожидания
        time_sleep = int(response.headers.get('Retry-After'))
        logger.info(f'Too many requests - Time for sleep {time_sleep+1} sec')
        # Подождать нужное время
        time.sleep(time_sleep + 1)
        # Повторить запрос на тот же url
        response = session.get(url, headers=required_headers)
    elif response.status_code != HTTPStatus.OK:
        logger.error(f'ERROR!!!   Status code = {response.status_code}')
        response = session.get(url, headers=required_headers)
    return BeautifulSoup(response.text, 'html.parser')


def find_aircraft_family(new_soup: BeautifulSoup) -> list[str]:
    """Сбор информации о семействах самолётов.
    На выходе получает список url'ов семейств самолётов.
    """
    urls_aircraft_family = []
    family_codes = new_soup.find_all(title="Aircraft family code")
    for code in family_codes:
        relative_path = code.get('href')
        url_family = f'{HEAD_URL}{relative_path}'
        urls_aircraft_family.append(url_family)
    return urls_aircraft_family


def parsing_aircraft_family(urls_aircraft_family: list[str]) -> list[dict]:
    """Сбор информации о самолётах в каждом семействе.
    Возвращает список всех самолётов, удовлетворяющих заданному условию.
    """
    n = 0
    all_aircrafts = []
    for one_url in urls_aircraft_family:
        # Получить набор самолётов с каждого url
        family_soup = get_new_soup(one_url)
        all_aircrafts_one_family = family_soup.find_all(class_="regLinks")
        # В каждом наборе получить reg_number и url для каждого самолёта
        for aircraft in all_aircrafts_one_family:
            relative_path = aircraft.get('href')
            url_aircraft = f'{HEAD_URL}{relative_path}'
            reg_number = aircraft.string.strip()
            # Рег_номер самолётов Китая начинается с "B"
            if 'B-' in reg_number[0:2]:
                n += 1
                # Упаковать данные в словарь и добавить в список всех самолётов
                # one_aircraft = reg_number, url_aircraft
                one_aircraft = {
                    'reg_number': reg_number,
                    'url_aircraft': url_aircraft,
                }
                all_aircrafts.append(one_aircraft)
                logger.debug(f'Нашли самолёт № {n}')
                if DEBUG and len(all_aircrafts) >= AIRCRAFT_COUNT:  # for debug
                    break  # for debug
        if DEBUG and len(all_aircrafts) >= AIRCRAFT_COUNT:  # for debug
            break  # for debug
        time.sleep(4)
    return all_aircrafts


def get_all_aircrafts() -> list[dict]:
    """Функция для получения списка всех самолётов.
    Содержит словари с рег.номером самолёта и его url на сайте.
    """
    new_soup = get_new_soup(f'{HEAD_URL}/data/aircraft/')
    urls_aircraft_family = find_aircraft_family(new_soup)
    all_aircrafts = parsing_aircraft_family(urls_aircraft_family)
    return all_aircrafts


def full_info_one_aircraft(one_aircraft: dict) -> dict:
    """Сбор информации об одном самолёте.
    Добавляет полученные данные к словарю самолёта.
    """
    # Получить url самолёта
    url_aircraft = one_aircraft.get('url_aircraft')
    # Получить набор данных со страницы одного самолёта
    one_aircraft_soup = get_new_soup(url_aircraft)
    # Выбрать набор данных с параметрами самолёта
    aircraft_params = one_aircraft_soup.find_all(class_='row p-l-20 p-t-5')
    m = 0
    for one_param in aircraft_params:
        # Получаем label и value и сразу записываем в словарь самолёта
        label = one_param.label.text.replace(" ", "_").lower()
        # Так как label == 'code' встречается дважды, то
        # изменить название для каждого label
        if label == 'code' and m == 0:
            label += '_airline'
            m += 1
        elif label == 'code' and m == 1:
            label += '_operator'
        value = one_param.span.text.strip()
        # Записать параметры в общий словарь данных о самолёте
        one_aircraft.update({label: value})

    all_flights = []  # история всех полётов одного самолёта
    # Выбрать набор данных с историей полётов
    flights_history = one_aircraft_soup.find_all(
        'div', class_='row table-row-responsive'
    )
    for one_history in flights_history:
        # История одного полёта
        one_flight = {
            'flight': '',
            'date': '',
            'time': '',
            'landed': '',
        }
        # Информация с левой части экрана разработки
        left_history = one_history.find('div', class_='col-xs-3')
        left_history = left_history.find_all('div', class_='row')
        # Итератор по словарю one_flight для получения ключей
        iter_one_flight = iter(one_flight)
        for one_left in left_history:
            val = next(iter_one_flight)
            one_flight.update({val: one_left.text.strip()})
        # Информация с правой части экрана разработки
        right_history = one_history.find('div', class_='col-xs-8')
        right_history = right_history.find_all('p')
        for one_right in right_history:
            label = one_right.label.text.strip().lower()
            value = one_right.span.text.strip()
            one_flight.update({label: value})
        # Добавить инфу одного полёта в список для всех полётов
        all_flights.append(one_flight)
        if DEBUG and len(all_flights) >= 2:  # for debug => количество полётов
            break
    # Записать историю всех полётов в общий словарь данных о самолёте
    one_aircraft.update({'flights_history': all_flights})
    return one_aircraft


@time_of_function
def get_info_aircrafts() -> list[dict]:
    """Наполняет список словарей самолётов всеми данными."""
    # Получить список словарей самолётов с рег.номером и url
    all_aircrafts = get_all_aircrafts()
    for n, one_aircraft in enumerate(all_aircrafts, start=0):
        # Получить полную информацию об одном самолёте
        full_info = full_info_one_aircraft(one_aircraft)
        # Обновить её в общем списке самолётов
        all_aircrafts[n] = full_info
        if DEBUG:
            # Сразу записываем в файл информацию о каждом самолёте,
            # чтобы можно было прерывать программу без потери собранных данных
            with open(PATH_TO_JSON, 'w') as outfile:
                json.dump(all_aircrafts, outfile, sort_keys=False, indent=2)

        logger.debug(f'Собрали данные о самолёте № {n+1}')
        if (n + 1) % 10 == 0:
            logger.info(f'Собрали данные о самолёте № {n+1}')
        # Подождать перед переходом на страницу другого самолёта
        time.sleep(5)
    return all_aircrafts


def send_to_server(aircrafts_info: list[dict]) -> None:
    """Отправка данных на сервер.
    Принимает список словарей. Конвертирует в json перед отправкой.
    """
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, SERVER_PORT))
        j_array = json.dumps(aircrafts_info)
        len_bytes_array = len(bytes(j_array, encoding="utf-8"))
        data = {
            "type": "select_aircraft",
            "result": aircrafts_info,
            "length_array": len_bytes_array
        }
        json_data = json.dumps(data)
        client.sendall(bytes(json_data, encoding="utf-8"))
        client.close()
    except Exception as error:
        raise SendError(f'Сбой при отправке данных на сервер - {error}')


def main():
    """Основная логика работы программы."""
    # Зацикливаем программу c работой по таймеру
    n = 0
    while True:
        try:
            logger.info('======START program=======')
            aircrafts_info = get_info_aircrafts()
            send_to_server(aircrafts_info)
        except SendError as error:
            logger.error(f'SendError: {error}')
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
        finally:
            n += 1
            logger.info('=======END program=======')
            logger.info(f'Прошёл запуск программы № {n}')
            if DEBUG and n == 3:
                exit()  # for debug
            logger.info(
                f'Подождать перед повторением программы - {RETRY_TIME} сек'
            )
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logger = get_logger()
    try:
        if DEBUG:
            logger.critical(f'!!! DEBUG !!! САМОЛЁТОВ = {AIRCRAFT_COUNT} шт')
        main()
    except KeyboardInterrupt:
        logger.info('Exit to Ctrl+C!')
        # TODO: попробовать сделать отправку json
        sys.exit(0)
