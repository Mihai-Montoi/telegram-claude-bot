#!/bin/bash
set -e

echo "=== Telegram Claude Bot Setup ==="
echo ""

# ── 1. Claude Code ────────────────────────────────────────────────
if ! command -v claude &>/dev/null; then
    echo "[1/5] Installing Claude Code..."
    curl -fsSL https://claude.ai/install.sh | bash
    # reload PATH so claude is available in this session
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "[1/5] Claude Code already installed."
fi

# ── 2. Python venv ────────────────────────────────────────────────
echo "[2/5] Setting up Python virtual environment..."

PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

if ! python3 -m venv --help &>/dev/null 2>&1; then
    echo "    Installing python${PYTHON_VER}-venv..."
    sudo apt install -y "python${PYTHON_VER}-venv"
fi

python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
echo "    Dependencies installed."

# ── 3. .env ───────────────────────────────────────────────────────
echo "[3/5] Configuration..."

if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "    Edit .env with your credentials:"
    echo "      TELEGRAM_BOT_TOKEN  — from @BotFather on Telegram"
    echo "      ALLOWED_USER_IDS    — from @userinfobot on Telegram"
    echo ""
    read -p "    Open .env now? [Y/n] " ans
    if [[ "$ans" != "n" && "$ans" != "N" ]]; then
        ${EDITOR:-nano} .env
    fi
else
    echo "    .env already exists, skipping."
fi

# ── 4. MCP Telegram plugin (server.ts) ───────────────────────────
echo "[4/5] Installing MCP Telegram plugin..."

PLUGIN_DIR="$HOME/.claude/plugins/marketplaces/claude-plugins-official/external_plugins/telegram"
mkdir -p "$PLUGIN_DIR"
cp server.ts "$PLUGIN_DIR/server.ts"
echo "    Installed to $PLUGIN_DIR/server.ts"

# ── 5. systemd service ────────────────────────────────────────────
echo "[5/5] Installing systemd service..."

if ! command -v systemctl &>/dev/null; then
    echo "    systemd not available — skipping service install."
    echo "    Run manually: .venv/bin/python bot.py"
else
    USER_NAME=$(whoami)
    DIR=$(pwd)
    sed "s|YOUR_USER|$USER_NAME|g; s|/home/$USER_NAME/telegram-claude-bot|$DIR|g" \
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
fi
