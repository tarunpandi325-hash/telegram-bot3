import asyncio
import aiosqlite
import logging
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

# ================= CONFIG =================
TOKEN = 8360784420:AAEZ0sR4V_erE0FjRmTI4RLeK51sxBddbo8"
ADMINS = [8503115617, 6761125512, 6617032248]

UPI_ID = "rahu1whereim@ptyes"
BINANCE_ID = "1189640561"

INR = 93
DB = "bot.db"

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()

# ================= DATABASE =================
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product TEXT,
            plan TEXT,
            price INTEGER,
            status TEXT
        )""")
        await db.commit()

async def add_user(uid):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (uid,))
        await db.commit()

async def is_verified(uid):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT verified FROM users WHERE id=?", (uid,))
        row = await cur.fetchone()
        return row and row[0] == 1

async def verify_user(uid):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET verified=1 WHERE id=?", (uid,))
        await db.commit()

async def update_balance(uid, amt):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amt, uid))
        await db.commit()

async def get_balance(uid):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT balance FROM users WHERE id=?", (uid,))
        row = await cur.fetchone()
        return row[0] if row else 0

async def add_order(uid, product, plan, price):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO orders (user_id, product, plan, price, status) VALUES (?, ?, ?, ?, ?)",
            (uid, product, plan, price, "pending")
        )
        await db.commit()

async def update_order(uid, status):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "UPDATE orders SET status=? WHERE user_id=? AND status='pending'",
            (status, uid)
        )
        await db.commit()

# ================= GET PENDING ORDER =================
async def get_pending_order(uid):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT product, plan, price FROM orders WHERE user_id=? AND status='pending' ORDER BY id DESC LIMIT 1",
            (uid,)
        )
        return await cur.fetchone()


# ================= PRODUCTS =================
PRODUCTS = {
    "ios": {
        "fluorite": [
            ("1 Day", 5),
            ("7 Day", 15),
            ("30 Day", 25)
        ],
        "migul": [
            ("1 Day", 5),
            ("30 Day", 20)
        ],
        "proxy": [
            ("1 Day", 5),
            ("30 Day", 20)
        ],
        "imazing": [
            ("60 Day", 15)
        ],
        "dns": [
            ("30 Day", 10)
        ]
    },

    "android": {
        "hg": [
            ("1 Day", 3),
            ("10 Day", 8),
            ("30 Day", 18)
        ],
        "dripclient": [
            ("1 Day", 3),
            ("10 Day", 8),
            ("30 Day", 12)
        ],
        "hexxcker": [
            ("1 Day", 3),
            ("10 Day", 8),
            ("30 Day", 12)
        ]
    },

    "pc": {
        "streamer": [
            ("30 Day", 20),
            ("Lifetime", 30)
        ],
        "streamerplus": [   # ✅ FIXED (removed underscore)
            ("30 Day", 25),
            ("Lifetime", 40)
        ],
        "obsidian": [
            ("30 Day", 15),
            ("Lifetime", 30)
        ],
        "silent": [
            ("30 Day", 15),
            ("Lifetime", 23)
        ]
    }
}

# ================= PLAN =================
@dp.callback_query(F.data.startswith("plan|"))
async def plan(c: types.CallbackQuery):
    try:
        _, name, plan_name, price = c.data.split("|")
        price = int(price)

        # save selected product in memory
        user_data[c.from_user.id] = {
            "product": name,
            "plan": plan_name,
            "price": price
        }

    except:
        return await c.answer("❌ Error selecting plan", show_alert=True)

    # save to DB
    await add_order(c.from_user.id, name, plan_name, price)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 UPI", callback_data="upi"),
            InlineKeyboardButton(text="🪙 Binance", callback_data="binance")
        ],
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back"),
            InlineKeyboardButton(text="📞 Support", callback_data="support")
        ]
    ])

    await c.message.edit_text(
        f"🧾 Order Created\n\n"
        f"📦 Product: {name}\n"
        f"📅 Plan: {plan_name}\n"
        f"💰 Amount: ₹{price * INR}\n\n"
        f"👉 Choose payment method below:",
        reply_markup=kb
    )

    await c.answer()

# ================= STATE =================
user_data = {}
def payment_nav():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back"),
            InlineKeyboardButton(text="📞 Support", callback_data="support")
        ]
    ])

# ================= MENUS =================
def verify_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Verify Account", callback_data="verify")]
    ])


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 SHOP NOW", callback_data="shop")],
        [
            InlineKeyboardButton(text="💰 BALANCE", callback_data="balance"),
            InlineKeyboardButton(text="🎰 LUCKY SPIN", callback_data="spin")
        ],
        [InlineKeyboardButton(text="📞 SUPPORT", callback_data="support")]
    ])

# ================= CALLBACK HANDLERS =================

# ================= BACK =================
@dp.callback_query(F.data == "back")
async def back(c: types.CallbackQuery):
    await c.answer()

    try:
        await c.message.edit_text(
            "💙 Main Menu",
            reply_markup=main_menu()
        )
    except:
        # fallback if message is photo
        await c.message.delete()
        await c.message.answer(
            "💙 Main Menu",
            reply_markup=main_menu()
        )

# ================= SUPPORT =================
@dp.callback_query(F.data == "support")
async def support(c: types.CallbackQuery):
    await c.answer()

    await c.message.edit_text(
        "📞 SUPPORT MENU\n\n"
        "👤 Admin Contacts:\n"
        "• @mar1xff\n"
        "• @bhavisss\n"
        "• @pssysmglr\n\n"
        "💬 Contact any admin for help anytime.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back")]
        ])
    )


# ================= SPIN MENU =================
@dp.callback_query(F.data == "spin")
async def spin_menu(c: types.CallbackQuery):
    await c.answer()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 SPIN NOW", callback_data="spin_start")],
        [InlineKeyboardButton(text="🏠 Back", callback_data="back")]
    ])

    await c.message.edit_text(
        "🎰 LUCK SPIN\n\n"
        "🔥 Try your luck and win rewards!\n"
        "💎 You can win balance or get nothing\n\n"
        "👇 Press spin to play",
        reply_markup=kb
    )


# ================= SPIN ACTION =================
@dp.callback_query(F.data == "spin_start")
async def spin_start(c: types.CallbackQuery):
    import random
    import asyncio

    await c.answer()

    slots = ["💔", "🍀", "🎉", "🔥", "😢", "🪙"]
    rewards = [0, 0, 5, 10, 20, 50, 100]

    losing_msgs = [
        "😢 Better luck next time!",
        "🍀 Try again, luck will come!",
        "💔 So close!",
        "🎯 Try again!"
    ]

    reward = random.choice(rewards)

    msg = await c.message.edit_text("🎰 SPINNING...")

    # 🔥 animation
    for _ in range(10):
        await asyncio.sleep(0.3)
        await msg.edit_text(f"🎰 SPINNING...\n\n{random.choice(slots)}")

    if reward > 0:
        await update_balance(c.from_user.id, reward)
        text = (
            f"🎰 RESULT\n\n"
            f"🎉 You won ₹{reward}!\n"
            f"🔥 GG! Lucky win!"
        )
    else:
        text = (
            f"🎰 RESULT\n\n"
            f"{random.choice(losing_msgs)}"
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Spin Again", callback_data="spin_start")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back")]
    ])

    await msg.edit_text(text, reply_markup=kb)

# ================= START =================
@dp.message(Command("start"))
async def start(msg: types.Message):
    uid = msg.from_user.id

    await add_user(uid)

    # 🔐 CHECK VERIFIED (DB controls one-time verification)
    if await is_verified(uid):
        await msg.answer(
            "💙 Welcome back to Marscot!",
            reply_markup=main_menu()
        )
        return

    # ❌ NOT VERIFIED → SHOW VERIFY ONLY ONCE
    await msg.answer(
        "💙 Welcome to Marscot Premium Store\n\n"
        "🛍 Your all-in-one digital shop for iOS, Android & PC tools.\n\n"
        "✨ Features:\n"
        "• Browse premium products\n"
        "• Choose flexible plans\n"
        "• Pay via UPI or Binance\n"
        "• Fast order processing\n"
        "• 24/7 support available\n\n"
        "🔐 Verification required (one-time only)\n\n"
        "👇 Click below to verify your account",
        reply_markup=verify_menu()
    )


# ================= VERIFY =================
@dp.callback_query(F.data == "verify")
async def verify(c: types.CallbackQuery):
    uid = c.from_user.id

    # ❌ STOP IF ALREADY VERIFIED
    if await is_verified(uid):
        return await c.answer("Already verified ✅", show_alert=True)

    username = c.from_user.username or "NoUsername"

    for admin in ADMINS:
        await bot.send_message(
            admin,
            f"🔐 Verification Request\n\nUser ID: {uid}\nUsername: @{username}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✅ Approve", callback_data=f"vok_{uid}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"vno_{uid}")
            ]])
        )

    await c.message.edit_text("⏳ Wait for admin approval...")

# ✅ APPROVE
@dp.callback_query(F.data.startswith("vok_"))
async def approve_user(c: types.CallbackQuery):
    if c.from_user.id not in ADMINS:
        return await c.answer("Not allowed", show_alert=True)

    uid = int(c.data.split("_")[1])

    # ❌ STOP DOUBLE VERIFY
    if await is_verified(uid):
        return await c.answer("Already verified", show_alert=True)

    await verify_user(uid)

    await bot.send_message(uid, "✅ You are verified! Use /start")

    await c.message.edit_reply_markup()
    await c.answer("Approved")

# ❌ REJECT
@dp.callback_query(F.data.startswith("vno_"))
async def reject_user(c: types.CallbackQuery):
    if c.from_user.id not in ADMINS:
        return await c.answer("Not allowed", show_alert=True)

    uid = int(c.data.split("_")[1])

    await bot.send_message(uid, "❌ Your verification was rejected. Contact support.")

    # remove buttons
    await c.message.edit_reply_markup()

    await c.answer("User rejected")

# ================= SHOP =================
@dp.callback_query(F.data == "shop")
async def shop(c: types.CallbackQuery):
    if not await is_verified(c.from_user.id):
        return await c.answer("Verify first", show_alert=True)

    kb = [
        [InlineKeyboardButton(text="🍎 iOS", callback_data="ios")],
        [InlineKeyboardButton(text="🤖 Android", callback_data="android")],
        [InlineKeyboardButton(text="💻 PC", callback_data="pc")],
        [InlineKeyboardButton(text="⬅ Back", callback_data="back")]
    ]
    await c.message.edit_text("🛍 Select Category:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))


# ================= CATEGORY =================
@dp.callback_query(F.data.in_(["ios", "android", "pc"]))
async def category(c: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text=p.upper(), callback_data=f"prod_{c.data}_{p}")]
        for p in PRODUCTS[c.data]
    ]
    kb.append([InlineKeyboardButton(text="⬅ Back", callback_data="shop")])

    await c.message.edit_text("📦 Select Product:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))


# ================= PRODUCT =================
@dp.callback_query(F.data.startswith("prod_"))
async def product(c: types.CallbackQuery):
    try:
        _, cat, name = c.data.split("_")
    except:
        return await c.answer("❌ Error loading product", show_alert=True)

    plans = PRODUCTS[cat][name]

    kb = [
        [InlineKeyboardButton(
            text=f"{plan} - ₹{price * INR}",
            callback_data=f"plan|{name}|{plan}|{price}"   # ✅ IMPORTANT FIX
        )]
        for plan, price in plans
    ]

    kb.append([InlineKeyboardButton(text="⬅ Back", callback_data=cat)])

    await c.message.edit_text(
        f"💰 {name.upper()} Plans:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

    await c.answer()  # ✅ fix button loading issue

# ================= PAYMENT =================
@dp.callback_query(F.data == "upi")
async def upi(c: types.CallbackQuery):
    d = user_data.get(c.from_user.id)

    if not d:
        return await c.answer("❌ Select product first", show_alert=True)

    await c.answer()

    text = (
        f"💳 UPI PAYMENT\n\n"
        f"👤 User: @{c.from_user.username or 'NoUsername'}\n"
        f"📦 Product: {d['product']}\n"
        f"📅 Plan: {d['plan']}\n"
        f"💰 Amount: ₹{d['price'] * INR}\n\n"
        f"UPI: {UPI_ID}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back"),
            InlineKeyboardButton(text="📞 Support", callback_data="support")
        ]
    ])

    try:
        await c.message.edit_media(
            media=types.InputMediaPhoto(
                media=FSInputFile("qr.jpg"),
                caption=text
            ),
            reply_markup=kb
        )
    except:
        await bot.send_photo(
            chat_id=c.from_user.id,
            photo=FSInputFile("qr.jpg"),
            caption=text,
            reply_markup=kb
        )

# ================= BINANCE =================
@dp.callback_query(F.data == "binance")
async def binance(c: types.CallbackQuery):
    d = user_data.get(c.from_user.id)

    if not d:
        return await c.answer("❌ Select product first", show_alert=True)

    await c.answer()

    text = (
        f"🪙 BINANCE PAYMENT\n\n"
        f"👤 User: @{c.from_user.username or 'NoUsername'}\n"
        f"📦 Product: {d['product']}\n"
        f"📅 Plan: {d['plan']}\n"
        f"💰 Amount: ${d['price']}\n\n"
        f"🆔 Binance ID: {BINANCE_ID}\n\n"
        f"📸 Send payment proof after payment"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back"),
            InlineKeyboardButton(text="📞 Support", callback_data="support")
        ]
    ])

    try:
        await c.message.edit_media(
            media=types.InputMediaPhoto(
                media=FSInputFile("binance.jpg"),
                caption=text
            ),
            reply_markup=kb
        )
    except:
        await bot.send_photo(
            chat_id=c.from_user.id,
            photo=FSInputFile("binance.jpg"),
            caption=text,
            reply_markup=kb
        )

# ================= PROOF HANDLER =================
@dp.message(F.photo | F.video)
async def proof(msg: types.Message):
    uid = msg.from_user.id
    data = user_data.get(uid)

    if not data:
        return await msg.answer("❌ No active order found")

    username = msg.from_user.username or "NoUsername"

    caption = (
        f"🧾 PAYMENT PROOF\n\n"
        f"👤 User: @{username} ({uid})\n"
        f"📦 Product: {data['product']}\n"
        f"📅 Plan: {data['plan']}\n"
        f"💰 Price: ₹{data['price'] * INR}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{uid}"),
        InlineKeyboardButton(text="❌ Deny", callback_data=f"deny_{uid}")
    ]])

    for admin in ADMINS:
        try:
            if msg.photo:
                await bot.send_photo(
                    admin,
                    msg.photo[-1].file_id,
                    caption=caption,
                    reply_markup=kb
                )
            else:
                await bot.send_video(
                    admin,
                    msg.video.file_id,
                    caption=caption,
                    reply_markup=kb
                )
        except Exception as e:
            print("Admin send error:", e)

    await msg.answer("⏳ Proof sent to admin for approval")


# ================= ADMIN ===============
@dp.callback_query(F.data.startswith("approve_"))
async def approve(c: types.CallbackQuery):
    if c.from_user.id not in ADMINS:
        return await c.answer("Not allowed", show_alert=True)

    uid = int(c.data.split("_")[1])

    await update_order(uid, "approved")

    await bot.send_message(
        uid,
        "⚠️ KEY SYSTEM UNDER MAINTENANCE ⚠️\n\n"
        "🔧 Currently our key delivery system is under maintenance.\n"
        "📞 Please contact support for manual delivery.\n\n"
        "👤 Admins:\n"
        "• @mar1xff\n"
        "• @bhavisss\n"
        "• @pssysmglr"
    )

    await c.message.edit_reply_markup()
    await c.answer("Approved")

@dp.callback_query(F.data.startswith("deny_"))
async def deny(c: types.CallbackQuery):
    if c.from_user.id not in ADMINS:
        return await c.answer("Not allowed", show_alert=True)

    uid = int(c.data.split("_")[1])

    await update_order(uid, "denied")

    await bot.send_message(uid, "❌ Payment Rejected")

    await c.message.edit_reply_markup()
    await c.answer("Rejected")

# ================= SUPPORT =================
@dp.callback_query(F.data == "support")
async def support(c: types.CallbackQuery):
    await c.answer()

    await c.message.edit_text(
        "📞 SUPPORT MENU\n\n"
        "👤 Admin Contacts:\n"
        "• @mar1xff\n"
        "• @bhavisss\n"
        "• @pssysmglr\n\n"
        "💬 Contact any admin for help.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back")]
        ])
    )

# ================= BALANCE =================
@dp.callback_query(F.data == "balance")
async def balance(c: types.CallbackQuery):
    bal = await get_balance(c.from_user.id)
    await c.message.edit_text(f"Balance: ₹{bal}", reply_markup=main_menu())


# ================= BROADCAST =================
@dp.message(Command("broadcast"))
async def broadcast(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return

    async with aiosqlite.connect(DB) as db:
        users = await db.execute_fetchall("SELECT id FROM users")

    for u in users:
        try:
            if msg.reply_to_message:
                await msg.reply_to_message.copy_to(u[0])
            else:
                await bot.send_message(u[0], msg.text.replace("/broadcast",""))
        except:
            pass

    await msg.answer("Done")

# ================= RUN =================
async def main():
    await init_db()
    print("BOT RUNNING")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())