#!/bin/sh
set -e

# Default: migrate then serve. If a command is passed (e.g. `docker compose run … python manage.py shell`),
# run that command instead so one-off tasks don't start Gunicorn.
if [ "$#" -eq 0 ]; then
  python manage.py migrate --noinput
  exec gunicorn app.wsgi:application \
    --bind "0.0.0.0:${DJANGO_PORT:-8001}" \
    --workers 2 \
    --threads 2 \
    --access-logfile - \
    --error-logfile -
else
  exec "$@"
fi
