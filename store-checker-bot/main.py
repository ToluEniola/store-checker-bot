import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pygame
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import requests
from scraperHelpers import check_stock_zara, check_stock_bershka, check_stock_mango, check_stock_pullandbear

with open("config.json", "r") as config_file:
    config = json.load(config_file)

urls_to_check = config["urls"]
sleep_min_seconds = config["sleep_min_seconds"]
sleep_max_seconds = config["sleep_max_seconds"]

pygame.mixer.init()

cart_status = {item["url"]: False for item in urls_to_check}

load_dotenv()
BOT_API = os.getenv("BOT_API")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_API or not CHAT_ID:
    print("BOT_API or CHAT_ID not found in .env file. Telegram messages will be disabled.")
    TELEGRAM_ENABLED = False
else:
    TELEGRAM_ENABLED = True

def play_sound(sound_file):
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.play()

def send_telegram_message(message):
    if not TELEGRAM_ENABLED:
        print("Telegram message skipped (missing BOT_API or CHAT_ID).")
        return
    url = f"https://api.telegram.org/bot{BOT_API}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        print("Telegram message sent.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")

def notify(sizes_in_stock, url):
    sizes_str = ", ".join(sizes_in_stock)
    message = f"🛍️ Sizes {sizes_str} Back In Stock!!!!\nLink: {url}"
    print(f"Alert: {message}")
    play_sound('Crystal.mp3')
    send_telegram_message(message)

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--log-level=3")
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
chrome_options.add_argument(
    "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

store_funcs = {
    "zara": check_stock_zara,
    "bershka": check_stock_bershka,
    "mango": check_stock_mango,
    "pullandbear": check_stock_pullandbear,
}

while True:
    for item in urls_to_check:
        try:
            url = item.get("url")
            store = item.get("store")
            sizes = item.get("sizes", [])

            if cart_status[url]:
                print(f"Skipping {url} - already notified.")
                continue

            driver.get(url)
            print("--------------------------------")
            print(f"Checking {store} | {url} | sizes: {sizes}")

            check_func = store_funcs.get(store)
            if not check_func:
                print(f"Unknown store: {store}")
                continue

            sizes_in_stock = check_func(driver, sizes)

            if sizes_in_stock and isinstance(sizes_in_stock, list):
                notify(sizes_in_stock, url)
            else:
                print(f"No stock found.")

        except Exception as e:
            print(f"Error checking {url}: {e}")

    sleep_time = random.randint(sleep_min_seconds, sleep_max_seconds)
    print(f"Sleeping for {sleep_time // 60}m {sleep_time % 60}s...")
    time.sleep(sleep_time)