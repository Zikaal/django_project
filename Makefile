.PHONY: build up down restart logs app frontend migrate clear superuser help

# Переменные по умолчанию
DOCKER_COMPOSE = docker compose

help: ## Показать список доступных команд
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ==============================================================================
# УПРАВЛЕНИЕ ОКРУЖЕНИЕМ (Docker)
# ==============================================================================
up: ## Запуск всех контейнеров в фоновом режиме
	$(DOCKER_COMPOSE) up -d
	@echo "==================================================================="
	@echo "✅ Контейнеры запущены! Начинается фоновая инициализация (БД, зависимости)..."
	@echo "⏳ Транслируем логи в консоль до завершения запуска:"
	@echo "-------------------------------------------------------------------"
	@$(DOCKER_COMPOSE) logs --tail=200 -f app 2>&1 | grep -m1 "Backend App Service is ready and running!" >/dev/null || true
	@echo "-------------------------------------------------------------------"
	@echo "🎉 Запуск прошел успешно! Терминал свободен."
	@echo "🌍 Веб Приложение (Nginx): http://localhost:8086"
	@echo "🗄️  База данных (Adminer): http://localhost:8084"
	@echo "📧 Почта (Mailpit): http://localhost:8027"
	@echo "==================================================================="

down: ## Остановка и удаление всех сервисов
	$(DOCKER_COMPOSE) down

restart: down up ## Перезапуск всех сервисов

logs: ## Просмотр логов всех сервисов
	$(DOCKER_COMPOSE) logs -f

logs-app: ## Просмотр логов только Django сервиса
	$(DOCKER_COMPOSE) logs -f app

# ==============================================================================
# DJANGO И РАЗРАБОТКА
# ==============================================================================
manage: ## Запуск произвольной команды manage.py (пример: make manage migrate)
	$(DOCKER_COMPOSE) exec app python manage.py $(filter-out $@,$(MAKECMDGOALS))

shell: ## Запуск интерактивной консоли Django Shell
	$(DOCKER_COMPOSE) exec app python manage.py shell

clear: ## Сборка статики
	$(DOCKER_COMPOSE) exec app python manage.py collectstatic --noinput

# ==============================================================================
# БАЗА ДАННЫХ И МИГРАЦИИ
# ==============================================================================
migrations: ## Создание новых миграций (makemigrations)
	$(DOCKER_COMPOSE) exec app python manage.py makemigrations

migrate: ## Запуск миграций базы данных (migrate)
	$(DOCKER_COMPOSE) exec app python manage.py migrate

superuser: ## Создание нового суперпользователя (createsuperuser)
	$(DOCKER_COMPOSE) exec app python manage.py createsuperuser

user: ## Создание первого администратора (логин: admin, пароль: pass1234)
	$(DOCKER_COMPOSE) exec app python manage.py seed_user

data: ## Запуск генератора большого объема тестовых данных (seed)
	$(DOCKER_COMPOSE) exec app python manage.py seed_data

# ==============================================================================
# QA И ТЕСТИРОВАНИЕ
# ==============================================================================
test: ## Запуск тестов Django
	$(DOCKER_COMPOSE) exec app python manage.py test

# ==============================================================================
# QA И АНАЛИЗ КОДА (Ruff)
# ==============================================================================
format-check: ## Проверка стиля кода без сохранения файлов (Dry Run)
	$(DOCKER_COMPOSE) exec app ruff check .
	$(DOCKER_COMPOSE) exec app ruff format --check .

format: ## Авто-форматирование кода и импортов через Ruff
	$(DOCKER_COMPOSE) exec app ruff check --fix .
	$(DOCKER_COMPOSE) exec app ruff format .

# ==============================================================================
# ДОСТУП В КОНТЕЙНЕРЫ И ПРОЧЕЕ
# ==============================================================================
app: ## Интерактивный терминал (bash) внутри Django контейнера
	$(DOCKER_COMPOSE) exec app bash

frontend: ## Интерактивный терминал (sh) внутри Frontend (node/tailwind) контейнера
	$(DOCKER_COMPOSE) exec frontend bash

build: ## Пересборка всех Docker-образов (если меняли Dockerfile)
	$(DOCKER_COMPOSE) build

logs-db: ## Просмотр логов MySQL (БД)
	$(DOCKER_COMPOSE) logs -f db

logs-front: ## Просмотр логов Tailwind
	$(DOCKER_COMPOSE) logs -f frontend

# ==============================================================================
# РАБОТА С CELERY
# ==============================================================================

logs-celery: ## Просмотр логов Celery worker
	$(DOCKER_COMPOSE) logs -f celery

celery: ## Интерактивный терминал внутри Celery контейнера
	$(DOCKER_COMPOSE) exec celery bash

restart-celery: ## Перезапуск Celery worker
	$(DOCKER_COMPOSE) restart celery
