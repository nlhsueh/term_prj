#!/bin/bash

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist (Only if not in production or for first setup)
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123', role='professor', student_id='PROF01', has_changed_password=True)
END

# Start server (Development or Gunicorn)
# Use Railway's $PORT or default to 8000
APP_PORT=${PORT:-8000}

if [ "$DEBUG" = "False" ]; then
    gunicorn core.wsgi --bind 0.0.0.0:$APP_PORT
else
    python manage.py runserver 0.0.0.0:$APP_PORT
fi
