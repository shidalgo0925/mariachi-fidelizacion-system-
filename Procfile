web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: celery -A app.celery worker --loglevel=info
beat: celery -A app.celery beat --loglevel=info
