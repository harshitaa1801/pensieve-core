web: gunicorn main.wsgi:application --bind 0.0.0.0:8000
worker: celery -A main worker --loglevel=info --concurrency=2
beat: celery -A main beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
