import os
import json
import threading
from datetime import datetime
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("ERROR: TOKEN not set")
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Главное меню
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(KeyboardButton("Начать работу"))
main_kb.add(KeyboardButton("Мой отчёт за сегодня"))
main_kb.add(KeyboardButton("Завершить день"))

# Список проектов
PROJECTS = ["Проект А", "Проект Б", "Внутренние задачи"]

# Активные сессии {user_id: {project, start_time}}
active_sessions = {}

# Файл для хранения сессий
DATA_FILE = "sessions.json"

# Сохранение сессии
def save_session(user_id, project, start_time):
    data = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.append({
        "user_id": user_id,
        "project": project,
        "start_time": start_time,
        "end_time": None
    })
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Завершение сессии
def end_session(user_id):
    if not os.path.exists(DATA_FILE):
        return 0
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    total_seconds = 0
    for session in data:
        if session["user_id"] == user_id and session["end_time"] is None:
            session["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Подсчёт времени в секундах
            start_dt = datetime.fromisoformat(session["start_time"])
            end_dt = datetime.now()
            total_seconds += int((end_dt - start_dt).total_seconds())
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return total_seconds

# Клавиатура проектов
def project_keyboard():
    kb = InlineKeyboardMarkup()
    for p in PROJECTS:
        kb.add(InlineKeyboardButton(text=p, callback_data=f"proj:{p}"))
    return kb

# Команды бота
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer(
        "Привет 👋\nЯ помогу фиксировать твоё время по проектам.",
        reply_markup=main_kb
    )

@dp.message_handler(lambda msg: msg.text == "Начать работу")
async def start_work(message: types.Message):
    await message.answer("Выберите проект:", reply_markup=project_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith("proj:"))
async def process_project(callback: types.CallbackQuery):
    project = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    start_time = datetime.now().isoformat(timespec='seconds')
    active_sessions[user_id] = {"project": project, "start_time": start_time}
    save_session(user_id, project, start_time)
    await callback.answer(f"Начал работу над '{project}'")
    await callback.message.edit_text(f"✅ Сейчас работаешь над '{project}' с {start_time}")

@dp.message_handler(lambda msg: msg.text == "Мой отчёт за сегодня")
async def today_report(message: types.Message):
    if not os.path.exists(DATA_FILE):
        await message.answer("Данных пока нет.")
        return
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_sessions = [s for s in data if s["user_id"] == message.from_user.id]
    if not user_sessions:
        await message.answer("Ты ещё не начинал работу сегодня.")
        return
    report = ""
    for s in user_sessions:
        report += f"{s['project']}: {s['start_time']} — {s.get('end_time','В процессе')}\n"
    await message.answer(report)

@dp.message_handler(lambda msg: msg.text == "Завершить день")
async def finish_day(message: types.Message):
    user_id = message.from_user.id
    total_seconds = end_session(user_id)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    await message.answer(f"✅ День завершён. Всего отработано: {hours} ч {minutes} мин.")

# Web-сервер для Render health-check
def run_web():
    app = Flask(__name__)
    @app.route("/")
    def index():
        return "OK"
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    executor.start_polling(dp, skip_updates=True)
