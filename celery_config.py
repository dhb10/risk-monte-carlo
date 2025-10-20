import os
from celery import Celery
from dotenv import load_dotenv


load_dotenv()

redis_url = os.getenv("REDISCLOUD_URL")
if not redis_url:
    raise ValueError("Redis URL is not set in the environment variables")


# For SSL on Azure, you could uncomment and use this:
redis_url_with_ssl = redis_url + "?ssl_cert_reqs=CERT_REQUIRED"

# For local/testing
# redis_url_with_ssl = redis_url

celery_app = Celery('app')

celery_app.conf.broker_url = redis_url_with_ssl
celery_app.conf.result_backend = redis_url_with_ssl

#update other config values
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    worker_concurrency=8,
    broker_connection_retry_on_startup=True,
    worker_log_format='%(asctime)s [%(levelname)s]: %(message)s',
    worker_task_log_format='%(asctime)s [%(levelname)s]: %(message)s',
    loglevel='DEBUG',
    broker_transport_options={
        'socket_timeout': 30,
        'retry_on_timeout': True
    }
)


import tasks  #explicitly importing your task module
