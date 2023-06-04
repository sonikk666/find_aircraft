"""Получает список кортежей со всеми самолётами по заданному условию."""
import time
from http import HTTPStatus

import requests
from bs4 import BeautifulSoup

HEAD_URL = (
    'https://www.flightradar24.com'
)


def get_new_soup(url: str) -> BeautifulSoup:
    """Получение нового набора данных с указанного url."""
    # Создать сессию и получить страницу
    required_headers = {
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0',
        'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/104.0.5112.102 Safari/537.36 OPR/90.0.4480.84 (Edition Yx 08)'
    }
    session = requests.session()
    response = session.get(url, headers = required_headers)

    # Если слишком много запросов в заданный период времени
    if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
        # Узнать количество времени для ожидания
        time_sleep = int(response.headers.get('Retry-After'))
        print(f'Time for sleep {time_sleep+1} sec')
        # Подождать нужное время
        time.sleep(time_sleep + 1)
        # Повторить запрос на тот же url
        response = session.get(url, headers = required_headers)
    elif response.status_code != HTTPStatus.OK:
        print('ERROR!!!')
        print(response.status_code) # 520
        exit()
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
    На выходе получает список всех самолётов, удовлетворяющих заданному условию.
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
            if 'B-' in reg_number[0:2]:  # for debug
                # Упаковать данные в словарь и добавить в список всех самолётов
                # one_aircraft = reg_number, url_aircraft
                one_aircraft = {
                    'reg_number': reg_number,
                    'url_aircraft': url_aircraft,
                }
                all_aircrafts.append(one_aircraft)
                print(f'Нашли самолёт № {n}')
                n += 1
                # break  # for debug
                if len(all_aircrafts) >= 2:  # for debug
                    break  # for debug
        if len(all_aircrafts) >= 1:  # for debug
            break  # for debug
        time.sleep(3.5)
    return all_aircrafts


def get_all_aircrafts() -> list[dict]:
    """Главная функция для получения списка всех самолётов.
    Содержит словари с рег.номером самолёта и его url на сайте.
    """
    new_soup = get_new_soup(f'{HEAD_URL}/data/aircraft/')
    urls_aircraft_family = find_aircraft_family(new_soup)
    all_aircrafts = parsing_aircraft_family(urls_aircraft_family)
    return all_aircrafts


if __name__ == '__main__':
    print(get_all_aircrafts())
