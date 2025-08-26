import random
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from datetime import datetime

API_TOKEN = '' # додайте свій ключ

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

user_state = {}

# Мапа ID -> Ім’я
USER_NAMES = {
    # додайте знайомих людей
}

def log_message(message: str, level: str = "LOG", user_id: int = None):
    time_str = datetime.now().strftime("%H:%M")

    # Кольори ANSI
    colors = {
        "LOG": "\033[94m",       # синій
        "ПОМИЛКА": "\033[91m",   # червоний
        "MAIN": "\033[1;36m",    # світло синій
        "ІМЯ": "\033[95m",      # фіолетовий
        "ЧАС": "\033[92m",       # зелений
        "END": "\033[0m"         # скидання стилю
    }

    # Отримати ім'я або ID
    name = USER_NAMES.get(user_id, str(user_id)) if user_id is not None else "?"

    # Формування логів
    header = f"{colors.get(level, '')}[{level}]{colors['ЧАС']}[{time_str}]{colors['END']}"
    name_str = f"{colors['ІМЯ']}[{name}]{colors['END']}"
    
    print(f"{header}{name_str} Користувач {message}")

# Стартова клавіатура
start_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Обрати тему")]],
    resize_keyboard=True
)

# Для прикладу
topic_display_map = {
    "Exam/ex1" : "1. Фізіологія збудливих тканин",
    "Exam/ex2" : "2. Нервова регуляція рухових і т.д :)",
    "Exam/ex3" : "3. Фізіологія АНС",
    "Exam/ex4" : "4. Фізіологія сенсорних систем",
    "Exam/ex5" : "5. Фізіологія ендокринної системи",
    "Exam/ex6" : "6. Енергетичний обмін. і т.д.",
    "Exam/ex7" : "7. Фізіологія системи крові",
    "Exam/ex8" : "8. Фізіологія дихання",
    "Exam/ex9_h1" : "9. (Перша частина)",
    "Exam/ex9_h2" : "9. (Друга частина)",
    "Exam/ex9" : "9. Фізіологія серцево-судинної системи",
    "Exam/ex10" : "10. Фізіологія системи травлення",
    "Exam/ex11" : "11. Фізіологія виділення",
    "Exam/exAll" : "Всі теми разом"
}

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer("Привіт! Обери тему для навчання:", reply_markup=start_kb)

@dp.message(F.text == "Обрати тему")
async def handle_choose_topic(message: types.Message):
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"topic_{key}")]
            for key, name in topic_display_map.items()
        ]
    )
    await message.answer("Оберіть одну з тем:", reply_markup=inline_kb)

@dp.callback_query(F.data.startswith("topic_"))
async def handle_topic_selected(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    topic_key = callback.data.split("_", 1)[1]
    topic_name = topic_display_map.get(topic_key, topic_key)
    log_message(f"обрав тему: {topic_key}", "LOG", user_id)

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Розпочати тестування", callback_data=f"start_test_{topic_key}")],
            [InlineKeyboardButton(text="Повернутися назад", callback_data="back_to_topics")]
        ]
    )
    await callback.message.edit_text(f"Обрана тема: {topic_name}", reply_markup=markup)

@dp.callback_query(F.data == "back_to_topics")
async def handle_back(callback: types.CallbackQuery):
    await handle_choose_topic(callback.message)

@dp.callback_query(F.data.startswith("start_test_"))
async def handle_start_test(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    topic_key = callback.data.split("_", 2)[2]
    topic_name = topic_display_map.get(topic_key, topic_key)
    log_message(f"почав тестування з теми: {topic_key}", "LOG", user_id)

    user_state[user_id] = {"topic": topic_key} 

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="По порядку", callback_data="mode_order")],
        [InlineKeyboardButton(text="Рандомно", callback_data="mode_random")],
        [InlineKeyboardButton(text="Повернутися назад", callback_data="back_to_topics")]
    ])

    await callback.message.edit_text(
        f"Починаємо тестування з теми: {topic_name}\n\nЯкий порядок тестів вас цікавить?",
        reply_markup=markup
    )

@dp.callback_query(F.data.in_(["mode_order", "mode_random"]))
async def start_test_session(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    topic = user_state[user_id]["topic"]
    db_name = f"DataBases/{topic}.db" # HERE ADDED A NEW WAY 'DATABASES/'
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    conn.close()

    if callback.data == "mode_random":
        random.shuffle(questions)

    user_state[user_id]["questions"] = questions
    user_state[user_id]["current_index"] = 0
    user_state[user_id]["score"] = 0  # <--- кількість правильних відповідей
    user_state[user_id]["total"] = len(questions)  # <--- загальна кількість питань
    await send_question(callback.message, user_id)

def shuffle_answers(row):
    answers = [row[2], row[3], row[4], row[5], row[6]]
    correct_index = row[7] - 1  # правильна відповідь до перемішування
    indexed_answers = list(enumerate(answers, 1))
    random.shuffle(indexed_answers)

    # знайти новий номер правильної відповіді після перемішування
    for num, text in indexed_answers:
        if text == answers[correct_index]:
            new_correct = num
            break

    return indexed_answers, new_correct

async def send_question(message, user_id):
    data = user_state[user_id]
    index = data["current_index"]
    questions = data["questions"]
    
    if index >= len(questions):
        log_message(f"пройшов тему з результатом {user_state[user_id].get('score', 0)} / {user_state[user_id].get('total', 0)}", "LOG", user_id)
        score = user_state[user_id].get("score", 0)
        total = user_state[user_id].get("total", 0)
        await message.answer(f"Тестування завершено ✅\n\nВаш результат: *{score} / {total}*", parse_mode="Markdown")
        return

    row = questions[index]
    
    # 🆕 Отримуємо перемішані відповіді та правильну відповідь після тасування
    shuffled, new_correct = shuffle_answers(row)
    data["shuffled"] = shuffled
    data["correct"] = new_correct

    # Кнопки для відповідей
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ans[1], callback_data=f"answer_{ans[0]}")]
        for ans in shuffled
    ])

    text = row[1].replace("\\n", "\n")
    question_text = f"*({index + 1}/{len(questions)})* {text}"
    await message.answer(question_text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("answer_"))
async def handle_answer(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    try:
        data = user_state[user_id]
    except KeyError:
        # Лог у консоль
        log_message("намагався відповісти, але дані відсутні (бот перезапущено)", "ПОМИЛКА", user_id)
        
        # Повідомлення користувачу
        await callback.message.answer("Сесія тестування недоступна 😕\nБудь ласка, оберіть тему заново:")
        await handle_choose_topic(callback.message)
        return  # зупиняємо виконання

    chosen = int(callback.data.split("_")[1])
    correct = data["correct"]

    correct_text = next(text for num, text in data["shuffled"] if num == correct)

    if chosen == correct:
        user_state[user_id]["score"] += 1  # <--- додай до рахунку
        await callback.message.answer(
            f"Ви відповіли правильно ✅. Відповідь:\n*{correct_text}*",
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(
            f"Відповідь не правильна ❌. Правильна відповідь:\n*{correct_text}*",
            parse_mode="Markdown"
        )

    data["current_index"] += 1
    await send_question(callback.message, user_id)
    await callback.message.edit_reply_markup(reply_markup=None)

async def main():
    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        print("Бот зупинено вручну.")

if __name__ == "__main__":
    try:
        log_message(f"Бот було успішно запущено", "MAIN")
        asyncio.run(main())
    except KeyboardInterrupt:
        log_message(f"Бот було успішно вимкнено", "MAIN") #174