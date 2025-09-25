import os
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Берём токен из переменной окружения
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("ERROR: TOKEN not set. Set environment variable TOKEN and restart.")
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Главное меню
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(KeyboardButton("Начать работу"))
main_kb.add(KeyboardButton("Мой отчёт за сегодня"))

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer(
        "Привет 👋\nЯ помогу фиксировать твое время по проектам.",
        reply_markup=main_kb
    )

@dp.message_handler(lambda msg: msg.text == "Начать работу")
async def start_work(message: types.Message):
    # Здесь позже добавим выбор проектов
    await message.answer("Тут позже будет список проектов ✅")

@dp.message_handler(lambda msg: msg.text == "Мой отчёт за сегодня")
async def today_report(message: types.Message):
    # Позже будем показывать часы по проектам
    await message.answer("Здесь будет отчёт по твоим часам 📊")

# Web-сервер для Render health-check
def run_web():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return "OK"

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # запускаем web-сервер в отдельном потоке
    t = threading.Thread(target=run_web)
    t.start()

    # запускаем polling для Telegram
    executor.start_polling(dp, skip_updates=True)
