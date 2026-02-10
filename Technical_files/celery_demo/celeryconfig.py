# 官方配置文档：查询每个配置项的含义。
# http://docs.celeryproject.org/en/latest/userguide/configuration.html

#broker(消息中间件来接收和发送任务消息)
broker_url  = 'redis://localhost:6379/1'
#backend(存储worker执行的结果)
result_backend  = 'redis://localhost:6379/2'

#设置时间参照，不设置默认使用的UTC时间
timezone  = 'America/Los_Angeles'
#指定任务的序列化
task_serializer ='json'
#指定执行结果的序列化
result_serializer ='json'