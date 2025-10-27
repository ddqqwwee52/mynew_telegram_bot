import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Настройка
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Хранилище
user_limits = {}

def get_user_limits(user_id):
    if user_id not in user_limits:
        user_limits[user_id] = {'text_used': 0}
    return user_limits[user_id]

# Команда /start
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    limits = get_user_limits(user.id)
    text_remaining = 15 - limits['text_used']
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

🤖 Бот запущен и работает!

📊 Лимиты:
• Текстовых запросов: {text_remaining}/15

Просто напиши вопрос!
"""
    update.message.reply_text(welcome_text)

# Обработка сообщений
def handle_text(update: Update, context: CallbackContext):
    user = update.effective_user
    user_message = update.message.text
    limits = get_user_limits(user.id)
    
    if limits['text_used'] >= 15:
        update.message.reply_text("❌ Лимит исчерпан")
        return
    
    limits['text_used'] += 1
    text_remaining = 15 - limits['text_used']
    
    update.message.reply_text(f"✅ Получил: {user_message}\n\n📊 Осталось: {text_remaining}/15")

# Главная функция
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    
    print("🤖 Бот запускается...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
