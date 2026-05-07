import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

ALLOWED_USER_IDS: set[int] = set(
    int(uid) for uid in os.getenv("ALLOWED_USER_IDS", "").split(",") if uid.strip()
)

# Fiecare chat are propriul director — conversațiile sunt izolate
SESSIONS_DIR = Path.home() / ".telegram_bot"

# Chat-uri care au primit /reset și trebuie să înceapă sesiune nouă
fresh_chats: set[int] = set()


def chat_dir(chat_id: int) -> Path:
    d = SESSIONS_DIR / str(chat_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def call_claude(message: str, chat_id: int) -> str:
    cwd = chat_dir(chat_id)
    is_fresh = chat_id in fresh_chats

    cmd = ["claude"]
    if not is_fresh:
        cmd.append("--continue")
    cmd.extend(["-p", message])

    if is_fresh:
        fresh_chats.discard(chat_id)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(cwd),
    )

    return result.stdout.strip() or result.stderr.strip() or "(fără răspuns)"


def is_allowed(user_id: int) -> bool:
    return not ALLOWED_USER_IDS or user_id in ALLOWED_USER_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("Acces neautorizat.")
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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("Acces neautorizat.")
        return

    chat_id = update.effective_chat.id
    user_text = update.message.text

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        response = call_claude(user_text, chat_id)

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot pornit. Ctrl+C pentru oprire.")
    app.run_polling()


if __name__ == "__main__":
    main()
