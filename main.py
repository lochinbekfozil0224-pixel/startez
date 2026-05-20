# ==========================================================
#   TEZKOR STAR BOT — bitta fayl, hech qanday sozlama kerakmas
#   Faqat yuklab, Deploy bos. Tamom.
# ==========================================================

import asyncio
import logging
import os
import sqlite3
from contextlib import suppress
from datetime import datetime

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, CopyTextButton

# ==========================================================
#   ⚙️ SOZLAMALAR — KODNING ICHIDA, HECH NARSA QO'SHISH KERAKMAS
# ==========================================================
BOT_TOKEN = "8712600970:AAFFXIwrY1Rg_sVj4GrxXkMaqgEFSh0-J38"
ADMIN_ID = 8135915671
DB_PATH = "bot.db"  # Oddiy fayl, hech qanday volume kerakmas

# ==========================================================
#   DEFAULT MA'LUMOTLAR
# ==========================================================
DEFAULT_SETTINGS = {
    "welcome_text": "👋 Salom, <b>{name}</b>!\n\n⭐ Star va 💎 Premium sotib olish uchun pastdagi tugmalardan foydalaning.",
    "stars_menu_text": "⭐ <b>Star sotib olish</b>\n\nKerakli paketni tanlang:",
    "premium_menu_text": "💎 <b>Telegram Premium</b>\n\nMuddatni tanlang:",
    "help_text": "❓ <b>Yordam</b>\n\n👨‍💼 Admin: @{admin}\n⏰ 24/7 ishlaymiz",
    "about_text": "ℹ️ <b>Bot haqida</b>\n\n⭐ Telegram Star\n💎 Telegram Premium\n\n✅ Tez yetkazib beramiz\n✅ Ishonchli",
    "ask_username_text": "👤 <b>Kimga yuboramiz?</b>\n\nTelegram username yuboring (masalan: <code>@username</code>)\n\nYoki o'zingizga olsangiz, <b>🔗 O'zimga</b> tugmasini bosing.",
    "payment_text": "💳 <b>TO'LOV MA'LUMOTLARI</b>\n\n💳 Karta: <code>{card}</code>\n🏦 Bank: {bank}\n👤 Egasi: {holder}\n\n💰 <b>Miqdor: {amount} so'm</b>\n\n⚠️ Tolov qilgandan keyin <b>chek rasmini</b> shu yerga yuboring.",
    "waiting_admin_text": "✅ <b>To'lov qabul qilindi!</b>\n\n⏱ <b>5 daqiqa</b> ichida hisobingizga tushadi.",
    "order_completed_text": "🎉 <b>Tabriklaymiz!</b>\n\n✅ Buyurtmangiz bajarildi.",
    "order_rejected_text": "❌ <b>Buyurtma rad etildi.</b>\n\nIltimos, admin bilan bog'laning: @{admin}",
    "sub_required_text": "⚠️ <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>",
    "btn_stars": "⭐ Star sotib olish",
    "btn_premium": "💎 Premium sotib olish",
    "btn_help": "❓ Yordam",
    "btn_about": "ℹ️ Bot haqida",
    "btn_back": "◀️ Orqaga",
    "btn_cancel": "❌ Bekor qilish",
    "btn_main": "🏠 Asosiy menyu",
    "btn_contact_admin": "👨‍💼 Admin bilan bog'lanish",
    "btn_check_sub": "✅ Tekshirish",
    "btn_myself": "🔗 O'zimga",
    "payment_card": "9860230102795708",
    "payment_bank": "Universalbank Humo",
    "payment_holder": "ADMIN",
    "admin_username": "tezkor_admin",
    "star_rate_uzs": "210",
    "payment_provider": "",
    "click_merchant_id": "",
    "click_service_id": "",
    "click_secret_key": "",
    "mirpay_merchant_id": "",
    "mirpay_api_key": "",
    "mirpay_secret": "",
    "proof_channel": "",
}

DEFAULT_STARS = [50, 100, 250, 500, 1000, 2500]
DEFAULT_PREMIUM = [(3, 175000), (6, 235000), (12, 425000)]

EDITABLE_TEXTS = {
    "welcome_text": "👋 Salomlashuv",
    "stars_menu_text": "⭐ Star menyu",
    "premium_menu_text": "💎 Premium menyu",
    "help_text": "❓ Yordam",
    "about_text": "ℹ️ Bot haqida",
    "ask_username_text": "👤 Username so'rash",
    "payment_text": "💳 To'lov",
    "waiting_admin_text": "⏳ Kutish",
    "order_completed_text": "🎉 Bajarildi",
    "order_rejected_text": "❌ Rad etildi",
    "sub_required_text": "⚠️ Obuna talab",
}

BTN_KEYS = {
    "btn_stars": "⭐ Star",
    "btn_premium": "💎 Premium",
    "btn_help": "❓ Yordam",
    "btn_about": "ℹ️ Bot haqida",
    "btn_back": "◀️ Orqaga",
    "btn_cancel": "❌ Bekor",
    "btn_main": "🏠 Menyu",
    "btn_contact_admin": "👨‍💼 Admin",
    "btn_check_sub": "✅ Tekshirish",
    "btn_myself": "🔗 O'zimga",
}


# ==========================================================
#   DATABASE (SQLite — oddiy fayl)
# ==========================================================
def db_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = db_conn()
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        balance INTEGER DEFAULT 0,
        stars_bought INTEGER DEFAULT 0,
        total_spent INTEGER DEFAULT 0,
        referred_by INTEGER,
        referral_count INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS star_packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stars INTEGER UNIQUE
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS premium_packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        months INTEGER UNIQUE,
        price INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        order_type TEXT,
        package_info TEXT,
        amount_value INTEGER,
        price INTEGER,
        recipient TEXT,
        status TEXT DEFAULT 'pending',
        payment_proof TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER UNIQUE,
        is_counted INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS required_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT,
        channel_title TEXT
    )""")

    for k, v in DEFAULT_SETTINGS.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    c.execute("SELECT COUNT(*) FROM star_packages")
    if c.fetchone()[0] == 0:
        for s in DEFAULT_STARS:
            c.execute("INSERT INTO star_packages (stars) VALUES (?)", (s,))

    c.execute("SELECT COUNT(*) FROM premium_packages")
    if c.fetchone()[0] == 0:
        for m, p in DEFAULT_PREMIUM:
            c.execute("INSERT INTO premium_packages (months, price) VALUES (?, ?)", (m, p))

    conn.commit()
    conn.close()


def S(key):
    conn = db_conn()
    r = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return r[0] if r else ""

def SS(key, val):
    conn = db_conn()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(val)))
    conn.commit()
    conn.close()

def add_user(uid, un, fn, referred_by=None):
    conn = db_conn()
    exists = conn.execute("SELECT user_id FROM users WHERE user_id=?", (uid,)).fetchone()
    if exists:
        conn.execute("UPDATE users SET username=?, first_name=? WHERE user_id=?", (un or "", fn or "", uid))
    else:
        conn.execute("INSERT INTO users (user_id, username, first_name, referred_by) VALUES (?, ?, ?, ?)",
                     (uid, un or "", fn or "", referred_by))
        if referred_by and referred_by != uid:
            ref_exists = conn.execute("SELECT user_id FROM users WHERE user_id=?", (referred_by,)).fetchone()
            if ref_exists:
                conn.execute("INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                             (referred_by, uid))
    conn.commit()
    conn.close()

def get_user(uid):
    conn = db_conn()
    conn.row_factory = sqlite3.Row
    r = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return dict(r) if r else None

def get_all_uids():
    conn = db_conn()
    rows = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    return [r[0] for r in rows]

def is_user_admin(uid):
    if uid == ADMIN_ID:
        return True
    u = get_user(uid)
    return bool(u and u.get("is_admin"))

def set_admin(uid, on=True):
    conn = db_conn()
    conn.execute("UPDATE users SET is_admin=? WHERE user_id=?", (1 if on else 0, uid))
    conn.commit()
    conn.close()

def adjust_balance(uid, delta):
    conn = db_conn()
    conn.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (delta, uid))
    conn.commit()
    conn.close()

# Star packages
def get_star_packages():
    rate = int(S("star_rate_uzs") or "210")
    conn = db_conn()
    rows = conn.execute("SELECT id, stars FROM star_packages ORDER BY stars").fetchall()
    conn.close()
    return [{"id": i, "stars": s, "price": s * rate} for i, s in rows]

def get_star_package(pid):
    rate = int(S("star_rate_uzs") or "210")
    conn = db_conn()
    r = conn.execute("SELECT id, stars FROM star_packages WHERE id=?", (pid,)).fetchone()
    conn.close()
    return {"id": r[0], "stars": r[1], "price": r[1] * rate} if r else None

def add_star_package(stars):
    conn = db_conn()
    conn.execute("INSERT OR IGNORE INTO star_packages (stars) VALUES (?)", (stars,))
    conn.commit()
    conn.close()

def delete_star_package(pid):
    conn = db_conn()
    conn.execute("DELETE FROM star_packages WHERE id=?", (pid,))
    conn.commit()
    conn.close()

# Premium
def get_premium_packages():
    conn = db_conn()
    rows = conn.execute("SELECT id, months, price FROM premium_packages ORDER BY months").fetchall()
    conn.close()
    return [{"id": i, "months": m, "price": p} for i, m, p in rows]

def get_premium_package(pid):
    conn = db_conn()
    r = conn.execute("SELECT id, months, price FROM premium_packages WHERE id=?", (pid,)).fetchone()
    conn.close()
    return {"id": r[0], "months": r[1], "price": r[2]} if r else None

def update_premium_price(pid, price):
    conn = db_conn()
    conn.execute("UPDATE premium_packages SET price=? WHERE id=?", (price, pid))
    conn.commit()
    conn.close()

# Orders
def create_order(uid, otype, info, amt, price, recip):
    conn = db_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO orders (user_id, order_type, package_info, amount_value, price, recipient)
                 VALUES (?, ?, ?, ?, ?, ?)""", (uid, otype, info, amt, price, recip))
    oid = c.lastrowid
    conn.commit()
    conn.close()
    return oid

def get_order(oid):
    conn = db_conn()
    conn.row_factory = sqlite3.Row
    r = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    conn.close()
    return dict(r) if r else None

def update_order_status(oid, status, proof=None):
    conn = db_conn()
    if proof:
        conn.execute("UPDATE orders SET status=?, payment_proof=? WHERE id=?", (status, proof, oid))
    elif status == "completed":
        conn.execute("UPDATE orders SET status=?, completed_at=CURRENT_TIMESTAMP WHERE id=?", (status, oid))

        r = conn.execute("SELECT user_id, price, order_type, amount_value FROM orders WHERE id=?", (oid,)).fetchone()
        if r:
            uid, price, otype, amt = r
            conn.execute("UPDATE users SET total_spent = total_spent + ? WHERE user_id=?", (price, uid))
            if otype == "stars":
                conn.execute("UPDATE users SET stars_bought = stars_bought + ? WHERE user_id=?", (amt, uid))
                ref = conn.execute("SELECT id, referrer_id, is_counted FROM referrals WHERE referred_id=?", (uid,)).fetchone()
                if ref and ref[2] == 0:
                    conn.execute("UPDATE referrals SET is_counted=1 WHERE id=?", (ref[0],))
                    conn.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id=?", (ref[1],))
    else:
        conn.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
    conn.commit()
    conn.close()

# Channels
def get_required_channels():
    conn = db_conn()
    rows = conn.execute("SELECT id, channel_id, channel_title FROM required_channels ORDER BY id").fetchall()
    conn.close()
    return rows

def add_required_channel(ch, title):
    conn = db_conn()
    conn.execute("INSERT INTO required_channels (channel_id, channel_title) VALUES (?, ?)", (ch, title))
    conn.commit()
    conn.close()

def remove_required_channel(cid):
    conn = db_conn()
    conn.execute("DELETE FROM required_channels WHERE id=?", (cid,))
    conn.commit()
    conn.close()

# Stats
def get_stats():
    conn = db_conn()
    r = {}
    for k, q in [
        ("users", "SELECT COUNT(*) FROM users"),
        ("orders", "SELECT COUNT(*) FROM orders"),
        ("completed", "SELECT COUNT(*) FROM orders WHERE status='completed'"),
        ("pending", "SELECT COUNT(*) FROM orders WHERE status='paid'"),
        ("revenue", "SELECT COALESCE(SUM(price),0) FROM orders WHERE status='completed'"),
        ("stars_sold", "SELECT COALESCE(SUM(amount_value),0) FROM orders WHERE status='completed' AND order_type='stars'"),
    ]:
        r[k] = conn.execute(q).fetchone()[0]
    conn.close()
    return r

# Ratings
def get_rating_spending(period="alltime"):
    conn = db_conn()
    conn.row_factory = sqlite3.Row
    if period == "alltime":
        rows = conn.execute("""
            SELECT user_id, username, first_name, total_spent as value, stars_bought
            FROM users WHERE total_spent > 0
            ORDER BY total_spent DESC LIMIT 20
        """).fetchall()
    else:
        interval = "-7 days" if period == "week" else "-30 days"
        rows = conn.execute(f"""
            SELECT u.user_id, u.username, u.first_name,
                   COALESCE(SUM(o.price), 0) as value,
                   COALESCE(SUM(CASE WHEN o.order_type='stars' THEN o.amount_value ELSE 0 END), 0) as stars_bought
            FROM users u LEFT JOIN orders o
                ON u.user_id = o.user_id
                AND o.status='completed'
                AND o.completed_at >= datetime('now', '{interval}')
            GROUP BY u.user_id HAVING value > 0
            ORDER BY value DESC LIMIT 20
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==========================================================
#   HELPERS
# ==========================================================
def fmt(key, **kw):
    t = S(key)
    kw.setdefault("admin", (S("admin_username") or "admin").lstrip("@"))
    for k, v in kw.items():
        t = t.replace("{" + k + "}", str(v))
    return t

async def check_sub(bot, uid):
    chs = get_required_channels()
    bad = []
    for cid, ch_id, title in chs:
        try:
            m = await bot.get_chat_member(ch_id, uid)
            if m.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
                bad.append((ch_id, title))
        except Exception:
            pass
    return bad

def kb_sub_wall(bad):
    rows = []
    for ch_id, title in bad:
        url = f"https://t.me/{ch_id.lstrip('@')}" if ch_id.startswith("@") else f"https://t.me/c/{str(ch_id).replace('-100','')}"
        rows.append([InlineKeyboardButton(text=f"📢 {title}", url=url)])
    rows.append([InlineKeyboardButton(text=S("btn_check_sub"), callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def safe_edit(call, text, kb, bot):
    try:
        await call.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    except TelegramBadRequest:
        with suppress(Exception):
            await call.message.delete()
        await bot.send_message(call.message.chat.id, text, reply_markup=kb, disable_web_page_preview=True)


# ==========================================================
#   STATES
# ==========================================================
class OrderFSM(StatesGroup):
    waiting_recipient = State()
    waiting_payment = State()

class AdminFSM(StatesGroup):
    editing_text = State()
    editing_button = State()
    adding_star = State()
    editing_premium_price = State()
    editing_payment_info = State()
    editing_admin_username = State()
    editing_star_rate = State()
    setting_proof_channel = State()
    adding_channel_id = State()
    adding_channel_title = State()
    editing_payment_api_key = State()
    adding_new_admin = State()
    adjust_balance = State()
    broadcasting = State()


# ==========================================================
#   KEYBOARDS (USER)
# ==========================================================
def kb_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=S("btn_stars"), callback_data="menu:stars")],
        [InlineKeyboardButton(text=S("btn_premium"), callback_data="menu:premium")],
        [InlineKeyboardButton(text=S("btn_help"), callback_data="menu:help"),
         InlineKeyboardButton(text=S("btn_about"), callback_data="menu:about")],
    ])

def kb_stars_list():
    pkgs = get_star_packages()
    rows = []
    row = []
    for p in pkgs:
        row.append(InlineKeyboardButton(text=f"⭐ {p['stars']} — {p['price']:,} so'm", callback_data=f"buy:stars:{p['id']}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=S("btn_back"), callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_premium_list():
    pkgs = get_premium_packages()
    rows = [[InlineKeyboardButton(text=f"💎 {p['months']} oy — {p['price']:,} so'm", callback_data=f"buy:premium:{p['id']}")] for p in pkgs]
    rows.append([InlineKeyboardButton(text=S("btn_back"), callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_ask_username():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=S("btn_myself"), callback_data="username:myself")],
        [InlineKeyboardButton(text=S("btn_cancel"), callback_data="order:cancel")],
    ])

def kb_back_main():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=S("btn_main"), callback_data="menu:main")]])

def kb_help():
    admin_un = (S("admin_username") or "").lstrip("@")
    rows = []
    if admin_un and admin_un not in ("username", ""):
        rows.append([InlineKeyboardButton(text=S("btn_contact_admin"), url=f"https://t.me/{admin_un}")])
    rows.append([InlineKeyboardButton(text=S("btn_main"), callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_pay_copy(card, amount):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Karta raqamini nusxalash", copy_text=CopyTextButton(text=card))],
        [InlineKeyboardButton(text="📋 Summani nusxalash", copy_text=CopyTextButton(text=amount))],
        [InlineKeyboardButton(text=S("btn_cancel"), callback_data="order:cancel")],
    ])


# ==========================================================
#   ADMIN KEYBOARDS
# ==========================================================
def kb_admin_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Star paketlar", callback_data="a:stars"),
         InlineKeyboardButton(text="💎 Premium", callback_data="a:premium")],
        [InlineKeyboardButton(text="💱 Star kursi", callback_data="a:star_rate"),
         InlineKeyboardButton(text="💳 To'lov karta", callback_data="a:payment")],
        [InlineKeyboardButton(text="🔌 To'lov API", callback_data="a:payment_api"),
         InlineKeyboardButton(text="👨‍💼 Admin username", callback_data="a:username")],
        [InlineKeyboardButton(text="📝 Matnlar", callback_data="a:texts"),
         InlineKeyboardButton(text="🔘 Tugma nomlari", callback_data="a:buttons")],
        [InlineKeyboardButton(text="📢 Tolovlar kanali", callback_data="a:proof_ch"),
         InlineKeyboardButton(text="📌 Majburiy obuna", callback_data="a:req_ch")],
        [InlineKeyboardButton(text="👥 Adminlar", callback_data="a:admins"),
         InlineKeyboardButton(text="💰 Balans tahrirlash", callback_data="a:user_balance")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="a:broadcast"),
         InlineKeyboardButton(text="📊 Statistika", callback_data="a:stats")],
    ])

def kb_back_admin():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Admin panel", callback_data="a:back")]])

def kb_cancel(cb):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor", callback_data=cb)]])


# ==========================================================
#   ROUTERS
# ==========================================================
user_router = Router()
admin_router = Router()


# ==========================================================
#   USER HANDLERS
# ==========================================================
@user_router.message(CommandStart())
async def cmd_start(msg: Message, command: CommandObject, state: FSMContext, bot: Bot):
    await state.clear()
    referred_by = None
    if command.args:
        try:
            referred_by = int(command.args[4:]) if command.args.startswith("ref_") else int(command.args)
        except ValueError:
            pass
    add_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, referred_by)

    bad = await check_sub(bot, msg.from_user.id)
    if bad:
        return await msg.answer(fmt("sub_required_text"), reply_markup=kb_sub_wall(bad))

    await msg.answer(fmt("welcome_text", name=msg.from_user.first_name or "do'st"), reply_markup=kb_main())

@user_router.callback_query(F.data == "check_sub")
async def cb_check(call: CallbackQuery, bot: Bot):
    bad = await check_sub(bot, call.from_user.id)
    if bad:
        await call.answer("❌ Hali obuna emas!", show_alert=True)
        return await safe_edit(call, fmt("sub_required_text"), kb_sub_wall(bad), bot)
    await call.answer("✅")
    await safe_edit(call, fmt("welcome_text", name=call.from_user.first_name or "do'st"), kb_main(), bot)

@user_router.callback_query(F.data == "menu:main")
async def cb_main(call: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    bad = await check_sub(bot, call.from_user.id)
    if bad:
        await safe_edit(call, fmt("sub_required_text"), kb_sub_wall(bad), bot)
        return await call.answer()
    await safe_edit(call, fmt("welcome_text", name=call.from_user.first_name or "do'st"), kb_main(), bot)
    await call.answer()

@user_router.callback_query(F.data == "menu:stars")
async def cb_stars(call: CallbackQuery, bot: Bot):
    await safe_edit(call, fmt("stars_menu_text"), kb_stars_list(), bot)
    await call.answer()

@user_router.callback_query(F.data == "menu:premium")
async def cb_prem(call: CallbackQuery, bot: Bot):
    await safe_edit(call, fmt("premium_menu_text"), kb_premium_list(), bot)
    await call.answer()

@user_router.callback_query(F.data == "menu:help")
async def cb_help(call: CallbackQuery, bot: Bot):
    await safe_edit(call, fmt("help_text"), kb_help(), bot)
    await call.answer()

@user_router.callback_query(F.data == "menu:about")
async def cb_about(call: CallbackQuery, bot: Bot):
    await safe_edit(call, fmt("about_text"), kb_back_main(), bot)
    await call.answer()

@user_router.callback_query(F.data.startswith("buy:"))
async def cb_buy(call: CallbackQuery, state: FSMContext):
    _, ot, pid = call.data.split(":")
    pid = int(pid)
    if ot == "stars":
        pk = get_star_package(pid)
        if not pk:
            return await call.answer("❌", show_alert=True)
        info = f"⭐ {pk['stars']} star"
        amt = pk["stars"]
        price = pk["price"]
    else:
        pk = get_premium_package(pid)
        if not pk:
            return await call.answer("❌", show_alert=True)
        info = f"💎 {pk['months']} oy Premium"
        amt = pk["months"]
        price = pk["price"]

    await state.set_state(OrderFSM.waiting_recipient)
    await state.update_data(order_type=ot, package_info=info, amount_value=amt, price=price)
    t = f"🛒 <b>{info}</b>\n💰 <b>{price:,} so'm</b>\n\n{fmt('ask_username_text')}"
    await call.message.edit_text(t, reply_markup=kb_ask_username())
    await call.answer()

@user_router.callback_query(F.data == "username:myself")
async def cb_myself(call: CallbackQuery, state: FSMContext, bot: Bot):
    d = await state.get_data()
    if not d.get("order_type"):
        await state.clear()
        return await call.answer("❌ Sessiya tugagan", show_alert=True)
    un = f"@{call.from_user.username}" if call.from_user.username else f"<a href='tg://user?id={call.from_user.id}'>{call.from_user.first_name}</a>"
    await process_payment(call.message, call.from_user, un, d, state, bot, edit=True)
    await call.answer()

@user_router.message(OrderFSM.waiting_recipient, F.text)
async def recv_recipient(msg: Message, state: FSMContext, bot: Bot):
    r = msg.text.strip()
    if not r.startswith("@"):
        r = "@" + r.lstrip("@")
    if len(r) < 3 or " " in r:
        return await msg.answer("❗️ Noto'g'ri username. Qaytadan kiriting:")
    d = await state.get_data()
    if not d.get("order_type"):
        await state.clear()
        return await msg.answer("❗️ /start bosing.")
    await process_payment(msg, msg.from_user, r, d, state, bot, edit=False)

async def process_payment(msg, user, recipient, d, state, bot, edit=False):
    oid = create_order(user.id, d["order_type"], d["package_info"], d["amount_value"], d["price"], recipient)
    await state.update_data(order_id=oid, recipient=recipient)
    await state.set_state(OrderFSM.waiting_payment)

    card = S("payment_card")
    bank = S("payment_bank")
    holder = S("payment_holder")
    amt = f"{d['price']:,}"
    pt = fmt("payment_text", card=card, bank=bank, holder=holder, amount=amt)
    t = f"🆔 <code>#{oid}</code>\n📦 {d['package_info']}\n👤 <code>{recipient}</code>\n💰 <b>To'lov: {amt} so'm</b>\n\n{pt}"
    kb = kb_pay_copy(card, amt)
    if edit:
        try:
            await msg.edit_text(t, reply_markup=kb)
        except Exception:
            await bot.send_message(msg.chat.id, t, reply_markup=kb)
    else:
        await msg.answer(t, reply_markup=kb)

@user_router.message(OrderFSM.waiting_payment, F.photo)
async def recv_payment(msg: Message, state: FSMContext, bot: Bot):
    d = await state.get_data()
    oid = d.get("order_id")
    if not oid:
        await state.clear()
        return await msg.answer("❗️ /start bosing.")
    fid = msg.photo[-1].file_id
    update_order_status(oid, "paid", fid)

    wt = fmt("waiting_admin_text")
    await msg.answer(f"🆔 <code>#{oid}</code>\n\n{wt}", reply_markup=kb_back_main())

    u = msg.from_user
    tag = f"@{u.username}" if u.username else f"<a href='tg://user?id={u.id}'>{u.first_name}</a>"
    cap = f"🆕 <b>BUYURTMA</b>\n\n🆔 <code>#{oid}</code>\n📦 {d['package_info']}\n💰 <b>{d['price']:,} so'm</b>\n👤 <code>{d['recipient']}</code>\n👨‍💻 {tag} (<code>{u.id}</code>)"

    with suppress(Exception):
        await bot.send_photo(ADMIN_ID, fid, caption=cap, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"ord:approve:{oid}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"ord:reject:{oid}"),
        ]]))
    await state.clear()

@user_router.message(OrderFSM.waiting_payment)
async def recv_payment_wrong(msg: Message):
    await msg.answer("📸 Iltimos, <b>chek rasmini</b> yuboring.")

@user_router.callback_query(F.data == "order:cancel")
async def cb_cancel(call: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await safe_edit(call, fmt("welcome_text", name=call.from_user.first_name or "do'st"), kb_main(), bot)
    await call.answer("Bekor qilindi")


# ==========================================================
#   ADMIN HANDLERS
# ==========================================================
@admin_router.message(Command("admin"))
async def cmd_admin(msg: Message, state: FSMContext):
    if not is_user_admin(msg.from_user.id):
        return
    await state.clear()
    await msg.answer("🛠 <b>Admin panel</b>", reply_markup=kb_admin_main())

@admin_router.callback_query(F.data == "a:back")
async def cb_ab(call: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    await safe_edit(call, "🛠 <b>Admin panel</b>", kb_admin_main(), bot)
    await call.answer()

@admin_router.callback_query(F.data == "a:stats")
async def cb_stats(call: CallbackQuery):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    s = get_stats()
    await call.message.edit_text(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{s['users']}</b>\n"
        f"📦 Buyurtmalar: <b>{s['orders']}</b>\n"
        f"✅ Bajarilgan: <b>{s['completed']}</b>\n"
        f"⏳ Kutilmoqda: <b>{s['pending']}</b>\n"
        f"⭐ Sotilgan starlar: <b>{s['stars_sold']:,}</b>\n"
        f"💰 Daromad: <b>{s['revenue']:,} so'm</b>",
        reply_markup=kb_back_admin()
    )
    await call.answer()

# Star paketlar
@admin_router.callback_query(F.data == "a:stars")
async def cb_admin_stars(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    pkgs = get_star_packages()
    rows = [[InlineKeyboardButton(text=f"⭐ {p['stars']} — {p['price']:,}", callback_data=f"sp:{p['id']}")] for p in pkgs]
    rows += [[InlineKeyboardButton(text="➕ Yangi paket", callback_data="sp:add")],
             [InlineKeyboardButton(text="◀️ Admin panel", callback_data="a:back")]]
    await call.message.edit_text("⭐ <b>Star paketlari</b>\n\nKurs orqali narx hisoblanadi.", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()

@admin_router.callback_query(F.data.startswith("sp:"))
async def cb_sp(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    v = call.data[3:]
    if v == "add":
        await state.set_state(AdminFSM.adding_star)
        return await call.message.edit_text("➕ Star sonini kiriting:", reply_markup=kb_cancel("a:stars"))
    pk = get_star_package(int(v))
    if not pk:
        return await call.answer("Topilmadi")
    await call.message.edit_text(
        f"⭐ <b>{pk['stars']} star</b> — <b>{pk['price']:,} so'm</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"spd:{pk['id']}")],
            [InlineKeyboardButton(text="◀️", callback_data="a:stars")],
        ]))
    await call.answer()

@admin_router.message(AdminFSM.adding_star)
async def msg_add_star(msg: Message, state: FSMContext):
    if not msg.text or not msg.text.isdigit():
        return await msg.answer("❗️ Faqat raqam")
    add_star_package(int(msg.text))
    await state.clear()
    await msg.answer("✅ Qo'shildi", reply_markup=kb_back_admin())

@admin_router.callback_query(F.data.startswith("spd:"))
async def cb_spd(call: CallbackQuery):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    delete_star_package(int(call.data[4:]))
    await call.answer("✅ O'chirildi", show_alert=True)
    await call.message.edit_text("⭐ <b>Star paketlari</b>", reply_markup=kb_back_admin())

# Star kursi
@admin_router.callback_query(F.data == "a:star_rate")
async def cb_rate(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    cur = S("star_rate_uzs")
    await state.set_state(AdminFSM.editing_star_rate)
    await call.message.edit_text(
        f"💱 <b>Star kursi</b>\n\nHozirgi: <b>1 ⭐ = {cur} so'm</b>\n\nYangi kursni kiriting:",
        reply_markup=kb_cancel("a:back"))
    await call.answer()

@admin_router.message(AdminFSM.editing_star_rate)
async def msg_rate(msg: Message, state: FSMContext):
    if not msg.text or not msg.text.isdigit():
        return await msg.answer("❗️ Faqat raqam")
    SS("star_rate_uzs", msg.text)
    await state.clear()
    await msg.answer(f"✅ Yangi kurs: 1 ⭐ = {msg.text} so'm", reply_markup=kb_back_admin())

# Premium
@admin_router.callback_query(F.data == "a:premium")
async def cb_admin_prem(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    pkgs = get_premium_packages()
    rows = [[InlineKeyboardButton(text=f"💎 {p['months']} oy — {p['price']:,}", callback_data=f"pp:{p['id']}")] for p in pkgs]
    rows.append([InlineKeyboardButton(text="◀️ Admin panel", callback_data="a:back")])
    await call.message.edit_text("💎 <b>Premium paketlari</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()

@admin_router.callback_query(F.data.startswith("pp:"))
async def cb_pp(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    pk = get_premium_package(int(call.data[3:]))
    if not pk:
        return await call.answer("Topilmadi")
    await state.set_state(AdminFSM.editing_premium_price)
    await state.update_data(pkg_id=pk["id"])
    await call.message.edit_text(
        f"💎 <b>{pk['months']} oy</b> — hozirgi: <b>{pk['price']:,} so'm</b>\n\nYangi narx:",
        reply_markup=kb_cancel("a:premium"))
    await call.answer()

@admin_router.message(AdminFSM.editing_premium_price)
async def msg_prem(msg: Message, state: FSMContext):
    if not msg.text or not msg.text.isdigit():
        return await msg.answer("❗️")
    d = await state.get_data()
    update_premium_price(d["pkg_id"], int(msg.text))
    await state.clear()
    await msg.answer("✅", reply_markup=kb_back_admin())

# To'lov karta
@admin_router.callback_query(F.data == "a:payment")
async def cb_pay(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    await call.message.edit_text(
        f"💳 <b>To'lov karta</b>\n\n💳 Karta: <code>{S('payment_card')}</code>\n🏦 Bank: {S('payment_bank')}\n👤 Egasi: {S('payment_holder')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Karta", callback_data="ep:payment_card")],
            [InlineKeyboardButton(text="🏦 Bank", callback_data="ep:payment_bank")],
            [InlineKeyboardButton(text="👤 Egasi", callback_data="ep:payment_holder")],
            [InlineKeyboardButton(text="◀️ Admin panel", callback_data="a:back")],
        ]))
    await call.answer()

@admin_router.callback_query(F.data.startswith("ep:"))
async def cb_ep(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    key = call.data[3:]
    await state.set_state(AdminFSM.editing_payment_info)
    await state.update_data(key=key)
    await call.message.edit_text(f"✏️ Hozirgi: <code>{S(key)}</code>\n\nYangi qiymat:", reply_markup=kb_cancel("a:payment"))
    await call.answer()

@admin_router.message(AdminFSM.editing_payment_info)
async def msg_ep(msg: Message, state: FSMContext):
    if not msg.text:
        return await msg.answer("❗️")
    SS((await state.get_data())["key"], msg.text.strip())
    await state.clear()
    await msg.answer("✅", reply_markup=kb_back_admin())

# To'lov API (Click/Mirpay)
@admin_router.callback_query(F.data == "a:payment_api")
async def cb_payapi(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    provider = S("payment_provider") or "qo'lda"
    click_set = "✅" if S("click_secret_key") else "❌"
    mirpay_set = "✅" if S("mirpay_api_key") else "❌"
    text = (f"🔌 <b>To'lov API</b>\n\nHozirgi rejim: <b>{provider}</b>\n\n"
            f"{click_set} Click sozlangan\n{mirpay_set} Mirpay sozlangan\n\n"
            f"💡 Kalitlarni kiritsangiz, avto rejim ishga tushadi.")
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Click sozlash", callback_data="api:click")],
        [InlineKeyboardButton(text="🔧 Mirpay sozlash", callback_data="api:mirpay")],
        [InlineKeyboardButton(text="✅ Click yoq", callback_data="apie:click"),
         InlineKeyboardButton(text="✅ Mirpay yoq", callback_data="apie:mirpay")],
        [InlineKeyboardButton(text="🚫 Qo'lda rejim", callback_data="apie:")],
        [InlineKeyboardButton(text="◀️ Admin panel", callback_data="a:back")],
    ]))
    await call.answer()

@admin_router.callback_query(F.data.startswith("apie:"))
async def cb_apie(call: CallbackQuery):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    provider = call.data.split(":")[1] if len(call.data.split(":")) > 1 else ""
    if provider:
        key_check = "click_secret_key" if provider == "click" else "mirpay_api_key"
        if not S(key_check):
            return await call.answer(f"❗️ Avval {provider} sozlamalarini kiriting", show_alert=True)
    SS("payment_provider", provider)
    mode = provider if provider else "qo'lda"
    await call.answer(f"✅ Rejim: {mode}", show_alert=True)
    await cb_payapi(call, None)

@admin_router.callback_query(F.data.startswith("api:"))
async def cb_api_setup(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    provider = call.data.split(":")[1]
    if provider == "click":
        fields = [("click_merchant_id", "Merchant ID"), ("click_service_id", "Service ID"), ("click_secret_key", "Secret Key")]
    else:
        fields = [("mirpay_merchant_id", "Merchant ID"), ("mirpay_api_key", "API Key"), ("mirpay_secret", "Secret")]
    rows = []
    for k, label in fields:
        mark = "✅" if S(k) else "❌"
        rows.append([InlineKeyboardButton(text=f"{mark} {label}", callback_data=f"setapi:{k}")])
    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="a:payment_api")])
    await call.message.edit_text(
        f"🔧 <b>{provider.upper()}</b>\n\nHar maydonni bosing va qiymat kiriting:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()

@admin_router.callback_query(F.data.startswith("setapi:"))
async def cb_setapi(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    key = call.data.split(":")[1]
    await state.set_state(AdminFSM.editing_payment_api_key)
    await state.update_data(key=key)
    await call.message.edit_text(f"🔑 <b>{key}</b> qiymatini yuboring:", reply_markup=kb_cancel("a:payment_api"))
    await call.answer()

@admin_router.message(AdminFSM.editing_payment_api_key)
async def msg_setapi(msg: Message, state: FSMContext):
    if not msg.text:
        return await msg.answer("❗️")
    d = await state.get_data()
    SS(d["key"], msg.text.strip())
    await state.clear()
    with suppress(Exception):
        await msg.delete()
    await msg.answer(f"✅ Saqlandi: <code>{d['key']}</code>", reply_markup=kb_back_admin())

# Admin username
@admin_router.callback_query(F.data == "a:username")
async def cb_un(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(AdminFSM.editing_admin_username)
    await call.message.edit_text(
        f"👨‍💼 Hozirgi: <code>@{S('admin_username')}</code>\n\nYangi username (@ siz):",
        reply_markup=kb_cancel("a:back"))
    await call.answer()

@admin_router.message(AdminFSM.editing_admin_username)
async def msg_un(msg: Message, state: FSMContext):
    if not msg.text:
        return await msg.answer("❗️")
    un = msg.text.strip().lstrip("@")
    if not un or " " in un or len(un) < 3:
        return await msg.answer("❗️ Noto'g'ri")
    SS("admin_username", un)
    await state.clear()
    await msg.answer(f"✅ @{un}", reply_markup=kb_back_admin())

# Matnlar
@admin_router.callback_query(F.data == "a:texts")
async def cb_texts(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    rows = [[InlineKeyboardButton(text=l, callback_data=f"et:{k}")] for k, l in EDITABLE_TEXTS.items()]
    rows.append([InlineKeyboardButton(text="◀️ Admin panel", callback_data="a:back")])
    await call.message.edit_text(
        "📝 <b>Matnlar</b>\n\n💡 Variables: <code>{name}</code> <code>{admin}</code> <code>{card}</code> <code>{amount}</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()

@admin_router.callback_query(F.data.startswith("et:"))
async def cb_et(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    key = call.data[3:]
    await state.set_state(AdminFSM.editing_text)
    await state.update_data(key=key)
    await call.message.edit_text(
        f"📝 <b>{EDITABLE_TEXTS.get(key)}</b>\n\nHozirgi:\n<code>{S(key)}</code>\n\nYangi matn:",
        reply_markup=kb_cancel("a:texts"))
    await call.answer()

@admin_router.message(AdminFSM.editing_text)
async def msg_et(msg: Message, state: FSMContext):
    new = msg.html_text if (msg.text or msg.caption) else None
    if not new:
        return await msg.answer("❗️ Matn yuboring")
    SS((await state.get_data())["key"], new)
    await state.clear()
    await msg.answer("✅ Saqlandi", reply_markup=kb_back_admin())

# Tugma nomlari
@admin_router.callback_query(F.data == "a:buttons")
async def cb_btns(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    rows = [[InlineKeyboardButton(text=l, callback_data=f"eb:{k}")] for k, l in BTN_KEYS.items()]
    rows.append([InlineKeyboardButton(text="◀️ Admin panel", callback_data="a:back")])
    await call.message.edit_text("🔘 <b>Tugma nomlari</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()

@admin_router.callback_query(F.data.startswith("eb:"))
async def cb_eb(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    key = call.data[3:]
    await state.set_state(AdminFSM.editing_button)
    await state.update_data(key=key)
    await call.message.edit_text(f"🔘 Hozirgi: <code>{S(key)}</code>\n\nYangi nom:", reply_markup=kb_cancel("a:buttons"))
    await call.answer()

@admin_router.message(AdminFSM.editing_button)
async def msg_eb(msg: Message, state: FSMContext):
    if not msg.text or len(msg.text) > 60:
        return await msg.answer("❗️ 60 belgidan kam")
    SS((await state.get_data())["key"], msg.text.strip())
    await state.clear()
    await msg.answer("✅", reply_markup=kb_back_admin())

# Tolovlar kanali
@admin_router.callback_query(F.data == "a:proof_ch")
async def cb_pc(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    cur = S("proof_channel") or "yo'q"
    await state.set_state(AdminFSM.setting_proof_channel)
    await call.message.edit_text(
        f"📢 <b>Tolovlar kanali</b>\n\nHozirgi: <code>{cur}</code>\n\nKanal (@channel)\n⚠️ Bot kanalda admin bo'lsin!\n🗑 O'chirish: <code>-</code>",
        reply_markup=kb_cancel("a:back"))
    await call.answer()

@admin_router.message(AdminFSM.setting_proof_channel)
async def msg_pc(msg: Message, state: FSMContext):
    if not msg.text:
        return await msg.answer("❗️")
    if msg.text.strip() == "-":
        SS("proof_channel", "")
        await state.clear()
        return await msg.answer("🗑", reply_markup=kb_back_admin())
    ch = msg.text.strip()
    if not ch.startswith("@"):
        ch = "@" + ch
    SS("proof_channel", ch)
    await state.clear()
    await msg.answer(f"✅ {ch}\n\n⚠️ Botni kanalga ADMIN qiling!", reply_markup=kb_back_admin())

# Majburiy obuna
@admin_router.callback_query(F.data == "a:req_ch")
async def cb_rc(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    await state.clear()
    chs = get_required_channels()
    t = "📌 <b>Majburiy obuna</b>\n\n"
    t += "\n".join(f"• {ti} ({ci})" for _, ci, ti in chs) if chs else "Kanallar yo'q."
    t += "\n\n⚠️ Bot har kanalda admin bo'lsin!"
    rows = [[InlineKeyboardButton(text=f"🗑 {ti}", callback_data=f"del_ch:{cid}")] for cid, _, ti in chs]
    rows += [[InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_ch")],
             [InlineKeyboardButton(text="◀️ Admin panel", callback_data="a:back")]]
    await call.message.edit_text(t, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()

@admin_router.callback_query(F.data.startswith("del_ch:"))
async def cb_dc(call: CallbackQuery):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    remove_required_channel(int(call.data.split(":")[1]))
    await call.answer("✅", show_alert=True)
    await cb_rc(call, None)

@admin_router.callback_query(F.data == "add_ch")
async def cb_ac(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(AdminFSM.adding_channel_id)
    await call.message.edit_text("📌 Kanal (@channel):", reply_markup=kb_cancel("a:req_ch"))
    await call.answer()

@admin_router.message(AdminFSM.adding_channel_id)
async def msg_aci(msg: Message, state: FSMContext):
    if not msg.text:
        return await msg.answer("❗️")
    ch = msg.text.strip()
    if not ch.startswith("@"):
        ch = "@" + ch
    await state.update_data(ch_id=ch)
    await state.set_state(AdminFSM.adding_channel_title)
    await msg.answer(f"<code>{ch}</code>\n\nKanal nomini yuboring:")

@admin_router.message(AdminFSM.adding_channel_title)
async def msg_act(msg: Message, state: FSMContext):
    if not msg.text:
        return await msg.answer("❗️")
    d = await state.get_data()
    add_required_channel(d["ch_id"], msg.text.strip())
    await state.clear()
    await msg.answer(f"✅ {msg.text.strip()} qo'shildi", reply_markup=kb_back_admin())

# Adminlar
@admin_router.callback_query(F.data == "a:admins")
async def cb_admins(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌ Faqat asosiy admin", show_alert=True)
    await state.set_state(AdminFSM.adding_new_admin)
    await call.message.edit_text(
        "👥 <b>Admin qo'shish</b>\n\nUser ID yuboring.\nO'chirish: <code>-USERID</code>",
        reply_markup=kb_cancel("a:back"))
    await call.answer()

@admin_router.message(AdminFSM.adding_new_admin)
async def msg_aa(msg: Message, state: FSMContext):
    if not msg.text:
        return await msg.answer("❗️")
    txt = msg.text.strip()
    remove = txt.startswith("-")
    if remove:
        txt = txt[1:]
    if not txt.isdigit():
        return await msg.answer("❗️ User ID raqam")
    uid = int(txt)
    if not get_user(uid):
        return await msg.answer("❗️ User botda ro'yxatdan o'tmagan")
    set_admin(uid, not remove)
    await state.clear()
    action = "O'chirildi" if remove else "Qo'shildi"
    await msg.answer(f"✅ {action}: <code>{uid}</code>", reply_markup=kb_back_admin())

# Balans
@admin_router.callback_query(F.data == "a:user_balance")
async def cb_bal(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(AdminFSM.adjust_balance)
    await call.message.edit_text(
        "💰 <b>Balans tahrirlash</b>\n\nFormat:\n<code>USERID SUMMA</code>\n\nMisol:\n<code>123456 50000</code>\n<code>123456 -50000</code>",
        reply_markup=kb_cancel("a:back"))
    await call.answer()

@admin_router.message(AdminFSM.adjust_balance)
async def msg_bal(msg: Message, state: FSMContext):
    if not msg.text:
        return await msg.answer("❗️")
    parts = msg.text.strip().split()
    if len(parts) != 2:
        return await msg.answer("❗️ Format: USERID SUMMA")
    try:
        uid = int(parts[0])
        amount = int(parts[1])
    except ValueError:
        return await msg.answer("❗️ Raqamlar noto'g'ri")
    if not get_user(uid):
        return await msg.answer("❗️ User topilmadi")
    adjust_balance(uid, amount)
    new_bal = get_user(uid)["balance"]
    await state.clear()
    await msg.answer(f"✅ {amount:+,} so'm\nYangi balans: <b>{new_bal:,} so'm</b>", reply_markup=kb_back_admin())

# Broadcast
@admin_router.callback_query(F.data == "a:broadcast")
async def cb_bc(call: CallbackQuery, state: FSMContext):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(AdminFSM.broadcasting)
    await call.message.edit_text("📢 Hammaga yuboriladigan xabar:", reply_markup=kb_cancel("a:back"))
    await call.answer()

@admin_router.message(AdminFSM.broadcasting)
async def msg_bc(msg: Message, state: FSMContext, bot: Bot):
    await state.clear()
    uids = get_all_uids()
    total = len(uids)
    sent = failed = 0
    st = await msg.answer(f"📤 0/{total}")
    for i, uid in enumerate(uids, 1):
        try:
            await bot.copy_message(uid, msg.chat.id, msg.message_id)
            sent += 1
        except Exception:
            failed += 1
        if i % 25 == 0:
            with suppress(Exception):
                await st.edit_text(f"📤 {i}/{total}")
            await asyncio.sleep(1)
    await st.edit_text(f"✅ Yuborildi: <b>{sent}</b>\n❌ Xato: <b>{failed}</b>\n👥 Jami: <b>{total}</b>", reply_markup=kb_back_admin())

# Buyurtma tasdiq/rad
@admin_router.callback_query(F.data.startswith("ord:"))
async def cb_ord(call: CallbackQuery, bot: Bot):
    if not is_user_admin(call.from_user.id):
        return await call.answer()
    _, act, oid = call.data.split(":")
    oid = int(oid)
    o = get_order(oid)
    if not o:
        return await call.answer("Topilmadi", show_alert=True)
    uid = o["user_id"]
    info = o["package_info"]
    price = o["price"]

    if act == "approve":
        update_order_status(oid, "completed")
        with suppress(Exception):
            await bot.send_message(uid, f"🆔 <code>#{oid}</code>\n📦 {info}\n\n{fmt('order_completed_text')}")
        with suppress(TelegramBadRequest):
            await call.message.edit_caption(caption=(call.message.caption or "") + "\n\n✅ <b>TASDIQLANDI</b>")
        pc = S("proof_channel")
        if pc:
            now = datetime.now().strftime("%d.%m.%Y %H:%M")
            with suppress(Exception):
                await bot.send_message(pc, f"✅ <b>Yangi xarid!</b>\n\n📦 {info}\n💰 {price:,} so'm\n👤 {o['recipient'] or '—'}\n🕐 {now}")
        await call.answer("✅", show_alert=True)
    elif act == "reject":
        update_order_status(oid, "rejected")
        with suppress(Exception):
            await bot.send_message(uid, f"🆔 <code>#{oid}</code>\n📦 {info}\n\n{fmt('order_rejected_text')}")
        with suppress(TelegramBadRequest):
            await call.message.edit_caption(caption=(call.message.caption or "") + "\n\n❌ <b>RAD ETILDI</b>")
        await call.answer("❌", show_alert=True)


# ==========================================================
#   MAIN
# ==========================================================
async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    init_db()
    print(f"[DB] Database tayyor: {DB_PATH}")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin_router)
    dp.include_router(user_router)
    await bot.delete_webhook(drop_pending_updates=True)

    print("✅ Bot ishga tushdi: @tezkor_star_bot")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Bot to'xtatildi")
