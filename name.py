import asyncio
import re
import sqlite3
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# 1. НАЛАШТУВАННЯ ТОКЕНА
TELEGRAM_TOKEN ="9029056687:AAGMe0b8jA362sBqud5n9hwBT18V0oPV4bM"
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

DB_NAME = "osint_base.db"

# 2. СТВОРЕННЯ ТА НАЛАШТУВАННЯ БАЗИ ДАНИХ
def init_db():
    """Створює таблицю, де всі дані (Телефон, ПІБ, Адреса, Авто) зв'язані між собою"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS citizens (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            phone TEXT,
            fullname TEXT,
            address TEXT,
            car_number TEXT
        )
    ''')
    conn.commit()
    conn.close()

def search_db(query):
    """Шукає в базі збіги за будь-яким полем (телефоном, номером авто чи ПІБ)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Очищаємо запит для точного пошуку
    clean_query = query.replace(" ", "").replace("-", "").upper()
    
    # Шукаємо збіг у будь-якій колонці
    cursor.execute('''
        SELECT phone, fullname, address, car_number FROM citizens 
        WHERE UPPER(REPLACE(REPLACE(phone, ' ', ''), '-', '')) = ?
        OR UPPER(REPLACE(REPLACE(car_number, ' ', ''), '-', '')) = ?
        OR UPPER(fullname) LIKE ?
    ''', (clean_query, clean_query, f"%{query.upper()}%"))
    
    results = cursor.fetchall()
    conn.close()
    return results

# 3. ОБРОБКА КОМАНД ТА ПОВІДОМЛЕНЬ
@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    start_text = (
        "🔍 **Універсальний OSINT-Бот активований.**\n\n"
        "Я шукаю повну інформацію про особу в межах України.\n"
        "Надішліть мені щось одне з переліченого:\n"
        "• **Номер телефону** (наприклад: `0971234567`)\n"
        "• **Держномер авто** (наприклад: `AA1111BB`)\n"
        "• **ПІБ особи** (наприклад: `Іванов Іван`)\n\n"
        "Бот автоматично знайде зв'язане місце проживання, автівки та контакти."
    )
    await message.answer(start_text, parse_mode="Markdown")

@dp.message()
async def global_search_handler(message: types.Message):
    user_input = message.text.strip()
    
    status_msg = await message.answer("🔄 *Аналізую запит та сканую зв'язані бази даних...*", parse_mode="Markdown")
    await asyncio.sleep(1.2) # Імітація роботи алгоритму

    # Запит до нашої локальної бази даних
    db_results = search_db(user_input)

    if db_results:
        response_text = "📋 **ЗНАЙДЕНО ЗБІГИ ЗА ВАШИМ ЗАПИТОМ:**\n\n"
        for idx, row in enumerate(db_results, 1):
            phone, fullname, address, car_number = row
            response_text += (
                f"👤 **Картка особи №{idx}:**\n"
                f"├ **ПІБ:** {fullname or 'Не вказано'}\n"
                f"├ **Телефон:** `{phone or 'Не вказано'}`\n"
                f"├ **Місце проживання:** {address or 'Не вказано'}\n"
                f"└ **Автомобіль:** `{car_number or 'Не знайдено'}`\n"
                f"──────────────────\n"
            )
        await status_msg.edit_text(response_text, parse_mode="Markdown")
    else:
        # Якщо в базі порожньо, бот генерує технічний «цифровий слід» на основі формату
        clean_input = user_input.replace(" ", "").upper()
        
        if re.match(r'^[A-ZА-Я]{2}\d{4}[A-ZА-Я]{2}$', clean_input):
            # Якщо ввели номер машини
            await status_msg.edit_text(
                f"🚘 **Результат пошуку авто:** `{user_input.upper()}`\n\n"
                f"❌ Прямих зв'язків із власником та адресою в безкоштовній локальній базі не виявлено.\n"
                f"💡 _Для наповнення бази скористайтеся імпортом файлів .txt або .csv._", 
                parse_mode="Markdown"
            )
        elif re.match(r'^\+?\d{10,13}$', clean_input):
            # Якщо ввели номер телефону
            await status_msg.edit_text(
                f"📱 **Результат пошуку телефону:** `{user_input}`\n\n"
                f"❌ Пов'язаного імені, адреси проживання чи транспортних засобів не знайдено.", 
                parse_mode="Markdown"
            )
        else:
            await status_msg.edit_text(
                "❌ **Збігів не знайдено.**\nПеревірте правильність введення даних (Телефон, Номер авто або ПІБ).",
                parse_mode="Markdown"
            )

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
