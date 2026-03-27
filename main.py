import os
import telebot
import requests
from bs4 import BeautifulSoup
import time
import threading

# Получаем токен из переменных окружения хостинга по ключу 'BOT_TOKEN'
TOKEN = os.environ.get('BOT_TOKEN')

# Защита от ошибки: если токен забыли указать
if not TOKEN:
    raise ValueError("Не найден BOT_TOKEN в переменных окружения! Укажите его в настройках хостинга.")

bot = telebot.TeleBot(TOKEN)
subscribed_users = set()

# Боевой режим: при запуске бот еще не знает последних новостей
last_news = None 

def get_latest_news():
    """Парсит сайт Звезды и достает ссылку на самую свежую новость."""
    url = 'https://zvezda.org.ru/'
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_item = soup.find('a', class_='news-list__item')
        if news_item:
            return news_item.get('href')
        return None
    except Exception as e:
        print(f"Ошибка при проверке сайта: {e}")
        return None

def checker_loop():
    """Фоновый цикл проверки сайта раз в час."""
    global last_news
    while True:
        print("Проверяю сайт...")
        current_news = get_latest_news()
        
        # Если новость нашлась и она отличается от той, что в памяти
        if current_news and current_news != last_news:
            # Если это не первый запуск (когда last_news был None)
            if last_news is not None:
                print("Найдена новая новость! Делаю рассылку...")
                full_link = f"https://zvezda.org.ru{current_news}"
                
                for chat_id in list(subscribed_users):
                    try:
                        bot.send_message(
                            chat_id, 
                            f"❗️ На сайте Звезды появилась новая запись!\n\nЧитать тут: {full_link}"
                        )
                    except Exception as e:
                        print(f"Не удалось отправить сообщение {chat_id}: {e}")
            
            # Обновляем память бота новой ссылкой
            last_news = current_news
            
        # Боевой режим: пауза 3600 секунд (1 час) перед следующей проверкой
        time.sleep(3600) 

@bot.message_handler(commands=['start'])
def start_command(message):
    """Добавляет пользователя в рассылку при команде /start"""
    chat_id = message.chat.id
    subscribed_users.add(chat_id)
    bot.send_message(
        chat_id, 
        "Привет! Я добавил тебя в список рассылки. Буду присылать уведомления о новинках от Звезды!"
    )

if __name__ == '__main__':
    # Запускаем бесконечный цикл проверок в фоне
    checker_thread = threading.Thread(target=checker_loop, daemon=True)
    checker_thread.start()
    
    print("Бот успешно запущен в боевом режиме! Жду сообщений.")
    bot.infinity_polling()