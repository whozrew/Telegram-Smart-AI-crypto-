"""Utils package."""
from utils.i18n import t, detect_language
from utils.http_client import fetch_html, fetch_json

__all__ = ["t", "detect_language", "fetch_html", "fetch_json"]
