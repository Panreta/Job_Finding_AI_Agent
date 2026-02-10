import time
from celery import Celery

if __name__ == '__main__':
    #消息中间件（使用的redis）
    broker = 'redis://localhost:6379/1'
    #结果存储（使用的redis）
    backend = 'redis://localhost:6379/2'
    #实例化Celery对象
    app = Celery(
        'celeryDemo',
        broker=broker,
        backend=backend
    )

    # 添加@app.task()装饰器，说明执行的任务是一个异步任务
    @app.task()
    def add(x,y):
        print('task enter ....')
        time.sleep(5)
        return x+y