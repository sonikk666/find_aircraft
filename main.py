import json
import time

from get_url_aircrafts import get_all_aircrafts, get_new_soup


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
        # Итератор по словарю для получения ключей
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
        if len(all_flights) >= 2:  # for debug => история двух полётов
            break  # for debug => история двух полётов
    # Записать историю всех полётов в общий словарь данных о самолёте
    one_aircraft.update({'flights_history': all_flights})
    return one_aircraft


def main():
    """Главная функция программы."""
    print('======START program=======')
    # Получить список словарей только с рег.номером и url самолётов
    all_aircrafts = get_all_aircrafts()
    n = 0
    for one_aircraft in all_aircrafts:
        # Получить полную информацию об одном самолёте
        full_info = full_info_one_aircraft(one_aircraft)
        # Обновить её в общем списке самолётов
        all_aircrafts[n] = full_info
        # Сразу записываем в файл информацию о каждом самолёте,
        # чтобы можно было прерывать программу без потери уже собранных данных
        with open('media/data.json', 'w') as outfile:
            json.dump(all_aircrafts, outfile, sort_keys=False, indent=None)
        print(f'Записали инфу в файл о самолёте № {n}')
        # Подождать перед переходом на страницу другого самолёта
        n += 1
        time.sleep(3.5)
    print('=======END program=======')


if __name__ == '__main__':
    try:
        n = 0
        # Зацикливаем программу для работы по таймеру
        while True:
            main()
            n += 1
            print(f'Прошёл запуск программы № {n}')
            print('Подождать 5 сек перед повторением программы')
            time.sleep(5)
    except KeyboardInterrupt:
        print('Exit to Ctrl+C!')
