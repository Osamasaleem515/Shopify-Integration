# Docker-specific settings
# This file overrides local_settings.py for Docker containers

# Use PostgreSQL in Docker
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'shopify_integration',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'db',
        'PORT': '5432',
    }
}

# Celery settings for Docker
CELERY_TASK_ALWAYS_EAGER = False
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

# Disable Windows-specific settings in Docker
CELERY_WORKER_POOL = 'prefork'  # Use prefork pool for Linux
CELERY_WORKER_CONCURRENCY = 2  # Multiple workers for Linux 