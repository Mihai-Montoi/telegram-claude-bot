import asyncio
import os
import re
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ENV_FILE = Path(__file__).parent / ".env"

ALLOWED_USER_IDS: set[int] = set(
    int(uid) for uid in os.getenv("ALLOWED_USER_IDS", "").split(",") if uid.strip()
)

ADMIN_USER_ID: int = int(os.environ["ADMIN_USER_ID"])

SESSIONS_DIR = Path.home() / ".telegram_bot"
fresh_chats: set[int] = set()


def chat_dir(chat_id: int) -> Path:
    d = SESSIONS_DIR / str(chat_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_allowed_users() -> None:
    ids_str = ",".join(str(uid) for uid in sorted(ALLOWED_USER_IDS))
    content = ENV_FILE.read_text()
    if re.search(r"^ALLOWED_USER_IDS=.*$", content, re.MULTILINE):
        content = re.sub(r"^ALLOWED_USER_IDS=.*$", f"ALLOWED_USER_IDS={ids_str}", content, flags=re.MULTILINE)
    else:
        content += f"\nALLOWED_USER_IDS={ids_str}"
    ENV_FILE.write_text(content)


async def call_claude(message: str, chat_id: int) -> str:
    cwd = chat_dir(chat_id)
    is_fresh = chat_id in fresh_chats

    cmd = ["claude"]
    if not is_fresh:
        cmd.append("--continue")
    cmd.extend(["-p", message])

    if is_fresh:
        fresh_chats.discard(chat_id)

    def _run() -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(cwd),
        )

    result = await asyncio.to_thread(_run)
    if result.returncode == 143:
        return result.stdout.strip() or "Comandă executată (conexiunea a fost întreruptă)."
    return result.stdout.strip() or result.stderr.strip() or "(fără răspuns)"


def is_allowed(user_id: int) -> bool:
    return not ALLOWED_USER_IDS or user_id in ALLOWED_USER_IDS


async def request_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = user.full_name
    username = f"@{user.username}" if user.username else "(fără username)"

    await update.message.reply_text("Cererea ta de acces a fost trimisă administratorului.")

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Aprobă", callback_data=f"approve:{user.id}"),
            InlineKeyboardButton("❌ Respinge", callback_data=f"reject:{user.id}"),
        ]
    ])

    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=f"🔔 Cerere acces nou:\n\n👤 Nume: {name}\n🔗 Username: {username}\n🆔 ID: `{user.id}`",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        await request_access(update, context)
        return
    fresh_chats.add(update.effective_chat.id)
    await update.message.reply_text(
        "Salut! Sunt Claude Code, rulând local pe serverul tău.\n"
        "Pot executa comenzi, citi fișiere, scrie cod și orice altceva.\n\n"
        "/reset — începe o conversație nouă"
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"User ID: `{update.effective_user.id}`", parse_mode="Markdown")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    fresh_chats.add(update.effective_chat.id)
    await update.message.reply_text("Conversație nouă pornită.")


async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    action, user_id_str = query.data.split(":", 1)
    user_id = int(user_id_str)

    if action == "approve":
        ALLOWED_USER_IDS.add(user_id)
        save_allowed_users()
        await query.edit_message_text(f"✅ Utilizatorul `{user_id}` a fost aprobat.", parse_mode="Markdown")
        await context.bot.send_message(chat_id=user_id, text="✅ Accesul tău a fost aprobat! Scrie /start pentru a începe.")
    elif action == "reject":
        await query.edit_message_text(f"❌ Utilizatorul `{user_id}` a fost respins.", parse_mode="Markdown")
        await context.bot.send_message(chat_id=user_id, text="❌ Cererea ta de acces a fost respinsă.")


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        await request_access(update, context)
        return

    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    msg = update.message
    caption = msg.caption or ""

    try:
        if msg.photo:
            file = await context.bot.get_file(msg.photo[-1].file_id)
            ext = "jpg"
        elif msg.document:
            file = await context.bot.get_file(msg.document.file_id)
            ext = Path(msg.document.file_name or "file").suffix.lstrip(".") or "bin"
        else:
            return

        dest = chat_dir(chat_id) / f"upload_{file.file_unique_id}.{ext}"
        await file.download_to_drive(dest)

        prompt = f"Am primit un fișier salvat la: {dest}\n"
        if caption:
            prompt += f"Mesajul utilizatorului: {caption}\n"
        prompt += "Te rog să-l analizezi."

        response = await call_claude(prompt, chat_id)
        for i in range(0, max(len(response), 1), 4096):
            await msg.reply_text(response[i : i + 4096])

    except subprocess.TimeoutExpired:
        await msg.reply_text("Timeout — procesarea a durat prea mult.")
    except Exception as e:
        await msg.reply_text(f"Eroare: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        await request_access(update, context)
        return

    chat_id = update.effective_chat.id
    user_text = update.message.text

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        response = await call_claude(user_text, chat_id)
        for i in range(0, max(len(response), 1), 4096):
            await update.message.reply_text(response[i : i + 4096])
    except subprocess.TimeoutExpired:
        await update.message.reply_text("Timeout — comanda a durat prea mult.")
    except Exception as e:
        await update.message.reply_text(f"Eroare: {e}")


def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(handle_approval))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot pornit. Ctrl+C pentru oprire.")
    app.run_polling()


if __name__ == "__main__":
    main()
