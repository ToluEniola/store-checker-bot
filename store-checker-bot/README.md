# 🛍️ Store Stock Checker Bot (Telegram + Sound Notifications)

A Python bot that watches product pages for specific sizes and pings you (Telegram message + notification sound) as soon as your size is back in stock. Supports Zara, Bershka, Mango, and Pull&Bear.

This started as a fork/rework of [CerenAkyr/ZaraStockChecker](https://github.com/CerenAkyr/ZaraStockChecker) — credit to the original author for the core idea and Zara scraping logic. This version adds/changes:
- Bershka, Mango, and Pull&Bear support (`scraperHelpers.py`)
- A generic "brute force" size scanner used as a fallback for stores without a clean DOM structure
- Per-item stock tracking so each URL only alerts once until you reset it

---

## Features

- Headless Selenium Chrome scraping
- Telegram alerting (optional)
- Sound notifications using `pygame`
- Per-item URL + size configuration, with configurable sleep delay
- `.env`-based secret handling (never committed)

---

## Requirements

- Python 3.8+
- Google Chrome

---

## How to Use

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Install the required packages
```bash
pip install -r requirements.txt
```

### 3. Configure `config.json`
Add the products you want to track. Each entry needs a `store`, a `url`, and a list of `sizes`:
```json
{
  "urls": [
    {
      "store": "zara",
      "url": "https://www.zara.com/ie/en/example-product.html",
      "sizes": ["S", "M"]
    },
    {
      "store": "bershka",
      "url": "https://www.bershka.com/ie/example-product.html",
      "sizes": ["38"]
    }
  ],
  "sleep_min_seconds": 15,
  "sleep_max_seconds": 30
}
```
`store` must be one of: `zara`, `bershka`, `mango`, `pullandbear`.

### 4. (Optional) Set up Telegram alerts
- In Telegram, message **BotFather** and run `/newbot` to create a bot and get an API token.
- Message your new bot once (or add it to a group) so you can find your `chat_id`.
- Copy `.env.example` to `.env` and fill in your values:
```env
BOT_API=your_telegram_bot_api_key
CHAT_ID=your_chat_id
```
If you skip this step, the bot still runs and plays a sound locally — it just won't send Telegram messages.

### 5. Run it
```bash
python main.py
```

---

## Notes

- `.env` is git-ignored on purpose — never commit real bot tokens there.
- This scrapes live retail sites via Selenium; site markup can change at any time, which may break a store's scraper.

## Disclaimer

This repository is for educational and personal use only. It has no commercial/profit motive. Use responsibly and respect the terms of service of any site you point it at.
