#!/bin/bash
# Run migrations and collect static files on deployment
python manage.py migrate
python manage.py collectstatic --noinput
