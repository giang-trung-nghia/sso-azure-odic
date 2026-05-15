#!/bin/sh
set -e
python manage.py migrate --noinput
exec gunicorn app.wsgi:application \
  --bind "0.0.0.0:${DJANGO_PORT:-8001}" \
  --workers 2 \
  --threads 2 \
  --access-logfile - \
  --error-logfile -
