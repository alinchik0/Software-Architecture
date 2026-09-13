# microservices/locustfile.py
from locust import HttpUser, task, between, events
import logging
import random

# Настройка логирования в профессиональном формате
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class MicroMusicUser(HttpUser):
    # Пауза между запросами от 1 до 3 секунд
    wait_time = between(1, 3)

    @task(3)
    def search_catalog(self):
        """Поиск треков (основная читающая нагрузка на систему)"""
        queries = ["rock", "pop", "jazz", "electronic", "test", "music"]
        search_q = random.choice(queries)

        response = self.client.get(
            f"/catalog/search?q={search_q}&limit=10",
            name="Search Catalog",
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 429:
            logging.warning("[RATE LIMIT] Triggered on /catalog/search")
        elif response.status_code != 200:
            logging.error(f"[ERROR] Search failed: {response.status_code} - {response.text}")

    @task(1)
    def check_health(self):
        """Легковесная проверка здоровья шлюза"""
        response = self.client.get(
            "/health",
            name="API Gateway Health",
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 429:
            logging.warning("[RATE LIMIT] Triggered on /health")
        elif response.status_code != 200:
            logging.error(f"[HEALTH CHECK] Failed with status {response.status_code}: {response.text}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logging.info("[TEST START] MicroMusic read-only load testing initiated.")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logging.info("[TEST STOP] Testing completed. Review metrics in Grafana.")