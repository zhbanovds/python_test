from celery import Celery
from telegram_bot import send_welcome_message 
import asyncio

# Инициализация Celery
celery_app = Celery(
    'tasks',
    broker='pyamqp://guest@localhost//',
    backend='rpc://'
)

# Асинхронная обертка для вызова асинхронной функции
def run_async(func, *args, **kwargs):
    loop = asyncio.new_event_loop()  
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(func(*args, **kwargs))

# Celery задача для отправки приветственного сообщения
@celery_app.task
def send_welcome_message_task(username, chat_id):
    run_async(send_welcome_message, chat_id, username)  # Асинхронная задача через синхронную обертку
