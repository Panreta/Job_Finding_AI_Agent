import time
from celery_demo import app

@app.task
def mut(x, y):
    time.sleep(5)
    return x * y