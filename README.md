# Telegram Claude Bot

A Telegram bot that uses a locally installed [Claude Code](https://claude.ai/code) as its backend — no separate Anthropic API key required. Send messages on Telegram and Claude processes them on your server, executing commands, reading files, writing code, and anything else you need.

## How it works

```
Telegram → Bot → claude --continue -p "message" → response → Telegram
```

The bot calls the `claude` CLI as a subprocess. Each Telegram chat has its own isolated session stored in `~/.telegram_bot/{chat_id}/`.

## Requirements

- Linux (Debian/Ubuntu recommended)
- Python 3.10+
- `curl`
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- A Claude Code account ([claude.ai/code](https://claude.ai/code))

## Quick install

```bash
git clone https://github.com/Mihai-Montoi/telegram-claude-bot
cd telegram-claude-bot
chmod +x setup.sh
./setup.sh
```

The script automatically:
1. Installs Claude Code via the official installer (`curl -fsSL https://claude.ai/install.sh | bash`)
2. Creates a Python virtual environment and installs dependencies
3. Installs and enables a systemd service (auto-start on reboot)

## Manual install

### 1. Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
claude login
```

### 2. Python dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3. Configuration

```bash
cp .env.example .env
nano .env
```

```env
TELEGRAM_BOT_TOKEN=your_token_from_BotFather
ALLOWED_USER_IDS=your_telegram_user_id   # find it at @userinfobot
```

### 4. Systemd service

```bash
sed "s|YOUR_USER|$(whoami)|g" telegram-bot.service | sudo tee /etc/systemd/system/telegram-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-bot
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the conversation |
| `/reset` | Clear the current conversation history |
| `/myid`  | Show your Telegram user ID |

## Security

- Set `ALLOWED_USER_IDS` in `.env` to your Telegram user ID — otherwise anyone can run commands on your server
- The `.env` file is in `.gitignore` and will never be published
- Find your user ID by sending `/start` to [@userinfobot](https://t.me/userinfobot) on Telegram

## Managing the service

```bash
sudo systemctl status telegram-bot     # check status
sudo systemctl restart telegram-bot    # restart
sudo journalctl -u telegram-bot -f     # live logs
```
