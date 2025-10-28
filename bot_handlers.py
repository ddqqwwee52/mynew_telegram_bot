import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import google.generativeai as genai

from config import Config
from database import DatabaseManager
from subscription_service import SubscriptionService

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = DatabaseManager()

# Инициализация Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

class BotHandlers:
    def __init__(self):
        pass

    async def start(self, update: Update, context: CallbackContext):
        """Обработчик команды /start"""
        try:
            user = update.effective_user
            db.create_user(user.id, user.username)
            
            welcome_text = (
                f"Привет, {user.first_name}! 👋\n\n"
                "Я бот с интегрированной нейросетью Google Gemini. "
                "Я могу помочь вам с различными задачами:\n"
                "• Ответить на вопросы\n• Написать текст\n• Решить задачи\n• Обсудить идеи\n\n"
                f"🎁 Бесплатно: {Config.FREE_REQUESTS_LIMIT} запросов в сутки\n"
                "💎 С подпиской: неограниченное количество запросов\n\n"
                "Отправьте мне сообщение и я помогу!"
            )
            
            await update.message.reply_text(welcome_text)
            logger.info(f"User {user.id} started the bot")
        except Exception as e:
            logger.error(f"Error in start command: {e}")

    async def handle_message(self, update: Update, context: CallbackContext):
        """Обработчик текстовых сообщений"""
        try:
            user = update.effective_user
            user_message = update.message.text
            
            # Получаем данные пользователя
            user_data = db.get_user(user.id)
            if not user_data:
                db.create_user(user.id, user.username)
                user_data = db.get_user(user.id)

            # Проверяем возможность выполнения запроса
            if not SubscriptionService.can_make_free_request(user_data):
                await self.show_subscription_menu(update, context)
                return

            # Показываем что бот печатает
            await update.message.chat.send_action(action="typing")
            
            # Генерируем ответ через Gemini
            response = model.generate_content(user_message)
            response_text = response.text if response else "Извините, произошла ошибка при обработке запроса."
            
            # Сохраняем запрос и ответ
            db.save_request(user.id, user_message, response_text)
            db.update_request_count(user.id)
            
            # Отправляем ответ
            await update.message.reply_text(
                response_text,
                reply_to_message_id=update.message.message_id
            )
            
            # Показываем оставшиеся запросы
            remaining = SubscriptionService.get_remaining_requests(user_data)
            if remaining != float('inf'):
                await update.message.reply_text(
                    f"🔄 Осталось бесплатных запросов сегодня: {remaining}",
                    reply_to_message_id=update.message.message_id + 1
                )
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "⚠️ Произошла ошибка при обращении к нейросети. Пожалуйста, попробуйте позже."
            )

    async def show_subscription_menu(self, update: Update, context: CallbackContext):
        """Показ меню подписки"""
        try:
            keyboard = [
                [InlineKeyboardButton("💳 Неделя - 89₽", callback_data="sub_week")],
                [InlineKeyboardButton("💳 Месяц - 299₽", callback_data="sub_month")],
                [InlineKeyboardButton("💳 3 месяца - 549₽", callback_data="sub_3month")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                "🚫 Лимит бесплатных запросов исчерпан!\n\n"
                "💎 Приобретите подписку для неограниченного доступа:\n"
                f"• Неделя: {Config.SUBSCRIPTION_PRICES['week']['price']}₽\n"
                f"• Месяц: {Config.SUBSCRIPTION_PRICES['month']['price']}₽\n"
                f"• 3 месяца: {Config.SUBSCRIPTION_PRICES['3month']['price']}₽\n\n"
                "Выберите вариант подписки:"
            )
            
            if update.message:
                await update.message.reply_text(text, reply_markup=reply_markup)
            else:
                await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error showing subscription menu: {e}")

    async def handle_subscription_callback(self, update: Update, context: CallbackContext):
        """Обработчик callback'ов подписки"""
        try:
            query = update.callback_query
            await query.answer()
            
            user = query.from_user
            subscription_type = query.data.replace('sub_', '')
            
            # В реальном боте здесь должна быть интеграция с платежной системой
            # Для демонстрации просто активируем подписку
            subscription_info = Config.SUBSCRIPTION_PRICES.get(subscription_type)
            if subscription_info:
                days = subscription_info['days']
                db.add_subscription(user.id, days)
                price = subscription_info['price']
                
                success_text = (
                    f"🎉 Подписка активирована на {days} дней!\n"
                    f"💎 Теперь у вас неограниченное количество запросов!\n"
                    f"💰 Стоимость: {price}₽\n\n"
                    "Спасибо за покупку! Теперь можете продолжать общение с ботом."
                )
                
                await query.edit_message_text(success_text)
                logger.info(f"User {user.id} purchased {subscription_type} subscription")
            else:
                await query.edit_message_text("❌ Произошла ошибка при активации подписки.")
        except Exception as e:
            logger.error(f"Error handling subscription callback: {e}")

    async def stats(self, update: Update, context: CallbackContext):
        """Показ статистики пользователя"""
        try:
            user = update.effective_user
            user_data = db.get_user(user.id)
            
            if not user_data:
                await update.message.reply_text("Сначала используйте команду /start")
                return
            
            remaining = SubscriptionService.get_remaining_requests(user_data)
            has_subscription = SubscriptionService.has_active_subscription(user_data)
            
            stats_text = (
                f"📊 Ваша статистика:\n\n"
                f"👤 Пользователь: {user.first_name}\n"
                f"🆔 ID: {user.id}\n"
                f"📅 Зарегистрирован: {user_data['created_at'][:10]}\n\n"
            )
            
            if has_subscription:
                subscription_end = user_data['subscription_end']
                stats_text += (
                    f"💎 Статус: Активная подписка\n"
                    f"📅 Подписка действительна до: {subscription_end}\n"
                    f"🔢 Доступно запросов: Неограниченно\n"
                )
            else:
                stats_text += (
                    f"💎 Статус: Без подписки\n"
                    f"🔢 Осталось запросов сегодня: {remaining}/{Config.FREE_REQUESTS_LIMIT}\n"
                    f"📅 Следующий сброс: Завтра\n"
                )
            
            await update.message.reply_text(stats_text)
        except Exception as e:
            logger.error(f"Error showing stats: {e}")
