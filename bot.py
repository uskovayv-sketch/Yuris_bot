import asyncio
from mistralai import Mistral
import os
import PyPDF2
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import tempfile

# ========== НАСТРОЙКИ ==========
TOKEN = os.environ.get('BOT_TOKEN')
MISTRAL_KEY = os.environ.get('MISTRAL_KEY')
# ================================

if not TOKEN or not MISTRAL_KEY:
    print("❌ Ошибка: Не найдены переменные окружения!")
    exit(1)

# Инициализация
client = Mistral(api_key=MISTRAL_KEY)
dp = Dispatcher()

# --- Клавиатура ---
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📄 Загрузить документ"), KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="ℹ️ О боте")]
        ],
        resize_keyboard=True
    )
    return keyboard

# --- Функция для Mistral ---
async def ask_mistral(prompt):
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": "Ты — Юрис, юридический помощник. Объясняй сложные тексты простыми словами."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка Mistral: {e}")
        return f"🤖 Ошибка ИИ: {e}"

# --- Чтение PDF ---
def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
        return text[:3000]

# ========== ХЕНДЛЕРЫ ==========
@dp.message(Command('start'))
async def start_command(message: Message):
    await message.answer(
        "👋 **Привет! Я Юрис — юридический помощник!**\n\n"
        "📄 Отправь мне PDF с договором, и я объясню его простыми словами!",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command('help'))
async def help_command(message: Message):
    await message.answer(
        "📚 **Как пользоваться:**\n\n"
        "1. Отправь PDF-файл\n"
        "2. Я прочитаю текст\n"
        "3. Получишь простое объяснение!",
        reply_markup=get_main_keyboard()
    )

@dp.message(lambda message: message.document is not None)
async def handle_document(message: Message):
    if not message.document.file_name.endswith('.pdf'):
        await message.answer("⚠️ Пока я понимаю только PDF-файлы!")
        return
    
    msg = await message.answer("📥 Скачиваю файл...")
    
    # Скачиваем во временную папку
    file_info = await message.bot.get_file(message.document.file_id)
    file_path = file_info.file_path
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        await message.bot.download_file(file_path, tmp_file.name)
        tmp_path = tmp_file.name
    
    await msg.edit_text("📖 Читаю документ...")
    text = extract_text_from_pdf(tmp_path)
    os.unlink(tmp_path)  # Удаляем временный файл
    
    if not text.strip():
        await msg.edit_text("❌ Не удалось прочитать текст. Возможно, файл защищён или это сканированный документ.")
        return
    
    await msg.edit_text("🤔 Анализирую через Mistral AI... (это может занять до минуты)")
    answer = await ask_mistral(f"Объясни простыми словами этот юридический текст. Выдели самую суть:\n\n{text}")
    
    await message.answer(
        f"🧠 **Простое объяснение:**\n\n{answer}\n\n---\n"
        f"⚠️ *Ответ подготовлен ИИ, для важных решений проконсультируйтесь с юристом*"
    )

@dp.message()
async def text_handler(message: Message):
    if message.text and not message.text.startswith('/'):
        await message.answer("🤔 Думаю...")
        answer = await ask_mistral(message.text)
        await message.answer(answer)

# ========== ЗАПУСК ==========
async def main():
    print("🚀 Юрис-бот запускается на Render...")
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())