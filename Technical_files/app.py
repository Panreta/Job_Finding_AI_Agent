from celery_demo.task1 import add
from celery_demo.task2 import mut

add.delay(2, 4)
mut.delay(3, 4)
print('end...')