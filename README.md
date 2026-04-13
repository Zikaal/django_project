# Oil Production System (Django)

Веб-приложение на Django для учета нефтяных компаний, сотрудников, скважин и суточных рапортов по добыче нефти.

Проект включает:
- учет пользователей и профилей
- учет нефтяных компаний и скважин
- суточные рапорты по добыче
- dashboard с графиками
- импорт рапортов из Excel
- экспорт месячного сводного отчета в `.xlsx`
- Docker-окружение
- фоновую обработку задач через Redis/Celery
- ролевую модель доступа по компаниям и действиям

---

## Что нового в текущей версии

В проект внедрена ролевая модель бизнес-процесса:

- **Admin** — полный доступ, управление компаниями, пользователями и ролями
- **Manager** — доступ только к своей компании, своим скважинам, своим рапортам и dashboard своей компании
- **Operator** — доступ только к рапортам своей компании, без dashboard, без управления компаниями и скважинами

Также реализовано:
- ограничение данных по `oil_company`
- object-level доступ к рапортам
- скрытие недоступных действий в шаблонах
- правило: **Operator не может редактировать или удалять рапорты старше 7 дней**
- единый слой access-логики через permission-функции, mixin'ы и template tags

---

## Возможности проекта

### Пользователи и профили
- регистрация, вход и выход
- список пользователей с фильтрацией, сортировкой и пагинацией
- создание, редактирование и удаление пользователей
- профиль текущего пользователя
- редактирование своего профиля
- загрузка аватара
- дополнительные поля профиля:
  - нефтяная компания
  - отдел
  - телефон
  - bio

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

### Суточные рапорты
- список рапортов с фильтрацией по:
  - компании
  - скважине
  - диапазону дат
- создание, редактирование и удаление рапортов
- валидация уникальности `well + date`
- расчет добычи нефти по формуле
- импорт рапортов из Excel
- экспорт месячного отчета в Excel
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
- фильтрация по диапазону дат
- полноэкранный просмотр графиков

---

## Ролевая модель доступа

### Admin
- управляет пользователями
- назначает роли
- создает, редактирует и удаляет компании
- видит все компании, все скважины и все рапорты
- имеет доступ ко всем разделам, включая dashboard, импорт и экспорт

### Manager
- работает только в рамках своей `oil_company`
- видит dashboard только своей компании
- управляет скважинами своей компании
- работает только с рапортами своей компании
- может использовать импорт и экспорт
- не управляет пользователями и не редактирует компании как Admin

### Operator
- работает только с рапортами своей компании
- не имеет доступа к dashboard
- не управляет компаниями
- не управляет скважинами
- не видит импорт и экспорт
- не может редактировать или удалять рапорты старше 7 дней

---

## Изоляция данных по компании

Даже если пользователь вручную подставит `URL`, `id`, `company` или `well`, доступ к чужим данным ограничен на backend.

Ограничения реализованы через:
- scoped queryset во view
- ограничение queryset полей формы (`well`, `oil_company`)
- доступ к объектам только через отфильтрованный queryset
- mixin'ы для ролей и company-scope

Это защищает:
- список скважин
- создание и редактирование скважин
- список рапортов
- создание и редактирование рапортов
- dashboard

---

## Ограничение для Operator по старым рапортам

Реализовано бизнес-правило:

- если пользователь — `Operator`
- и дата рапорта старше 7 дней

то:
- редактирование запрещено
- удаление запрещено
- кнопки действий скрыты в интерфейсе
- прямой доступ по URL также запрещен на backend

---

## Архитектура доступа

В проекте есть единый слой access-логики:

- `accounts/utils.py` — permission-функции и object-level проверки
- `accounts/mixins.py` — mixin'ы для views
- `accounts/templatetags/access_tags.py` — доступ к permission-логике в шаблонах

Примеры используемых функций:
- `is_admin(user)`
- `is_manager(user)`
- `is_operator(user)`
- `get_user_company(user)`
- `can_manage_users(user)`
- `can_manage_companies(user)`
- `can_manage_wells(user)`
- `can_access_dashboard(user)`
- `can_edit_dailyproduction_obj(user, report)`
- `can_delete_dailyproduction_obj(user, report)`

---

## Технологии

- Python 3.11
- Django 5+
- MySQL 8.3
- SQLite3 для локального режима
- Redis
- Celery
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
├── accounts/                 # пользователи, профили, роли, access-логика
├── companies/                # нефтяные компании
├── productions/              # скважины, рапорты, dashboard, Excel import/export
├── config/                   # settings, urls, wsgi, asgi
├── theme/                    # Tailwind theme app
├── docker-compose/           # entrypoint и nginx-конфиг
├── media/                    # загруженные файлы и аватары
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

> `oil_company` может быть пустой для Admin. Для Manager и Operator компания должна быть назначена.

### `Well`
- `name`
- `oil_company`
- `type`
- `max_drilling_depth`
- `latitude`
- `longitude`

### `DailyProduction`
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

Та же формула используется:
- в dashboard
- в ORM-агрегациях
- в Excel-экспорте

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

Также поддерживаются алиасы заголовков, например:
- `скважина`
- `дата`
- `время работы`
- `дебит жидкости`
- `обводненность`
- `плотность нефти`

Импорт:
- пропускает пустые строки
- валидирует дату и числовые поля
- ищет скважину по имени
- сохраняет корректные записи
- возвращает количество созданных строк, пропусков и список ошибок

> Импорт доступен только `Admin` и `Manager`.

### Экспорт
Экспортирует месячный сводный отчет в `.xlsx`.

В файл попадают:
- компания
- скважина
- количество рапортов
- суммарный дебит жидкости
- средняя обводненность
- суммарная чистая нефть

> Экспорт доступен только `Admin` и `Manager`.

---

## Интерфейс

Проект использует Tailwind CSS и ориентирован на корпоративный интерфейс.

Реализовано:
- единый `base.html`
- верхняя навигация с учетом ролей
- таблицы и мобильные карточки
- формы с современным UI
- аватар пользователя в шапке
- dashboard с графиками
- модальные окна для импорта / экспорта
- скрытие недоступных действий по ролям и объектам

---

## Основные маршруты

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

Пример находится в `.env.example`.

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

### Режимы БД
Проект поддерживает два режима:

1. `DB_CONNECTION=mysql` — основной Docker-сценарий
2. любой другой `DB_CONNECTION` — локальный SQLite (`db.sqlite3`)

---

## Запуск через Docker

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
- создаст `.env` из `.env.example`, если его нет
- дождётся готовности MySQL
- выполнит миграции
- соберёт static
- запустит Gunicorn

### 3. Создать суперпользователя
```bash
make superuser
```

### 4. Создать группы и назначить permissions
```bash
python manage.py create_groups
```

### 5. Доступные сервисы
- приложение через Nginx: `http://localhost:8086`
- Django Admin: `http://localhost:8086/admin/`
- прямой доступ к Django app: `http://localhost:8006`
- Adminer: `http://localhost:8084`
- Mailpit: `http://localhost:8027`
- MySQL: `localhost:3308`

### 6. Остановить проект
```bash
make down
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
Скопируйте `.env.example` в `.env` и при желании переключите БД на SQLite:

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

### 4. Создать группы ролей
```bash
python manage.py create_groups
```

### 5. Создать пользователя
```bash
python manage.py createsuperuser
```

### 6. Запустить сервер
```bash
python manage.py runserver
```

> Для полноценной работы Tailwind watcher в локальном режиме понадобится Node.js, так как проект использует `django-tailwind`.

---

## Полезные команды

### Docker / Make
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

### Django
```bash
make migrate
make migrations
make shell
make manage migrate
make manage createsuperuser
python manage.py create_groups
```

### Тестовые данные
```bash
make user
make data
python manage.py seed_user
python manage.py seed_test_data
python manage.py seed_data
python manage.py seed_100_companies
python manage.py seed_wells_for_companies
python manage.py seed_daily_productions_2025
python manage.py reset_wells_and_dailyproductions
```

---

## Валидация и ограничения

### На уровне модели и формы
- `work_time` от `0` до `24`
- `water_cut` от `0` до `100`
- `well + date` должны быть уникальны

### На уровне доступа
- `Manager` и `Operator` видят только данные своей компании
- `Operator` не имеет доступа к скважинам, компаниям и dashboard
- `Operator` не может редактировать и удалять старые рапорты
- `Admin` имеет полный доступ

### Импорт Excel
- дата должна быть распознаваема
- числовые поля должны корректно парситься
- скважина должна существовать в БД

---

## Тесты

В проекте уже есть unit- и feature-тесты.

Запуск:
```bash
make test
```
или
```bash
python manage.py test
```

> После внедрения ролевой модели рекомендуется дополнительно проверить сценарии доступа для `Admin / Manager / Operator`, включая прямой доступ по URL и правило 7 дней для Operator.

---

## Качество кода

Для линтинга и форматирования используется Ruff.

Команды:
```bash
make format-check
make format
```

---

## Что уже реализовано

По текущей кодовой базе уже реализованы:
- Django auth + профили
- нефтяные компании
- скважины
- суточные рапорты
- dashboard
- Excel import/export
- Docker-окружение
- роли и permissions
- ограничение данных по компаниям
- object-level доступ к рапортам
- правило 7 дней для Operator
- единый слой access-логики

---

## Примечания

- В репозитории может присутствовать `db.sqlite3`, но основной Docker-сценарий рассчитан на MySQL.
- Медиафайлы сохраняются в директорию `media/`.
- В режиме `DEBUG=True` Django раздаёт media через `config/urls.py`.

---

## Лицензия

Укажи свою лицензию или оставь этот раздел пустым, если проект внутренний.
