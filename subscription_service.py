from datetime import datetime
from config import Config

class SubscriptionService:
    @staticmethod
    def has_active_subscription(user_data: dict) -> bool:
        """Проверка активной подписки"""
        if not user_data or not user_data.get('subscription_end'):
            return False
        
        try:
            subscription_end = datetime.strptime(
                user_data['subscription_end'], '%Y-%m-%d'
            ).date()
            return subscription_end >= datetime.now().date()
        except (ValueError, TypeError):
            return False

    @staticmethod
    def can_make_free_request(user_data: dict) -> bool:
        """Проверка возможности бесплатного запроса"""
        if not user_data:
            return False
            
        if SubscriptionService.has_active_subscription(user_data):
            return True
        
        today = datetime.now().date()
        last_request = user_data.get('last_request_date')
        
        # Если последний запрос был не сегодня, сбрасываем счетчик
        if last_request != str(today):
            return True
            
        return user_data.get('free_requests_used', 0) < Config.FREE_REQUESTS_LIMIT

    @staticmethod
    def get_remaining_requests(user_data: dict) -> int:
        """Получение количества оставшихся запросов"""
        if not user_data:
            return 0
            
        if SubscriptionService.has_active_subscription(user_data):
            return float('inf')  # Бесконечные запросы
        
        today = datetime.now().date()
        last_request = user_data.get('last_request_date')
        
        if last_request != str(today):
            return Config.FREE_REQUESTS_LIMIT
            
        return max(0, Config.FREE_REQUESTS_LIMIT - user_data.get('free_requests_used', 0))
