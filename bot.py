import time
import requests
from bs4 import BeautifulSoup
import os

# === НАСТРОЙКИ ===
SALE_URL = "https://www.sportvision.cz/produkty/muzi+unisex/final-sale-25/"
BASE_URL = "https://www.sportvision.cz"
SEEN_FILE = "seen_items.txt"

# === ДАННЫЕ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_seen(seen_links):
    with open(SEEN_FILE, "w") as f:
        for link in seen_links:
            f.write(link + "\n")

def send_telegram_message(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_TOKEN или TELEGRAM_CHAT_ID не заданы.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("❌ Ошибка Telegram:", response.text)
    except Exception as e:
        print("❌ Telegram исключение:", e)

def check_for_new_items():
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Проверка новых товаров…")
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(SALE_URL, headers=headers)
    if response.status_code != 200:
        print("⚠️ Ошибка загрузки страницы:", response.status_code)
        return

    soup = BeautifulSoup(response.text, "html.parser")
    products = soup.select("div.product-item")

    seen_links = load_seen()
    current_links = set()
    new_items = []

    for product in products:
        link_tag = product.find("a", href=True)
        name_tag = product.select_one(".product-title")
        price_tag = product.select_one(".price")
        image_tag = product.find("img", src=True)

        if not link_tag or not name_tag or not price_tag or not image_tag:
            continue

        link = BASE_URL + link_tag["href"]
        name = name_tag.get_text(strip=True)
        price = price_tag.get_text(strip=True)
        image = image_tag["src"] if image_tag["src"].startswith("http") else "https:" + image_tag["src"]

        current_links.add(link)

        if link not in seen_links:
            new_items.append({
                "name": name,
                "price": price,
                "link": link,
                "image": image
            })

    if new_items:
        print(f"🆕 Найдено новых товаров: {len(new_items)}")
        for item in new_items:
            message = (
                f"<b>{item['name']}</b>\n"
                f"💰 {item['price']}\n"
                f"<a href='{item['link']}'>🔗 Перейти к товару</a>\n"
                f"<a href='{item['image']}'>🖼️ Фото</a>"
            )
            send_telegram_message(message)
            print(f"📤 Отправлено: {item['name']}")
    else:
        print("Новых товаров нет.")

    save_seen(current_links)

# === ЦИКЛ ===
if __name__ == "__main__":
    while True:
        check_for_new_items()
        time.sleep(2 * 60 * 60)
