from celery import Celery
from telegram_bot import send_welcome_message  
import asyncio

# Инициализация Celery
celery_app = Celery(
    'tasks',
    broker='pyamqp://guest@localhost//',  
    backend='rpc://'  
)

def run_async(func, *args, **kwargs):
    loop = asyncio.new_event_loop()  
    asyncio.set_event_loop(loop)  
    return loop.run_until_complete(func(*args, **kwargs))  

@celery_app.task
def send_welcome_message_task(chat_id, username):
    run_async(send_welcome_message, chat_id, username)
