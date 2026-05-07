# Telegram Claude Bot

Un bot Telegram care folosește [Claude Code](https://claude.ai/code) instalat local ca backend — fără API key separat. Poți trimite mesaje pe Telegram și Claude le procesează pe serverul tău, putând executa comenzi, citi fișiere și orice altceva.

## Cum funcționează

```
Telegram → Bot → claude --continue -p "mesaj" → răspuns → Telegram
```

Botul apelează CLI-ul `claude` ca subprocess. Fiecare chat Telegram are propria sesiune izolată în `~/.telegram_bot/{chat_id}/`.

## Cerințe

- Linux (Debian/Ubuntu recomandat)
- Python 3.10+
- Node.js (pentru Claude Code)
- Un bot Telegram (creat prin [@BotFather](https://t.me/BotFather))

## Instalare rapidă

```bash
git clone https://github.com/YOUR_USERNAME/telegram-claude-bot
cd telegram-claude-bot
chmod +x setup.sh
./setup.sh
```

Scriptul instalează automat:
1. Claude Code (`npm install -g @anthropic-ai/claude-code`)
2. Virtualenv Python cu dependințele necesare
3. Serviciul systemd (pornire automată la restart)

## Instalare manuală

### 1. Claude Code

```bash
npm install -g @anthropic-ai/claude-code
claude login   # autentificare cu contul Anthropic
```

### 2. Dependințe Python

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3. Configurare

```bash
cp .env.example .env
nano .env
```

```env
TELEGRAM_BOT_TOKEN=token_de_la_BotFather
ALLOWED_USER_IDS=id_telegram_al_tau   # găsit la @userinfobot
```

### 4. Serviciu systemd

```bash
sed "s|YOUR_USER|$(whoami)|g" telegram-bot.service | sudo tee /etc/systemd/system/telegram-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-bot
```

## Comenzi disponibile

| Comandă | Descriere |
|---------|-----------|
| `/start` | Pornește conversația |
| `/reset` | Șterge istoricul conversației curente |
| `/myid`  | Afișează Telegram user ID-ul tău |

## Securitate

- Setează `ALLOWED_USER_IDS` în `.env` cu ID-ul tău Telegram — altfel oricine poate rula comenzi pe serverul tău
- Fișierul `.env` este în `.gitignore` și nu va fi publicat

## Gestionare serviciu

```bash
sudo systemctl status telegram-bot    # stare
sudo systemctl restart telegram-bot   # repornire
sudo journalctl -u telegram-bot -f    # log-uri live
```
