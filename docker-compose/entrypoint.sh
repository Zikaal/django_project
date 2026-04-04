#!/bin/bash
set -e

if [ "$1" = "gunicorn" ]; then
    if [ ! -f .env ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
    fi

    echo "Waiting for MySQL database to be ready..."

    DB_HOST=$(grep -E '^DB_HOST=' .env | cut -d '=' -f 2 | tr -d '\r\n"')
    DB_HOST=${DB_HOST:-db}

    DB_PORT=$(grep -E '^DB_PORT=' .env | cut -d '=' -f 2 | tr -d '\r\n"')
    DB_PORT=${DB_PORT:-3306}

    until nc -z -v -w30 "$DB_HOST" "$DB_PORT"; do
      echo "Waiting for database connection..."
      sleep 3
    done

    echo "Running migrations..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    # python manage.py tailwind build --no-input || true
    python manage.py collectstatic --noinput

    echo "-------------------------------------------------------"
    echo "✅ Backend App Service is ready and running!"
    echo "-------------------------------------------------------"
fi

exec "$@"
