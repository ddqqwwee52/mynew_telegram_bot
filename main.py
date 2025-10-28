import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from config import Config
from bot_handlers import BotHandlers

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска бота"""
    try:
        if not Config.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN не установлен в переменных окружения")
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY не установлен в переменных окружения")
        
        # Создание приложения
        application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        handlers = BotHandlers()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", handlers.start))
        application.add_handler(CommandHandler("stats", handlers.stats))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
        application.add_handler(CallbackQueryHandler(handlers.handle_subscription_callback, pattern="^sub_"))
        
        # Запуск бота
        logger.info("Бот запущен...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()
