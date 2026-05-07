#!/bin/bash
set -e

echo "=== Telegram Claude Bot Setup ==="
echo ""

# ── 1. Claude Code ────────────────────────────────────────────────
if ! command -v claude &>/dev/null; then
    echo "[1/4] Installing Claude Code..."
    npm install -g @anthropic-ai/claude-code
else
    echo "[1/4] Claude Code already installed: $(claude --version 2>/dev/null || echo 'ok')"
fi

# ── 2. Python venv ────────────────────────────────────────────────
echo "[2/4] Setting up Python virtual environment..."

if ! python3 -m venv --help &>/dev/null; then
    PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "    Installing python${PYTHON_VER}-venv..."
    sudo apt install -y "python${PYTHON_VER}-venv"
fi

python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
echo "    Dependencies installed."

# ── 3. .env ───────────────────────────────────────────────────────
echo "[3/4] Configuration..."

if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "    Edit .env and add your Telegram bot token:"
    echo "    - Get a token from @BotFather on Telegram"
    echo "    - Get your user ID from @userinfobot on Telegram"
    echo ""
    read -p "    Open .env now? [Y/n] " ans
    if [[ "$ans" != "n" && "$ans" != "N" ]]; then
        ${EDITOR:-nano} .env
    fi
else
    echo "    .env already exists, skipping."
fi

# ── 4. systemd service ────────────────────────────────────────────
echo "[4/4] Installing systemd service..."

USER=$(whoami)
DIR=$(pwd)
sed "s|YOUR_USER|$USER|g; s|/home/$USER/telegram-claude-bot|$DIR|g" \
    telegram-bot.service > /tmp/telegram-bot.service

sudo cp /tmp/telegram-bot.service /etc/systemd/system/telegram-bot.service
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl restart telegram-bot

echo ""
echo "=== Done! ==="
echo ""
echo "Bot status:  sudo systemctl status telegram-bot"
echo "Logs:        sudo journalctl -u telegram-bot -f"
echo "Restart:     sudo systemctl restart telegram-bot"
