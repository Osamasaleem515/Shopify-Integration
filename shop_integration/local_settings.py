from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Override database settings for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Celery settings for local development
CELERY_TASK_ALWAYS_EAGER = True

# Redis settings for local development (using port 6380)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Windows-specific Celery settings
CELERY_WORKER_POOL = 'solo'  # Use solo pool for Windows compatibility
CELERY_WORKER_CONCURRENCY = 1  # Single worker for Windows 