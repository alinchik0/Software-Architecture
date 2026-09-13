# microservices/locustfile.py
from locust import HttpUser, task, between, events
import logging
import random

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class MicroMusicUser(HttpUser):
    # Пауза между запросами от 1 до 3 секунд
    wait_time = between(1, 3)

    def on_start(self):
        """Выполняется один раз при старте каждого виртуального пользователя"""
        # Генерируем email ОДИН раз для всего жизненного цикла виртуального пользователя
        self.test_email = f"loadtest_{random.randint(1000, 9999)}@example.com"
        self.test_password = "TestPassword123!"
        self.access_token = None

    @task(3)
    def check_health(self):
        """Легковесная проверка здоровья шлюза"""
        response = self.client.get(
            "/health",
            name="API Gateway Health",
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 429:
            logging.warning("🚦 Rate Limit сработал на /health!")
        elif response.status_code != 200:
            logging.error(f"Health check failed: {response.status_code} - {response.text}")

    @task(2)
    def register_user(self):
        """Регистрация нового пользователя"""
        payload = {
            # ИСПРАВЛЕНО: используем тот же email, что и в on_start
            "email": self.test_email,
            "password": self.test_password
        }
        response = self.client.post(
            "/auth/register",
            name="Register User",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 429:
            logging.warning("🚦 Rate Limit сработал на /auth/register!")
        elif response.status_code in [200, 201]:
            logging.info(f"✅ Успешная регистрация: {self.test_email}")
        elif response.status_code == 400:
            logging.warning(f"⚠️ Пользователь уже существует или невалидные данные: {response.text}")
        else:
            logging.error(f"❌ Register failed: {response.status_code} - {response.text}")

    @task(2)
    def login_user(self):
        """Аутентификация пользователя"""
        payload = {
            "email": self.test_email,
            "password": self.test_password
        }
        response = self.client.post(
            "/auth/login",
            name="Login User",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 429:
            logging.warning("🚦 Rate Limit сработал на /auth/login!")
        elif response.status_code == 200:
            try:
                self.access_token = response.json().get("access_token")
                logging.info(f"✅ Успешный логин, получен токен для: {self.test_email}")
            except Exception as e:
                logging.error(f"❌ Ошибка парсинга токена: {e}")
        else:
            # Теперь мы логируем 401, чтобы видеть, если логин всё-таки не проходит
            logging.error(f"❌ Login failed: {response.status_code} - {response.text}")

    @task(1)
    def search_catalog(self):
        """Поиск треков через gRPC прокси"""
        queries = ["rock", "pop", "jazz", "electronic", "test"]
        search_q = random.choice(queries)

        response = self.client.get(
            f"/catalog/search?q={search_q}&limit=10",
            name="Search Catalog",
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 429:
            logging.warning("🚦 Rate Limit сработал на /catalog/search!")
        elif response.status_code != 200:
            logging.error(f"Search failed: {response.status_code} - {response.text}")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logging.info("🚀 Нагрузочное тестирование MicroMusic началось!")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logging.info("🏁 Тестирование завершено. Проверьте метрики!")