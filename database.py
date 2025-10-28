import sqlite3
import logging
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_name: str = Config.DATABASE_NAME):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Инициализация таблиц в базе данных"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Таблица пользователей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        free_requests_used INTEGER DEFAULT 0,
                        last_request_date DATE,
                        subscription_end DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица запросов к нейросети
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        request_text TEXT,
                        response_text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def get_user(self, user_id: int) -> dict:
        """Получение информации о пользователе"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM users WHERE user_id = ?', 
                    (user_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    return {
                        'user_id': result[0],
                        'username': result[1],
                        'free_requests_used': result[2],
                        'last_request_date': result[3],
                        'subscription_end': result[4],
                        'created_at': result[5]
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def create_user(self, user_id: int, username: str):
        """Создание нового пользователя"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO users (user_id, username) 
                    VALUES (?, ?)
                ''', (user_id, username))
                conn.commit()
                logger.info(f"User {user_id} created")
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")

    def update_request_count(self, user_id: int):
        """Обновление счетчика запросов"""
        try:
            today = datetime.now().date()
            
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                user = self.get_user(user_id)
                
                if user and user['last_request_date'] != str(today):
                    # Сброс счетчика если новый день
                    cursor.execute('''
                        UPDATE users 
                        SET free_requests_used = 1, last_request_date = ?
                        WHERE user_id = ?
                    ''', (today, user_id))
                else:
                    # Увеличение счетчика
                    cursor.execute('''
                        UPDATE users 
                        SET free_requests_used = free_requests_used + 1, 
                            last_request_date = ?
                        WHERE user_id = ?
                    ''', (today, user_id))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating request count for user {user_id}: {e}")

    def add_subscription(self, user_id: int, days: int):
        """Добавление подписки пользователю"""
        try:
            subscription_end = datetime.now() + timedelta(days=days)
            
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET subscription_end = ? 
                    WHERE user_id = ?
                ''', (subscription_end.date(), user_id))
                conn.commit()
                logger.info(f"Subscription added for user {user_id} for {days} days")
        except Exception as e:
            logger.error(f"Error adding subscription for user {user_id}: {e}")

    def save_request(self, user_id: int, request: str, response: str):
        """Сохранение запроса и ответа в базу данных"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO requests (user_id, request_text, response_text) 
                    VALUES (?, ?, ?)
                ''', (user_id, request, response))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving request for user {user_id}: {e}")
