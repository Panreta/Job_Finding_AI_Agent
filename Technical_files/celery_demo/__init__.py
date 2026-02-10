from celery import Celery

app = Celery(
    'demo',
    include=[
        'celery_demo.task1',
        'celery_demo.task2',
    ]
)
app.config_from_object('celery_demo.celeryconfig')