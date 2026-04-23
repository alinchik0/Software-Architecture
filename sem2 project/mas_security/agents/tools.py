from langchain_core.tools import tool
import re

@tool
def detect_patterns(text: str) -> str:
    """Scans text for repeated failure markers, suspicious IPs, or urgency phrases."""
    patterns = {
        "brute_force": re.findall(r'(?:failed|attempt|login)\s*\d+', text, re.IGNORECASE),
        "urgency": re.findall(r'(?:urgent|immediately|verify|deleted)', text, re.IGNORECASE),
        "ip_trace": re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', text)
    }
    active = [k for k, v in patterns.items() if v]
    return f"DETECTED: {', '.join(active) if active else 'none'}"

@tool
def check_links(text: str) -> str:
    """Extracts and flags shortened or suspicious domains."""
    urls = re.findall(r'https?://\S+', text)
    flagged = [u for u in urls if any(k in u for k in ["bit.ly", "tinyurl", "login-", "verify-"])]
    return f"SUSPICIOUS: {flagged}" if flagged else "CLEAN"