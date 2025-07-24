from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Override database settings for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable Celery for local development
CELERY_TASK_ALWAYS_EAGER = True 