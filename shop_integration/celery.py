import os

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_integration.settings')

try:
    from celery import Celery
    from celery.schedules import crontab

    app = Celery('shop_integration')

    # Using a string here means the worker doesn't have to serialize
    # the configuration object to child processes.
    app.config_from_object('django.conf:settings', namespace='CELERY')

    # Load task modules from all registered Django app configs.
    app.autodiscover_tasks()

    # Define the scheduled tasks
    app.conf.beat_schedule = {
        'nightly-inventory-update': {
            'task': 'products.tasks.nightly_inventory_update',
            'schedule': crontab(hour=2, minute=0),  # Run at 2:00 AM every day
            'args': (),
        },
        # Example schedules you can uncomment:
        # 'hourly-inventory-check': {
        #     'task': 'products.tasks.nightly_inventory_update',
        #     'schedule': crontab(minute=0),  # Every hour
        #     'args': (),
        # },
        # 'weekly-inventory-report': {
        #     'task': 'products.tasks.nightly_inventory_update',
        #     'schedule': crontab(day_of_week=1, hour=9, minute=0),  # Monday 9:00 AM
        #     'args': (),
        # },
        # 'every-5-minutes': {
        #     'task': 'products.tasks.nightly_inventory_update',
        #     'schedule': 300.0,  # Every 5 minutes (300 seconds)
        #     'args': (),
        # },
    }

    @app.task(bind=True, ignore_result=True)
    def debug_task(self):
        print(f'Request: {self.request!r}')
        
except ImportError:
    # Create placeholder app for Django to start without Celery
    class CeleryAppPlaceholder:
        def task(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        
        def __call__(self, *args, **kwargs):
            pass
            
    app = CeleryAppPlaceholder() 