import os
import logging
import asyncio
import gspread
import tempfile
from datetime import datetime
from aiohttp import web
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

BOT_TOKEN    = os.environ.get("BOT_TOKEN",    "8843645838:AAEp5tyJZ1bxG9OtbSBeUH5RwIULmmS-jdU")
SHEET_ID     = os.environ.get("SHEET_ID",     "1v6HGZypAhRDoDNvEHUG9rjwIkNrQDQXQjHJkuL_TLe8")
WEBHOOK_URL  = os.environ.get("WEBHOOK_URL",  "")
PORT         = int(os.environ.get("PORT",     8080))
CREDS_JSON   = os.environ.get("GOOGLE_CREDENTIALS", "")

KANAL_YIGITLAR = "https://t.me/imombuxoriy_yigitlar_uchun"
KANAL_QIZLAR   = "https://t.me/imombuxoriy_qizlar_uchun"

NAME, PHONE, DEPARTMENT = range(3)

DEPARTMENTS = [
    "1️⃣ Yozgi Qur'on kursi",
    "2️⃣ Qorilik madrasasi",
    "3️⃣ Islomiy ilmlar universiteti",
    "4️⃣ Ayollar bo'limi",
]
DEPT_NAMES = {
    "1️⃣ Yozgi Qur'on kursi":          "Yozgi Qur'on kursi",
    "2️⃣ Qorilik madrasasi":            "Qorilik madrasasi",
    "3️⃣ Islomiy ilmlar universiteti":  "Islomiy ilmlar universiteti",
    "4️⃣ Ayollar bo'limi":              "Ayollar bo'limi",
}

def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    if CREDS_JSON:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write(CREDS_JSON)
        tmp.flush()
        creds_path = tmp.name
    else:
        creds_path = "credentials.json"

    creds  = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(SHEET_ID).sheet1

    all_vals = sheet.get_all_values()
    if not all_vals or sheet.cell(1, 1).value != "№":
        sheet.insert_row(
            ["№", "Sana", "Ism", "Telefon", "Bo'lim", "Telegram ID", "Username"],
            index=1
        )
    return sheet


def save_to_sheet(data: dict):
    try:
        sheet  = get_sheet()
        number = len(sheet.get_all_values())
        row = [
            number,
            datetime.now().strftime("%d.%m.%Y %H:%M"),
            data["name"],
            data["phone"],
            data["department"],
            data["telegram_id"],
            data.get("username", "-"),
        ]
        sheet.append_row(row)
        logger.info(f"✅ Sheets ga yozildi: {data['name']} — {data['department']}")
    except Exception as e:
        logger.error(f"❌ Google Sheets xatosi: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum va rohmatulloh! 👋\n\n"
        "Imom Buxoriy Xalqaro Akademiyasiga xush kelibsiz!\n\n"
        "Iltimos, ismingizni yozib qoldiring.",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(
        "Telefon raqamingizni yozib qoldiring, siz bilan bog'lana olishimiz uchun.\n\n"
        "📞 Namuna: +99891234567"
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not (phone.startswith("+998") and len(phone) == 13 and phone[1:].isdigit()):
        await update.message.reply_text(
            "❌ Noto'g'ri format.\n"
            "Iltimos, +998XXXXXXXXX ko'rinishida kiriting.\n\n"
            "📞 Namuna: +99891234567"
        )
        return PHONE

    context.user_data["phone"] = phone
    keyboard = [[d] for d in DEPARTMENTS]
    await update.message.reply_text(
        "Qaysi bo'limda o'qimoqchisiz yoki farzandingizni o'qitmoqchisiz:\n\n"
        "1️⃣ Yozgi Qur'on kursi\n"
        "2️⃣ Qorilik madrasasi\n"
        "3️⃣ Islomiy ilmlar universiteti\n"
        "4️⃣ Ayollar bo'limi",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
    )
    return DEPARTMENT


async def get_department(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dept_raw = update.message.text.strip()
    if dept_raw not in DEPT_NAMES:
        keyboard = [[d] for d in DEPARTMENTS]
        await update.message.reply_text(
            "❌ Iltimos, quyidagi tugmalardan birini tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
        )
        return DEPARTMENT

    user = update.message.from_user
    department = DEPT_NAMES[dept_raw]

    data = {
        "name":        context.user_data["name"],
        "phone":       context.user_data["phone"],
        "department":  department,
        "telegram_id": str(user.id),
        "username":    f"@{user.username}" if user.username else "-",
    }

    if department == "Ayollar bo'limi":
        kanal = KANAL_QIZLAR
    else:
        kanal = KANAL_YIGITLAR

    loop = asyncio.get_event_loop()
    await asyncio.gather(
        loop.run_in_executor(None, save_to_sheet, data),
        update.message.reply_text(
            "✅ Tanlovingiz qabul qilindi!\n\n"
            "Qabul suhbati 72 soat ichida ushbu kanalda bo'lib o'tadi.\n"
            f"Kanalga qo'shilish uchun havolani bosing:\n"
            f"👉 {kanal}",
            reply_markup=ReplyKeyboardRemove()
        )
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def health(request):
    return web.Response(text="OK")


async def webhook_handler(request):
    bot_app = request.app["bot_app"]
    data    = await request.json()
    update  = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return web.Response(text="OK")


async def main():
    bot_app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME:       [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            DEPARTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_department)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    bot_app.add_handler(conv)

    if WEBHOOK_URL:
        logger.info(f"Webhook rejimida ishga tushmoqda: {WEBHOOK_URL}")
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook",
            drop_pending_updates=True
        )
        web_app = web.Application()
        web_app["bot_app"] = bot_app
        web_app.router.add_get("/",         health)
        web_app.router.add_post("/webhook", webhook_handler)
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        logger.info(f"Server ishga tushdi: port {PORT}")
        try:
            await asyncio.Event().wait()
        finally:
            await bot_app.stop()
            await bot_app.shutdown()
            await runner.cleanup()
    else:
        logger.info("Polling rejimida ishga tushmoqda (lokal test)...")
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()


if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
