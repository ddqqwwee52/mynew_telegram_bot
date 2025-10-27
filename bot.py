import os
import logging
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Настройка
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Ключи
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Настройка Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Цены подписок (рубли)
SUBSCRIPTION_PRICES = {
    'week': 199,
    'month': 599, 
    '3months': 1499,
    '6months': 2499
}

# ТВОИ КРИПТО-КОШЕЛЬКИ
CRYPTO_ADDRESSES = {
    'usdt': 'TTPyQybNxws84CbLZqjxptJa1fNoDYzgex',
    'btc': 'bc1qre29jcpyfpkden3c3l5yjymrqqjjvp57m6amvq', 
    'ton': 'UQDjZ3wu-ZziQb_Y5K9utUqbhML0dH7UTol_5AXOcsTHMfk7'
}

# Хранилище (временное)
user_limits = {}
user_subscriptions = {}

def get_user_limits(user_id):
    if user_id not in user_limits:
        user_limits[user_id] = {'text_used': 0, 'image_used': 0}
    return user_limits[user_id]

def is_premium(user_id):
    return user_id in user_subscriptions

# Клавиатура выбора подписки
def get_subscription_keyboard():
    keyboard = [
        [InlineKeyboardButton("💰 НЕДЕЛЯ - 199 руб.", callback_data="sub_week")],
        [InlineKeyboardButton("💎 МЕСЯЦ - 599 руб.", callback_data="sub_month")],
        [InlineKeyboardButton("🚀 3 МЕСЯЦА - 1499 руб.", callback_data="sub_3months")],
        [InlineKeyboardButton("🔥 6 МЕСЯЦЕВ - 2499 руб.", callback_data="sub_6months")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Клавиатура выбора способа оплаты
def get_payment_method_keyboard(subscription_type):
    keyboard = [
        [InlineKeyboardButton("💳 ЮKassa (карта)", callback_data=f"pay_ykassa_{subscription_type}")],
        [InlineKeyboardButton("₿ Криптовалюта", callback_data=f"pay_crypto_{subscription_type}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_subs")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Клавиатура выбора криптовалюты
def get_crypto_keyboard(subscription_type):
    keyboard = [
        [InlineKeyboardButton("USDT (TRC20)", callback_data=f"crypto_usdt_{subscription_type}")],
        [InlineKeyboardButton("BTC (Bitcoin)", callback_data=f"crypto_btc_{subscription_type}")],
        [InlineKeyboardButton("TON (Toncoin)", callback_data=f"crypto_ton_{subscription_type}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_pay_{subscription_type}")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    limits = get_user_limits(user.id)
    
    text_remaining = 15 - limits['text_used']
    image_remaining = 5 - limits['image_used']
    
    premium_status = "⭐ АКТИВНА ПРЕМИУМ ПОДПИСКА" if is_premium(user.id) else "🎫 БЕСПЛАТНЫЙ ДОСТУП"
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

🤖 Я — AI-ассистент на Gemini!

{premium_status}

📊 Лимиты на сегодня:
• Текстовых запросов: {text_remaining}/15
• Генераций изображений: {image_remaining}/5

Просто напиши вопрос или используй команды:
/image описание - создать изображение
/stats - статистика
/subscribe - премиум подписка
"""
    await update.message.reply_text(welcome_text)

# Статистика
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    limits = get_user_limits(user.id)
    
    text_remaining = 15 - limits['text_used']
    image_remaining = 5 - limits['image_used']
    
    stats_text = f"""
📊 ВАША СТАТИСТИКА

Использовано сегодня:
• Текстовых запросов: {limits['text_used']}/15
• Генераций изображений: {limits['image_used']}/5

Осталось сегодня:
• Текстовых запросов: {text_remaining}
• Генераций изображений: {image_remaining}

Статус: {'⭐ ПРЕМИУМ' if is_premium(user.id) else '🎫 БЕСПЛАТНЫЙ'}
"""
    await update.message.reply_text(stats_text)

# Обработка сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = update.message.text
    limits = get_user_limits(user.id)
    
    # Проверяем лимиты для бесплатных пользователей
    if not is_premium(user.id) and limits['text_used'] >= 15:
        await update.message.reply_text(
            "❌ БЕСПЛАТНЫЙ ЛИМИТ ИСЧЕРПАН\n\n"
            "🔄 Лимит обновится через 24 часа\n"
            "🚀 Или получите БЕЗЛИМИТНУЮ подписку:",
            reply_markup=get_subscription_keyboard()
        )
        return
    
    try:
        if not is_premium(user.id):
            limits['text_used'] += 1
        
        # Используем Gemini
        response = model.generate_content(user_message)
        bot_reply = response.text
        
        if is_premium(user.id):
            await update.message.reply_text(bot_reply)
        else:
            text_remaining = 15 - limits['text_used']
            await update.message.reply_text(f"{bot_reply}\n\n📊 Осталось запросов: {text_remaining}/15")
        
    except Exception as e:
        await update.message.reply_text("❌ Ошибка. Попробуйте позже.")

# Генерация изображений
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    limits = get_user_limits(user.id)
    
    if not is_premium(user.id) and limits['image_used'] >= 5:
        await update.message.reply_text(
            "❌ ЛИМИТ ИЗОБРАЖЕНИЙ ИСЧЕРПАН\n\n"
            "Получите безлимитную подписку:",
            reply_markup=get_subscription_keyboard()
        )
        return
    
    await update.message.reply_text(
        "🎨 Генерация изображений временно в разработке.\n"
        "Скоро добавим эту функцию! А пока пользуйтесь текстовыми запросами 🤗"
    )

# Подписка
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_premium(update.effective_user.id):
        await update.message.reply_text("✅ У вас уже активна премиум подписка!")
        return
        
    subscribe_text = """
🚀 ПРЕМИУМ ПОДПИСКА

Получите ПОЛНЫЙ БЕЗЛИМИТНЫЙ ДОСТУП:

♾️ Неограниченные текстовые запросы
♾️ Неограниченная генерация изображений
⚡ Максимальная скорость ответов
🎯 Приоритетная обработка

💰 ВЫБЕРИТЕ ПЕРИОД:
"""
    await update.message.reply_text(subscribe_text, reply_markup=get_subscription_keyboard())

# Обработка ВСЕХ кнопок
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user
    
    # Словари с названиями подписок
    sub_names = {
        'week': 'НЕДЕЛЮ',
        'month': 'МЕСЯЦ', 
        '3months': '3 МЕСЯЦА',
        '6months': '6 МЕСЯЦЕВ'
    }
    
    # Словари с ценами
    sub_prices = SUBSCRIPTION_PRICES
    
    # Словари с названиями криптовалют
    crypto_names = {
        'usdt': 'USDT (TRC20)',
        'btc': 'BTC (Bitcoin)',
        'ton': 'TON (Toncoin)'
    }
    
    # Выбор подписки → выбор способа оплаты
    if data.startswith('sub_'):
        sub_type = data.replace('sub_', '')
        sub_name = sub_names[sub_type]
        price = sub_prices[sub_type]
        
        payment_text = f"""
💳 ВЫБОР СПОСОБА ОПЛАТЫ

Подписка: {sub_name}
Сумма: {price} руб.

Выберите способ оплаты:
"""
        await query.edit_message_text(payment_text, reply_markup=get_payment_method_keyboard(sub_type))
    
    # Выбор ЮKassa
    elif data.startswith('pay_ykassa_'):
        sub_type = data.replace('pay_ykassa_', '')
        price = sub_prices[sub_type]
        
        ykassa_text = f"""
💳 ОПЛАТА ЧЕРЕЗ ЮKASSA

Подписка: {sub_names[sub_type]}
Сумма: {price} руб.

⚡ Ссылка для оплаты: 
(будет добавлена после настройки ЮKassa)

📞 После оплаты пришлите скриншот: @NeuroAssistant_Support
⏱️ Активация в течение 5 минут!
"""
        await query.edit_message_text(ykassa_text)
    
    # Выбор криптовалюты
    elif data.startswith('pay_crypto_'):
        sub_type = data.replace('pay_crypto_', '')
        
        crypto_text = f"""
₿ ОПЛАТА КРИПТОВАЛЮТОЙ

Подписка: {sub_names[sub_type]}
Сумма: {sub_prices[sub_type]} руб.

Выберите криптовалюту:
"""
        await query.edit_message_text(crypto_text, reply_markup=get_crypto_keyboard(sub_type))
    
    # Выбор конкретной криптовалюты
    elif data.startswith('crypto_'):
        parts = data.split('_')
        crypto_type = parts[1]  # usdt, btc, ton
        sub_type = parts[2]     # week, month, etc
        
        address = CRYPTO_ADDRESSES[crypto_type]
        crypto_name = crypto_names[crypto_type]
        price = sub_prices[sub_type]
        sub_name = sub_names[sub_type]
        
        crypto_payment_text = f"""
₿ ОПЛАТА {crypto_name}

Подписка: {sub_name}
Сумма: {price} руб.

💼 Адрес кошелька:
`{address}`

📋 ИНСТРУКЦИЯ:
1. Переведите {price} руб. в {crypto_name} на указанный адрес
2. Обязательно сохраните скриншот перевода
3. Пришлите скриншот: @NeuroAssistant_Support
4. Активируем подписку в течение 15 минут!

⚠️ Внимание: 
• Переводы в криптовалюте необратимы!
• Убедитесь в правильности адреса
• Сохраните хэш транзакции
"""
        await query.edit_message_text(crypto_payment_text, parse_mode='Markdown')
    
    # Назад к способам оплаты
    elif data.startswith('back_to_pay_'):
        sub_type = data.replace('back_to_pay_', '')
        await query.edit_message_text("💳 Выберите способ оплаты:", 
                                    reply_markup=get_payment_method_keyboard(sub_type))
    
    # Назад к подпискам
    elif data == 'back_to_subs':
        await query.edit_message_text("💰 Выберите период подписки:", 
                                    reply_markup=get_subscription_keyboard())

# Главная функция
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("image", handle_image))
    
    # Сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Кнопки (ОДИН обработчик для всех)
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Запуск
    application.run_polling()

if __name__ == '__main__':
    main()
