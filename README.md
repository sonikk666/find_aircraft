# Find_aircraft

## Скраппер для flightradar24

### Описание

Даёт возможность:

- Собрать всю информацию о выбранных самолётах
- Передать её на сервер в формате JSON для дальнейшей работы в приложении
- Сохранить в файл формата JSON

Принцип работы:

- Делает запрос на www.flightradar24.com/data/aircraft, потом в каждую основную aircraft_family (exp. ATR42)
- С каждой aircraft_family (порядка 18шт) собирает рег_номера и URL-страницы самолётов в список словарей
- Далее проходит по каждой странице самолёта и собирает с неё всю информацию
- Отправляет данные в JSON формате на указанный сервер
- Пишет логи в файл и в поток
P.S.: принадлежность стране определяется по префиксу в рег_номере

Как пользоваться (для Linux):

- запустить проект в dev-режиме для установки зависимостей в виртуальном окружении (смотрите ниже)
- отредактировать файл find_aircraft.service, указав в нём путь к развёрнутому проекту
- поместить файл find_aircraft.service в папку /etc/systemd/system/
- затем выполнить последовательно команды:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable find_aircraft.service
    sudo systemctl start find_aircraft.service
    sudo systemctl status find_aircraft.service
    ```

- запустить файл AircraftUI (при условии установленного Qt)

Для Windows - смотрите Запуск в dev-режиме

### Технологии

Python 3.11

BeautifulSoup 4.12.2

### Как запустить проект в dev-режиме

Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone https://github.com/sonikk666/find_aircraft

cd find_aircraft
```

Создать и активировать виртуальное окружение:

Для Linux:

```bash
python3 -m venv venv

source venv/bin/activate
```

Для Windows:

```bash
python -m venv venv

. venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```bash
python -m pip install --upgrade pip

pip install -r requirements.txt
```

Запустить проект:

```bash
python find_aircraft.py
```

### Автор

Никита Михайлов
