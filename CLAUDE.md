# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

## Setup

Copy `.env.example` to `.env` and fill in the two keys:
- `TELEGRAM_BOT_TOKEN` — get it from [@BotFather](https://t.me/BotFather) on Telegram
- `ANTHROPIC_API_KEY` — from [console.anthropic.com](https://console.anthropic.com)

## Architecture

Single-file bot (`bot.py`) built on:
- **`python-telegram-bot` v21+** (async) — handles Telegram webhook/polling, commands, and message routing
- **`anthropic` SDK** — calls Claude via streaming (`messages.stream`)

**Conversation memory** is stored in a module-level `dict[int, list]` keyed by `chat_id`. Each entry is a list of `{"role", "content"}` dicts passed directly to the Claude API. History is trimmed to the last `MAX_HISTORY` messages after every turn. Memory is in-process only — it resets when the bot restarts.

**Commands:** `/start` (greeting), `/reset` (clears history for that chat).

**Message flow:** user text → appended to history → streamed to Claude → full response appended to history → sent back to Telegram (split at 4096 chars if needed). On API error the failed user message is removed from history so the conversation stays valid.

## Model

Uses `claude-opus-4-7` with streaming. To switch models, change the `MODEL` constant at the top of `bot.py`.
