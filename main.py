import asyncio
import sqlite3
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, ADMIN_ID, CRYPTO_PAY_TOKEN, PAY_AMOUNT_USD, DB_PATH

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
admin_states = {}  # Для отслеживания состояния администратора

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, invited_by INTEGER, sub_active INTEGER)")
    conn.commit()
    conn.close()

def add_user(user_id, invited_by=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id, invited_by, sub_active) VALUES (?, ?, ?)", (user_id, invited_by, 0))
    conn.commit()
    conn.close()

def is_subscribed(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT sub_active FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    return row and row[0] == 1

async def create_invoice():
    url = "https://pay.crypt.bot/api/createInvoice"
    payload = {
        "asset": "USDT",
        "amount": str(PAY_AMOUNT_USD),
        "description": "GhostShell Lifetime Subscription",
        "hidden_message": "Спасибо за оплату!",
        "paid_btn_name": "openChannel",
        "paid_btn_url": "https://t.me/GhostShellBot"
    }
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json()
            return data["result"]["pay_url"]

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    add_user(message.from_user.id, ref_id)
    await send_main_menu(message)

async def send_main_menu(msg):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠️ Сносер", callback_data="snoser")],
        [InlineKeyboardButton(text="🕵️‍♂️ Пробив", callback_data="probiv")],
        [InlineKeyboardButton(text="ℹ️ Инфо", callback_data="info")]
    ])
    await msg.answer(
        "👻 <b>GhostShell</b> — сильнейшая OSINT утилита.\n\nВыберите действие:",
        reply_markup=kb
    )

async def edit_main_menu(call):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠️ Сносер", callback_data="snoser")],
        [InlineKeyboardButton(text="🕵️‍♂️ Пробив", callback_data="probiv")],
        [InlineKeyboardButton(text="ℹ️ Инфо", callback_data="info")]
    ])
    await call.message.edit_text(
        "👻 <b>GhostShell</b> — сильнейшая OSINT утилита.\n\nВыберите действие:",
        reply_markup=kb
    )

@dp.callback_query(F.data == "main_menu")
async def back_to_main(call: types.CallbackQuery):
    await edit_main_menu(call)

@dp.callback_query(F.data == "info")
async def info_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    sub = "Активна" if is_subscribed(user_id) else "Отсутствует"
    profile = (
        f"💎 Ваш профиль\n\n"
        f"🆔 ID: {user_id}\n"
        f"💳 Баланс: 0.0$\n"
        f"💸 Реферальный Баланс: 0.0$\n"
        f"💜 Приглашен: 484312705\n"
        f"💎 Подписка: {sub}\n\n"
        f"⏰ До: {'Бессрочная' if sub == 'Активна' else 'Подписка отсутствует'}\n"
        f"👨‍💻 Поддержка / Оплата по карте: @xmroman \n"
        f"{'✅ Ваша подписка активна' if sub == 'Активна' else '❌ Ваша подписка - отсутствует'}"
    )

    buttons = [
        [InlineKeyboardButton(text="💎 Купить подписку", callback_data="buy")],
        [InlineKeyboardButton(text="👥 Рефералы", callback_data="ref")]
    ]

    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="👑 Панель администратора", callback_data="admin_panel")])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text(profile, reply_markup=kb)

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выдать подписку", callback_data="admin_give")],
        [InlineKeyboardButton(text="❌ Отобрать подписку", callback_data="admin_revoke")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="info")]
    ])
    await call.message.edit_text("👑 Панель администратора:\nВыберите действие:", reply_markup=kb)

@dp.callback_query(F.data == "admin_give")
async def admin_give(call: types.CallbackQuery):
    await call.message.edit_text("🛠 Функция выдачи подписки будет реализована позже.", reply_markup=get_back_to_admin())

@dp.callback_query(F.data == "admin_revoke")
async def admin_revoke(call: types.CallbackQuery):
    await call.message.edit_text("🛠 Функция отзыва подписки будет реализована позже.", reply_markup=get_back_to_admin())

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(call: types.CallbackQuery):
    await call.message.edit_text("📊 Всего пользователей: [будет позже]", reply_markup=get_back_to_admin())

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(call: types.CallbackQuery):
    admin_states[call.from_user.id] = "awaiting_broadcast"
    await call.message.edit_text("📝 Введите текст рассылки. Сообщение будет отправлено всем пользователям.", reply_markup=get_back_to_admin())

@dp.message()
async def handle_text_messages(message: types.Message):
    user_id = message.from_user.id
    if admin_states.get(user_id) == "awaiting_broadcast" and user_id == ADMIN_ID:
        admin_states.pop(user_id)
        await message.answer("📤 Рассылка началась...")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM users")
        users = c.fetchall()
        conn.close()

        success = 0
        for u in users:
            try:
                await bot.send_message(u[0], message.text)
                success += 1
            except Exception:
                continue

        await message.answer(f"✅ Рассылка завершена. Отправлено: {success} пользователей.")

def get_back_to_admin():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])

@dp.callback_query(F.data == "buy")
async def buy_handler(call: types.CallbackQuery):
    await call.message.edit_text("⏳ Создаю счёт на оплату в USDT...")
    url = await create_invoice()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить подписку", url=url)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="info")]
    ])
    await call.message.edit_text("🔐 Пожизненная подписка: <b>20$</b>\nНажмите кнопку ниже для оплаты:", reply_markup=kb)

@dp.callback_query(F.data == "snoser")
async def snoser_handler(call: types.CallbackQuery):
    if not is_subscribed(call.from_user.id):
        await call.message.edit_text("⛔ Доступ запрещён. Приобретите подписку.", reply_markup=get_back_main())
    else:
        await call.message.edit_text("🔧 Выберите:\n- Снос каналов\n- Снос аккаунтов", reply_markup=get_back_main())

@dp.callback_query(F.data == "probiv")
async def probiv_handler(call: types.CallbackQuery):
    if not is_subscribed(call.from_user.id):
        await call.message.edit_text("⛔ Доступ запрещён. Приобретите подписку.", reply_markup=get_back_main())
    else:
        await call.message.edit_text(
            "🔍 Пробив:\n- Телефон\n- Telegram\n- VK\n- Email\n- IP\n- ИНН / СНИЛС",
            reply_markup=get_back_main()
        )

@dp.callback_query(F.data == "ref")
async def ref_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    await call.message.edit_text(
        f"👥 Ваша реферальная ссылка:\nhttps://t.me/GhostShellBot?start={user_id}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="info")]
        ])
    )

def get_back_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
