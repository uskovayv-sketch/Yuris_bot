import asyncio
from mistralai import Mistral
import os
import PyPDF2
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import tempfile

# ========== НАСТРОЙКИ ==========
TOKEN = '8747950882:AAFg3A-gAc3PwdORU5Mo_SPV8BLs2rjpoR0'
MISTRAL_KEY = "7Ynm0FvFKUE7DzPPPbds2tm59jWkcuwV"  
# ================================

# Инициализация клиента Mistral
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
        print(f"🔄 Отправляю запрос в Mistral...")
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": "Ты — Юрис, юридический помощник. Твоя задача - весело и легко объяснять сложные юридические тексты и формулировки, делая их понятнее для молодых ребят и подростков"},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content
        print(f"✅ Получен ответ от Mistral")
        return answer
    except Exception as e:
        print(f"❌ Ошибка Mistral: {e}")
        return f"🤖 Извини, временные проблемы с ИИ. Ошибка: {str(e)}"

# --- Чтение PDF ---
def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
        return text[:3000]  # Ограничиваем длину

# ========== ХЕНДЛЕРЫ ==========
@dp.message(Command('start'))
async def start_command(message: Message):
    await message.answer(
        "👋 **Привет! Я Юрис — твой помощник в понимании юридических бумаг!**\n\n"
        "📄 **Что я умею:**\n"
        "• Анализировать юридические документы (PDF)\n"
        "• Объяснять сложные термины простым языком\n"
        "• Отвечать на вопросы про законы\n\n"
        "👇 **Просто отправь мне файл или напиши вопрос!**",
        reply_markup=get_main_keyboard()
    )
    print(f"🚀 Пользователь @{message.from_user.username} запустил бота")

@dp.message(lambda message: message.text == "📄 Загрузить документ")
async def upload_document_prompt(message: Message):
    await message.answer("📎 Отправь мне PDF-файл с юридическим документом, и я проанализирую его!")

@dp.message(lambda message: message.text == "❓ Помощь")
async def help_command(message: Message):
    await message.answer(
        "📚 **Как пользоваться:**\n\n"
        "1️⃣ **Отправь PDF** — я прочитаю документ\n"
        "2️⃣ **Подожди немного** — я анализирую текст\n"
        "3️⃣ **Получишь объяснение** — простыми словами!\n\n"
        "Или просто задай вопрос про любой закон!",
        reply_markup=get_main_keyboard()
    )

@dp.message(lambda message: message.text == "ℹ️ О боте")
async def about_command(message: Message):
    await message.answer(
        "🤖 **О боте Юрис**\n\n"
        "• **Модель:** Mistral AI\n"
        "• **Версия:** 1.0\n"
        "• **Фичи:** Анализ PDF, объяснение терминов\n\n"
        "🚀 **Проект для Фестиваля ИИ**",
        reply_markup=get_main_keyboard()
    )

# --- Обработчик документов ---
@dp.message(lambda message: message.document is not None)
async def handle_document(message: Message):
    if not message.document.file_name.endswith('.pdf'):
        await message.answer("⚠️ Пока я понимаю только PDF-файлы. Отправь PDF!")
        return

    msg = await message.answer("📥 Получаю документ...")
    print(f"📎 Получен файл от @{message.from_user.username}: {message.document.file_name}")
    
    # Скачиваем файл во временную папку
    file_info = await message.bot.get_file(message.document.file_id)
    file_path = file_info.file_path
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        await message.bot.download_file(file_path, tmp_file.name)
        tmp_path = tmp_file.name
    
    await msg.edit_text("📖 Читаю документ...")
    
    # Извлекаем текст
    document_text = extract_text_from_pdf(tmp_path)
    os.unlink(tmp_path)  # Удаляем временный файл
    
    if not document_text.strip():
        await msg.edit_text("❌ Не удалось прочитать текст из PDF. Возможно, это сканированный документ или он защищён.")
        return
    
    # Показываем кусочек текста (для отладки)
    print(f"📄 Текст документа (первые 200 символов): {document_text[:200]}...")
    
    await msg.edit_text("🤔 Анализирую документ с помощью ИИ... (это может занять до минуты)")
    
    # Отправляем в Mistral
    ai_response = await ask_mistral(
        f"Проанализируй этот юридический документ и объясни его простыми словами. "
        f"Выдели самую суть, что это за документ, какие обязательства накладывает, "
        f"есть ли риски. Вот текст:\n\n{document_text}"
    )
    
    await message.answer(
        f"📄 **Анализ документа:**\n\n{ai_response}\n\n"
        f"---\n"
        f"⚠️ *Ответ подготовлен ИИ. Для принятия важных решений проконсультируйтесь с юристом.*"
    )
    print(f"✅ Ответ отправлен @{message.from_user.username}")

# --- Обработчик обычного текста ---
@dp.message()
async def text_handler(message: Message):
    if message.text and not message.text.startswith('/'):
        user_text = message.text
        print(f"📨 Вопрос от @{message.from_user.username}: {user_text[:50]}...")
        
        await message.answer("🤔 Думаю над ответом...")
        
        # Отправляем в Mistral
        ai_response = await ask_mistral(
            f"Ответь на вопрос по юридической теме простым понятным языком. "
            f"Вопрос: {user_text}"
        )
        
        await message.answer(ai_response)
        print(f"✅ Ответ отправлен @{message.from_user.username}")

# ========== ЗАПУСК ==========
async def main():
    print("\n" + "="*60)
    print("🚀 ЮРИС-БОТ С MISTRAL AI ЗАПУСКАЕТСЯ!")
    print("="*60)
    print(f"🤖 Ключ Mistral: {MISTRAL_KEY[:5]}...{MISTRAL_KEY[-5:]}")
    print("📊 Лог событий:")
    print("-"*40)
    
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
