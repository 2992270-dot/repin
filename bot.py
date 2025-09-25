import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("ERROR: TOKEN not set")
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.reply("Привет! Я простой бот 😊")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
