import os
import telebot
import requests
from bs4 import BeautifulSoup
import time
import threading

# Получаем токен из переменных окружения
TOKEN = os.environ.get('BOT_TOKEN')

if not TOKEN:
    raise ValueError("Не найден BOT_TOKEN в переменных окружения!")

bot = telebot.TeleBot(TOKEN)
subscribed_users = set()

# Боевой режим: при запуске бот ничего не помнит
last_news = None 
last_product = None

def get_latest_news(soup):
    """Ищет ссылку на самую свежую новость."""
    news_item = soup.find('a', class_='news-list__item')
    if news_item:
        return news_item.get('href')
    return None

def get_latest_product(soup):
    """Ищет ссылку на первый товар в блоке новинок."""
    # ВАЖНО: Замени 'ВСТАВЬ_КЛАСС_ТОВАРА' на реальный класс ссылки на товар.
    # Это может быть класс самой карточки товара, ее заголовка или кнопки "Подробнее".
    product_item = soup.find('a', class_='catalog-list__item')
    if product_item:
        return product_item.get('href')
    return None

def checker_loop():
    """Фоновый цикл проверки сайта."""
    global last_news, last_product
    url = 'https://zvezda.org.ru/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    while True:
        print("Проверяю сайт (новости и каталог)...")
        try:
            # Скачиваем страницу ОДИН раз для обеих проверок
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status() 
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- ПРОВЕРКА НОВОСТЕЙ ---
            current_news = get_latest_news(soup)
            if current_news and current_news != last_news:
                if last_news is not None:
                    print("Найдена новая новость!")
                    full_link = f"https://zvezda.org.ru{current_news}"
                    for chat_id in list(subscribed_users):
                        try:
                            bot.send_message(chat_id, f"📰 **Новая запись в блоге!**\n\nЧитать тут: {full_link}", parse_mode='Markdown')
                        except Exception:
                            pass
                last_news = current_news

            # --- ПРОВЕРКА НОВИНОК КАТАЛОГА ---
            current_product = get_latest_product(soup)
            if current_product and current_product != last_product:
                if last_product is not None:
                    print("Найден новый товар!")
                    # Иногда ссылки в каталоге уже содержат домен, сделаем проверку
                    if current_product.startswith('http'):
                        full_product_link = current_product
                    else:
                        full_product_link = f"https://zvezda.org.ru{current_product}"
                        
                    for chat_id in list(subscribed_users):
                        try:
                            bot.send_message(chat_id, f"🔥 **Новинка в каталоге Звезды!**\n\nСмотреть модель: {full_product_link}", parse_mode='Markdown')
                        except Exception:
                            pass
                last_product = current_product

        except Exception as e:
            print(f"Ошибка при проверке сайта: {e}")
            
        # Пауза 3600 секунд (1 час)
        time.sleep(3600) 

@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    subscribed_users.add(chat_id)
    bot.send_message(
        chat_id, 
        "Привет! Я добавил тебя в список рассылки.\nТеперь я слежу и за **новостями**, и за **новинками каталога** Звезды!",
        parse_mode='Markdown'
    )

if __name__ == '__main__':
    checker_thread = threading.Thread(target=checker_loop, daemon=True)
    checker_thread.start()
    print("Бот 2.0 запущен! Отслеживаем новости и товары.")
    bot.infinity_polling()
