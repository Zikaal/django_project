# Oil Production System (Django)

### Разработчик: Зинетов Алихан (Astana IT University)

Веб-приложение на Django для учета нефтяных компаний, сотрудников, скважин и суточных рапортов по добыче нефти.

Проект ориентирован на корпоративный сценарий, где важны:
- разграничение доступа по ролям и компаниям;
- централизованное хранение производственных данных;
- импорт/экспорт Excel;
- фоновая обработка тяжелых операций;
- аудит изменений и уведомления пользователям.

---

## Что умеет система

### Пользователи и роли
- аутентификация через Django auth;
- профиль пользователя с дополнительными полями;
- роли `Admin`, `Manager`, `Operator` через Django Groups;
- разграничение доступа по компании и по типу действий.

### Компании и скважины
- CRUD для нефтяных компаний;
- CRUD для скважин;
- фильтрация, сортировка и поиск по основным сущностям;
- ограничение доступа к чужим данным на backend.

### Суточные рапорты
- создание, редактирование и удаление рапортов;
- проверка уникальности пары `well + date`;
- расчет объема чистой нефти по формуле;
- список с фильтрами по компании, скважине и диапазону дат.

### Dashboard
- KPI-карточки;
- графики на Chart.js;
- фильтрация по компаниям и датам;
- кэширование тяжелых агрегатов;
- полноэкранный просмотр графиков.

### Excel
- импорт суточных рапортов из `.xlsx`;
- экспорт месячного сводного отчета в `.xlsx`;
- обработка в фоне через Celery;
- уведомления и email по результату операции.

### API
- токен-аутентификация для мобильного/внешнего клиента;
- endpoint текущего пользователя;
- endpoint создания суточного рапорта;
- единый JSON-формат ошибок через custom exception handler.

---

## Бизнес-правила доступа

### Admin
- полный доступ ко всем компаниям, скважинам, пользователям и рапортам;
- доступ к dashboard, импорту, экспорту и административным разделам.

### Manager
- работает только в рамках своей `oil_company`;
- видит dashboard своей компании;
- управляет скважинами и рапортами своей компании;
- может запускать импорт и экспорт.

### Operator
- работает только с рапортами своей компании;
- не управляет компаниями и скважинами;
- не имеет доступа к dashboard;
- не имеет доступа к импорту/экспорту;
- не может редактировать или удалять рапорты старше 7 дней.

### Изоляция данных
Даже если пользователь вручную изменит URL или попытается передать чужой `id`, доступ все равно ограничен на backend через:
- scoped queryset во view;
- object-level проверки;
- ограничение queryset в формах;
- permission-функции и mixin'ы.

---

## Основные доменные сущности

### `OilCompany`
Нефтяная компания.

Поля:
- `name`
- `region`

### `Profile`
Профиль пользователя, связанный с `User` через `OneToOneField`.

Поля:
- `user`
- `oil_company`
- `department`
- `phone_number`
- `bio`
- `avatar`

### `Well`
Скважина, принадлежащая компании.

Поля:
- `name`
- `oil_company`
- `type`
- `max_drilling_depth`
- `latitude`
- `longitude`

### `DailyProduction`
Суточный производственный рапорт.

Поля:
- `well`
- `date`
- `work_time`
- `liquid_debit`
- `water_cut`
- `oil_density`

Особенности:
- уникальность по паре `well + date`;
- вычисляемое свойство `calculated_oil`.

### `DailyProductionImportJob`
Фоновая задача импорта Excel-файла.

Хранит:
- исходный файл;
- статус;
- счетчики созданных и пропущенных строк;
- ошибки;
- пользователя, который загрузил файл.

### `MonthlyProductionExportJob`
Фоновая задача подготовки месячного Excel-отчета.

Хранит:
- период отчета;
- статус;
- ссылку на готовый файл;
- факт повторного использования кэша.

### `ProductionAuditLog`
Журнал аудита изменений суточных рапортов.

Фиксирует:
- создание / изменение / удаление;
- кто выполнил действие;
- какие поля изменились;
- старые и новые значения.

---

## Формула расчета нефти

Для расчета количества добытой нефти используется формула:

```text
Чистая нефть = Дебит жидкости × (1 - Обводненность / 100) × Плотность нефти
```

Эта логика используется:
- в модели `DailyProduction`;
- в dashboard;
- в ORM-агрегациях;
- в Excel-экспорте.

---

## Excel: импорт и экспорт

### Импорт `.xlsx`
Импорт реализован через `openpyxl` и `Celery`.

Обязательные колонки:
- `well`
- `date`
- `work_time`
- `liquid_debit`
- `water_cut`
- `oil_density`

Поддерживаются и русские алиасы заголовков, например:
- `скважина`
- `дата`
- `время работы`
- `дебит жидкости`
- `обводненность`
- `плотность нефти`

Что делает импорт:
- открывает workbook;
- определяет колонки по заголовкам;
- пропускает пустые строки;
- ищет скважину по имени;
- валидирует данные через существующую Django-форму;
- сохраняет только корректные записи;
- формирует счетчики и список ошибок.

После завершения:
- обновляется статус `DailyProductionImportJob`;
- инвалидируется кэш dashboard и export;
- создается внутреннее уведомление;
- при наличии email отправляется письмо пользователю.

### Экспорт `.xlsx`
Экспорт формирует месячный сводный отчет по всем рапортам за выбранный месяц.

В отчет попадают:
- компания;
- скважина;
- количество рапортов;
- суммарный дебит жидкости;
- средняя обводненность;
- суммарная чистая нефть.

Особенности:
- сборка выполняется в фоне через Celery;
- используется кэширование готовых файлов по месяцу/году и версии данных;
- пользователю приходит уведомление о готовности файла.

---

## Уведомления и аудит

### Уведомления
Приложение `notifications` отвечает за:
- список уведомлений текущего пользователя;
- пометку одного уведомления как прочитанного;
- пометку всех уведомлений как прочитанных;
- polling endpoint для счетчика непрочитанных.

### Аудит действий
Приложение `productions` ведет журнал изменений рапортов.

Для корректной фиксации автора изменений используется middleware:
- `accounts.middleware.CurrentUserMiddleware`

Он сохраняет текущего пользователя в `ContextVar`, чтобы signals могли определить, кто именно изменил запись.

---

## Архитектура проекта

```text
base_project/
├── accounts/                 # пользователи, профили, роли, access-логика
├── api/                      # REST API и токен-аутентификация
├── companies/                # нефтяные компании
├── config/                   # settings, urls, celery, wsgi, asgi
├── notifications/            # внутренние уведомления
├── productions/              # скважины, рапорты, dashboard, Excel, аудит
│   └── services/             # excel_import / excel_export
├── theme/                    # Tailwind theme app
├── docker-compose/           # entrypoint и nginx-конфиги
├── resources/                # примеры тестовых файлов
├── media/                    # загруженные файлы
├── manage.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

---

## Технологии

- Python 3.11
- Django 5+
- Django REST Framework
- MySQL 8.3
- SQLite3 для локальной разработки
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

## Быстрый старт через Docker

### 1. Подготовить переменные окружения
Скопируйте `.env.example` в `.env`:

```bash
cp .env.example .env
```

### 2. Поднять окружение

```bash
make up
```

Во время запуска:
- контейнер `db` поднимает MySQL;
- контейнер `redis` используется как broker/result backend и cache;
- контейнер `app` запускает Django/Gunicorn;
- контейнер `frontend` запускает Tailwind watcher;
- контейнер `celery` выполняет фоновые задачи;
- контейнер `nginx` проксирует веб-приложение.

### 3. Выполнить миграции
Если они не были выполнены автоматически при старте:

```bash
make migrate
```

### 4. Создать группы ролей

```bash
make group
```

или

```bash
python manage.py create_groups
```

### 5. Создать администратора

```bash
make superuser
```

или для быстрого тестового аккаунта:

```bash
make user
```

Команда `make user` создает пользователя:
- login: `admin`
- password: `pass1234`

### 6. Открыть сервисы
- веб-приложение: `http://localhost:8086`
- Django admin: `http://localhost:8086/admin/`
- прямой app-сервис: `http://localhost:8006`
- Adminer: `http://localhost:8084`
- Mailpit UI: `http://localhost:8027`
- MySQL: `localhost:3308`

### 7. Остановить окружение

```bash
make down
```

---

## Локальный запуск без Docker

Подходит для быстрого старта на SQLite.

### 1. Создать виртуальное окружение

```bash
python -m venv .venv
```

Linux / macOS:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Создать `.env`

Пример минимальной конфигурации для локальной разработки:

```env
DEBUG=True
SECRET_KEY=django-insecure-local-dev
ALLOWED_HOSTS=*
DB_CONNECTION=sqlite
REDIS_URL=redis://127.0.0.1:6379/1
REDIS_CACHE_URL=
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

> Если `REDIS_CACHE_URL` не задан, проект автоматически использует `LocMemCache` как fallback.

### 4. Применить миграции

```bash
python manage.py migrate
```

### 5. Создать роли и суперпользователя

```bash
python manage.py create_groups
python manage.py createsuperuser
```

### 6. Запустить Django

```bash
python manage.py runserver
```

### 7. Запустить Celery отдельно
Если нужен импорт/экспорт в фоне:

```bash
celery -A config worker -l INFO
```

> Для полноценной локальной работы Tailwind потребуется Node.js, так как проект использует `django-tailwind`.

---

## Переменные окружения

Пример файла уже есть в `.env.example`.

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
REDIS_CACHE_URL=redis://redis:6379/2
EXPORT_CACHE_TIMEOUT=43200

EMAIL_HOST=mailpit
EMAIL_PORT=1025
DEFAULT_FROM_EMAIL=noreply@base-project.local
```

### Режимы БД
Проект поддерживает два сценария:

1. `DB_CONNECTION=mysql` — основной Docker-сценарий;
2. любое другое значение `DB_CONNECTION` — локальный SQLite (`db.sqlite3`).

---

## Web-маршруты

### Accounts
- `/accounts/login/`
- `/accounts/logout/`
- `/accounts/register/`
- `/accounts/profile/`
- `/accounts/profile/edit/`
- `/accounts/users/`
- `/accounts/users/create/`

### Companies
- `/companies/`
- `/companies/create/`
- `/companies/<id>/edit/`
- `/companies/<id>/delete/`

### Productions
- `/productions/dashboard/`
- `/productions/`
- `/productions/create/`
- `/productions/<id>/edit/`
- `/productions/<id>/delete/`
- `/productions/import/`
- `/productions/export/monthly/`
- `/productions/export/monthly/<id>/download/`
- `/productions/wells/`
- `/productions/wells/create/`
- `/productions/wells/<id>/edit/`
- `/productions/wells/<id>/delete/`

### Notifications
- `/notifications/`
- `/notifications/poll/`
- `/notifications/<id>/read/`
- `/notifications/read-all/`

### Admin
- `/admin/`

---

## API v1

### Получить токен
```http
POST /api/v1/auth/token/
```

### Проверка доступности API
```http
GET /api/v1/health/
```

### Текущий пользователь
```http
GET /api/v1/me/
```

### Создать суточный рапорт
```http
POST /api/v1/reports/daily/
```

### Аутентификация API
Проект поддерживает:
- `SessionAuthentication`
- `TokenAuthentication`

По умолчанию API требует авторизацию.

---

## Команды Makefile

### Управление окружением
```bash
make up
make down
make restart
make build
make logs
make logs-app
make logs-db
make logs-front
make logs-celery
```

### Django
```bash
make manage migrate
make manage createsuperuser
make shell
make migrate
make migrations
make superuser
make group
```

### Тестовые данные
```bash
make user
make data
python manage.py seed_user
python manage.py seed_data
python manage.py seed_test_data
python manage.py seed_100_companies
python manage.py seed_wells_for_companies
python manage.py seed_daily_productions_2025
python manage.py reset_wells_and_dailyproductions
```

### Тесты и качество кода
```bash
make test
make format-check
make format
```

---

## Полезные файлы в репозитории

- `resources/daily_production_import_test_2024_2025.xlsx` — пример Excel-файла для проверки импорта;
- `TASKS.md` — список задач/этапов по развитию проекта;
- `.env.example` — шаблон конфигурации окружения.

---

## Важные замечания

- В проекте есть fallback на SQLite и локальный cache, поэтому минимальный запуск возможен даже без полного Docker-стека.
- Для фоновых задач импорта и экспорта желательно запускать Redis и Celery.
- Dashboard и экспорт используют cache versioning: при изменении рапортов версии кэша обновляются автоматически.
- Проект использует `debug_toolbar` в dev-режиме.
- `TIME_ZONE` сейчас установлен в `UTC`; при внедрении в production это стоит проверить отдельно с учетом локального бизнес-сценария.

---

