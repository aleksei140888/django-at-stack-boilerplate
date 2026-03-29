#!/bin/bash
set -e

echo "Waiting for database..."
while ! python -c "import psycopg2; psycopg2.connect('${DATABASE_URL}')" 2>/dev/null; do
    sleep 1
done
echo "Database is ready."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"
