from aiogram import Bot
import asyncio

API_TOKEN = "7869423396:AAG7N4TBsdq-4LvA7fY4_2lvnRW9oPljDb0"

bot = Bot(token=API_TOKEN)

async def send_welcome_message(chat_id, username):
    message = f"Привет, {username}! Добро пожаловать в наше приложение."
    await bot.send_message(chat_id, message)
    print(f" Приветственное сообщение отправлено пользователю {username}")
