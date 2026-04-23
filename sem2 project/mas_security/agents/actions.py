import hashlib
import time
import json
from typing import Dict, Any

# Простой трекер для дедупликации (in-memory)
class RequestTracker:
    def __init__(self, ttl: int = 300):
        self.cache: Dict[str, float] = {}
        self.ttl = ttl  # секунд

    def is_duplicate(self, payload: str) -> bool:
        h = hashlib.md5(payload.encode()).hexdigest()
        now = time.time()
        if h in self.cache and now - self.cache[h] < self.ttl:
            return True
        self.cache[h] = now
        # Очистка старых записей
        expired = [k for k, v in self.cache.items() if now - v >= self.ttl]
        for k in expired: del self.cache[k]
        return False

# Журнал действий и алертов
ALERT_LOG: list[dict] = []

def execute_decision(report_str: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Парсит JSON-отчёт агента и исполняет действие."""
    try:
        # Убираем markdown-обёртку, если LLM её добавил
        cleaned = report_str.replace("```json", "").replace("```", "").strip()
        report = json.loads(cleaned)
    except json.JSONDecodeError:
        report = {"action": "flag", "reasoning": "Invalid report format", "risk_level": "medium"}

    action = report.get("action", "allow").lower()
    alert = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event_type": event.get("type", "unknown"),
        "action_taken": action,
        "risk_level": report.get("risk_level", "unknown"),
        "reasoning": report.get("reasoning", ""),
        "status": "executed"
    }
    ALERT_LOG.append(alert)

    # Имитация исполнения
    print(f"🚨 ACTION EXECUTED: {action.upper()} | Risk: {alert['risk_level']}")
    if action == "block":
        print("   ✅ Blocked in mock firewall / DB status set to 'suspended'")
    elif action == "flag":
        print("   📌 Flagged for manual review queue")
    else:
        print("   ✅ Allowed, no action needed")

    return alert