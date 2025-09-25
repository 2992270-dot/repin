import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("ERROR: TOKEN not set")
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DATA_FILE = "sessions.json"
PROJECTS = ["Проект А", "Проект Б", "Внутренние задачи"]

# Главное меню
kb_builder = ReplyKeyboardBuilder()
kb_builder.add(KeyboardButton(text="Начать работу"))
kb_builder.add(KeyboardButton(text="Мой отчёт за сегодня"))
kb_builder.add(KeyboardButton(text="Завершить день"))
main_kb = kb_builder.as_markup(resize_keyboard=True)

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
            session["end_time"] = datetime.now().isoformat(timespec='seconds')
            start_dt = datetime.fromisoformat(session["start_time"])
            end_dt = datetime.now()
            total_seconds += int((end_dt - start_dt).total_seconds())
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return total_seconds

# Клавиатура проектов
def project_keyboard():
    kb = InlineKeyboardBuilder()
    for p in PROJECTS:
        kb.button(text=p, callback_data=f"proj:{p}")
    return kb.as_markup()

# Хендлеры
@dp.message(Command("start"))
async def start_cmd(msg: Message):
    await msg.answer("Привет 👋\nЯ помогу фиксировать твоё время по проектам.", reply_markup=main_kb)

@dp.message(F.text == "Начать работу")
async def start_work(msg: Message):
    await msg.answer("Выберите проект:", reply_markup=project_keyboard())

@dp.callback_query(lambda c: c.data.startswith("proj:"))
async def process_project(callback):
    project = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    start_time = datetime.now().isoformat(timespec='seconds')
    save_session(user_id, project, start_time)
    await callback.message.edit_text(f"✅ Сейчас работаешь над '{project}' с {start_time}")
    await callback.answer()

@dp.message(F.text == "Мой отчёт за сегодня")
async def today_report(msg: Message):
    if not os.path.exists(DATA_FILE):
        await msg.answer("Данных пока нет.")
        return
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_sessions = [s for s in data if s["user_id"] == msg.from_user.id]
    if not user_sessions:
        await msg.answer("Ты ещё не начинал работу сегодня.")
        return
    report = ""
    for s in user_sessions:
        report += f"{s['project']}: {s['start_time']} — {s.get('end_time','В процессе')}\n"
    await msg.answer(report)

@dp.message(F.text == "Завершить день")
async def finish_day(msg: Message):
    user_id = msg.from_user.id
    total_seconds = end_session(user_id)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    await msg.answer(f"✅ День завершён. Всего отработано: {hours} ч {minutes} мин.")

# Запуск бота
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
