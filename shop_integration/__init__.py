try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Allow Django to start even if Celery is not installed
    __all__ = ()
    celery_app = None
