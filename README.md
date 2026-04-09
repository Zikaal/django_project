# Oil Production System (Django)

Веб-приложение на Django для учета сотрудников, нефтяных компаний, скважин и суточных рапортов по добыче нефти.

Проект уже включает не только базовый CRUD, но и рабочий dashboard, загрузку Excel-файлов, экспорт сводного месячного отчета в `.xlsx`, профиль пользователя с аватаром, Docker-окружение и набор management commands для генерации тестовых данных.

---

## Что умеет проект

### Пользователи и профили
- регистрация, вход и выход из системы
- список пользователей с фильтрацией, сортировкой и пагинацией
- создание, редактирование и удаление пользователей
- отдельный профиль текущего пользователя
- редактирование профиля и загрузка аватара
- дополнительные поля профиля:
  - нефтяная компания
  - отдел
  - телефон
  - bio / описание

### Компании
- список нефтяных компаний
- создание, редактирование и удаление компаний
- фильтрация по региону
- сортировка по названию и региону

### Скважины
- список скважин
- создание, редактирование и удаление скважин
- фильтрация по компании
- сортировка
- хранение технических параметров и координат

### Суточные рапорты по добыче
- список рапортов с фильтрацией по:
  - компании
  - скважине
  - диапазону дат
- создание, редактирование и удаление рапортов
- валидация уникальности `скважина + дата`
- расчет добычи нефти по формуле
- импорт рапортов из Excel
- экспорт месячного сводного отчета в Excel
- модальные окна импорта и экспорта прямо на странице списка рапортов

### Dashboard
- KPI-карточки:
  - компании
  - скважины
  - сотрудники
  - суточные рапорты
- графики на Chart.js:
  - динамика добычи по датам
  - топ скважин по добыче
  - распределение скважин по компаниям
  - распределение сотрудников по компаниям
- фильтрация по нескольким компаниям
- фильтрация по диапазону дат
- полноэкранный просмотр графиков

---

## Технологии

- Python 3.11
- Django 5+
- MySQL 8.3
- SQLite3 (как альтернативный локальный вариант)
- Redis
- Gunicorn
- Nginx
- Tailwind CSS (`django-tailwind`)
- openpyxl
- Pillow
- Ruff
- Docker / Docker Compose
- Adminer
- Mailpit

---

## Архитектура проекта

```text
base_project/
├── accounts/                 # пользователи, профили, формы, views, auth
├── companies/                # нефтяные компании + команды заполнения данных
├── productions/              # скважины, рапорты, dashboard, Excel import/export
├── config/                   # settings, urls, wsgi, asgi
├── theme/                    # Tailwind theme app
├── docker-compose/           # entrypoint и nginx-конфиг
├── media/                    # загруженные аватары
├── manage.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

---

## Основные модели

### `OilCompany`
Поля:
- `name`
- `region`

### `Profile`
Связана с `User` через `OneToOneField`.

Поля:
- `user`
- `oil_company`
- `bio`
- `department`
- `phone_number`
- `avatar`

### `Well`
Поля:
- `name`
- `oil_company`
- `type`
- `max_drilling_depth`
- `latitude`
- `longitude`

### `DailyProduction`
Поля:
- `well`
- `date`
- `work_time`
- `liquid_debit`
- `water_cut`
- `oil_density`

Ограничение:
- уникальность записи по паре `well + date`

---

## Бизнес-логика

Для расчета количества добытой нефти используется формула:

```text
Чистая нефть = Дебит жидкости × (1 - Обводненность / 100) × Плотность нефти
```

В коде это доступно как свойство модели:
- `DailyProduction.calculated_oil`

Для dashboard и Excel-экспорта аналогичная формула используется и на уровне ORM-агрегаций.

---

## Excel: импорт и экспорт

### Импорт
Импорт реализован через `openpyxl`.

Поддерживаются обязательные колонки:
- `well`
- `date`
- `work_time`
- `liquid_debit`
- `water_cut`
- `oil_density`

Также поддерживаются некоторые алиасы заголовков, например:
- `скважина`
- `дата`
- `время работы`
- `дебит жидкости`
- `обводненность`
- `плотность нефти`

Импорт:
- пропускает пустые строки
- валидирует дату и числа
- ищет скважину по имени
- сохраняет только корректные записи
- возвращает количество созданных строк, пропусков и список ошибок

### Экспорт
Экспортирует месячный сводный отчет по скважинам в `.xlsx`.

В файл попадают:
- компания
- скважина
- количество рапортов
- суммарный дебит жидкости
- средняя обводненность
- суммарная чистая нефть

---

## Интерфейс

Проект использует Tailwind CSS и ориентирован на админский / корпоративный интерфейс.

Реализовано:
- единый `base.html`
- верхняя навигация
- таблицы и мобильные карточки
- формы с современным UI
- аватар пользователя в шапке
- dashboard с графиками
- модальные окна для импорта / экспорта

---

## Маршруты

### Аутентификация и профиль
- `/accounts/register/`
- `/accounts/login/`
- `/accounts/logout/`
- `/accounts/profile/`
- `/accounts/profile/edit/`
- `/accounts/users/`
- `/accounts/users/create/`

### Компании
- `/companies/`
- `/companies/create/`

### Скважины
- `/productions/wells/`
- `/productions/wells/create/`

### Рапорты
- `/productions/`
- `/productions/create/`
- `/productions/import/`
- `/productions/export/monthly/`

### Dashboard
- `/productions/dashboard/`

### Админка
- `/admin/`

---

## Переменные окружения

Пример находится в файле `.env.example`.

```env
DEBUG=True
SECRET_KEY=django-insecure-change-me-in-production
ALLOWED_HOSTS=*

DB_CONNECTION=mysql
DB_HOST=db
DB_PORT=3306
DB_DATABASE=django_project
DB_USERNAME=root
DB_PASSWORD=root

REDIS_URL=redis://redis:6379/1
```

### Поддерживаемые режимы БД
Проект поддерживает два режима:

1. `DB_CONNECTION=mysql` — основной Docker-сценарий
2. любой другой `DB_CONNECTION` — локальный SQLite (`db.sqlite3`)

---

## Запуск через Docker

Это основной и самый удобный способ запуска проекта.

### 1. Клонирование
```bash
git clone https://github.com/USERNAME/REPOSITORY_NAME.git
cd REPOSITORY_NAME
```

### 2. Поднять окружение
```bash
make up
```

Во время запуска контейнер `app` автоматически:
- создаст `.env` из `.env.example`, если файла нет
- дождётся готовности MySQL
- выполнит миграции
- соберёт static
- запустит Gunicorn

### 3. Доступные сервисы
- приложение через Nginx: `http://localhost:8086`
- Django Admin: `http://localhost:8086/admin/`
- прямой доступ к Django app: `http://localhost:8006`
- Adminer: `http://localhost:8084`
- Mailpit: `http://localhost:8027`
- MySQL: `localhost:3308`

### 4. Создать суперпользователя
```bash
make superuser
```

### 5. Остановить проект
```bash
make down
```

---

## Полезные Make-команды

### Управление контейнерами
```bash
make up
make down
make restart
make logs
make logs-app
make logs-db
make logs-front
make build
```

### Django-команды
```bash
make migrate
make migrations
make shell
make manage migrate
make manage createsuperuser
```

### Пользователи и тестовые данные
```bash
make user        # создаёт первого администратора admin / pass1234
make data        # массовый сидер данных
```

### Тесты и качество кода
```bash
make test
make format-check
make format
```

---

## Локальный запуск без Docker

Подходит для быстрого запуска на SQLite.

### 1. Установить зависимости
```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# или .venv\Scripts\activate на Windows
pip install -r requirements.txt
```

### 2. Создать `.env`
Скопируйте `.env.example` в `.env` и, при желании, переключите БД на SQLite:

```env
DB_CONNECTION=sqlite
DEBUG=True
SECRET_KEY=django-insecure-local-dev
ALLOWED_HOSTS=*
```

### 3. Применить миграции
```bash
python manage.py migrate
```

### 4. Создать пользователя
```bash
python manage.py createsuperuser
```

### 5. Запустить сервер
```bash
python manage.py runserver
```

> Примечание: для полноценной работы Tailwind watcher в локальном режиме понадобится Node.js, так как проект использует `django-tailwind`.

---

## Management commands

В проекте есть несколько полезных management commands.

### Пользователи
```bash
python manage.py seed_user
```
Создаёт администратора:
- username: `admin`
- password: `pass1234`

### Компании, пользователи, скважины
```bash
python manage.py seed_test_data
```
Создаёт:
- тестовые компании
- пользователей
- профили
- скважины

### Массовая генерация данных
```bash
python manage.py seed_data
```
Генерирует:
- 22 компании
- сотрудников
- скважины
- историю рапортов

### Дополнительные сидеры
```bash
python manage.py seed_100_companies
python manage.py seed_wells_for_companies
python manage.py seed_daily_productions_2025
python manage.py reset_wells_and_dailyproductions
```

---

## Валидация

### На уровне модели и формы
- `work_time` от `0` до `24`
- `water_cut` от `0` до `100`
- `well + date` должны быть уникальны

### Импорт Excel
- дата должна быть распознаваема
- числовые поля должны корректно парситься
- скважина должна существовать в БД

---

## Тесты

В проекте уже есть unit- и feature-тесты.

Покрываются, в частности:
- проверка форм пользователей
- проверка логики создания профиля
- создание скважин
- создание рапортов
- запрет дубликатов по `well + date`
- расчет `calculated_oil`
- ограничения `work_time` и `water_cut`

Запуск:
```bash
make test
```
или
```bash
python manage.py test
```

---

## Качество кода

Для линтинга и форматирования используется Ruff.

Конфигурация находится в `pyproject.toml`.

Команды:
```bash
make format-check
make format
```

---

## Что уже сделано по состоянию проекта

Судя по текущей кодовой базе, уже реализованы:
- Django auth + регистрация
- профили сотрудников
- компании
- скважины
- суточные рапорты
- dashboard
- Tailwind UI
- Excel import/export
- Docker-окружение
- тесты
- сидеры данных

Часть будущих улучшений и roadmap-идей дополнительно описаны в `TASKS.md`.

---

## Примечания

- В репозитории присутствует `db.sqlite3`, но основной Docker-сценарий рассчитан на MySQL.
- Медиафайлы пользователей сохраняются в директорию `media/`.
- В `DEBUG=True` Django раздаёт media через `config/urls.py`.

---

## Лицензия

При необходимости добавьте сюда выбранную лицензию проекта.
