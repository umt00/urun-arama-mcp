import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()


@dataclass
class Settings:
    """Ortam değişkenlerinden yüklenen uygulama ayarları."""

    # Elasticsearch
    es_url: str = field(default_factory=lambda: os.getenv("ES_URL", "http://127.0.0.1:9200"))
    es_api_key: str = field(default_factory=lambda: os.getenv("ES_API_KEY", ""))
    es_timeout: int = field(default_factory=lambda: int(os.getenv("ES_TIMEOUT", "30")))

    # Güvenlik
    index_whitelist: list[str] = field(
        default_factory=lambda: [s.strip() for s in os.getenv("INDEX_WHITELIST", "").split(",") if s.strip()]
    )
    max_result_limit: int = field(default_factory=lambda: int(os.getenv("MAX_RESULT_LIMIT", "50")))

    # MCP Sunucu
    mcp_host: str = field(default_factory=lambda: os.getenv("MCP_HOST", "0.0.0.0"))
    mcp_port: int = field(default_factory=lambda: int(os.getenv("MCP_PORT", "8000")))


def get_settings() -> Settings:
    """Ortam değişkenlerinden ayarları yükleyip döndürür."""
    return Settings()
