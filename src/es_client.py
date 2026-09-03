# Ürün Arama MCP — Elasticsearch İstemci Yönetimi

"""
Elasticsearch bağlantı yönetimi.

Bu modül ES cluster'ına salt-okunur bağlantı kurar ve yönetir.
Tüm ES erişimleri bu modül üzerinden geçer.
"""

import os

from elasticsearch import AsyncElasticsearch

from config.settings import Settings

# Windows localhost proxy atlatma
os.environ["NO_PROXY"] = "localhost,127.0.0.1"


class ESClient:
    """Elasticsearch bağlantı yöneticisi — salt-okunur."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncElasticsearch | None = None

    async def get_client(self) -> AsyncElasticsearch:
        """Lazy-init ile ES istemcisini döndürür."""
        if self._client is None:
            kwargs: dict = {
                "hosts": [self._settings.es_url],
                "request_timeout": self._settings.es_timeout,
            }
            if self._settings.es_api_key:
                kwargs["api_key"] = self._settings.es_api_key
            self._client = AsyncElasticsearch(**kwargs)
        return self._client

    async def close(self) -> None:
        """Bağlantıyı kapatır."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    # ── Salt-okunur ES işlemleri ──────────────────────────────────

    async def list_indices(self) -> list[dict]:
        """Tüm index'leri listeler (_cat/indices)."""
        client = await self.get_client()
        result = await client.cat.indices(format="json")
        return result  # type: ignore[return-value]

    async def get_mapping(self, index: str) -> dict:
        """Belirtilen index'in mapping bilgisini döndürür."""
        client = await self.get_client()
        result = await client.indices.get_mapping(index=index)
        return result  # type: ignore[return-value]

    async def search(self, index: str, body: dict, size: int = 10) -> dict:
        """ES arama sorgusu çalıştırır.

        elasticsearch-py 8.x uyumlu: body parametresini ayrıştırarak
        keyword arguments olarak geçer (deprecation uyarısını önler).
        """
        client = await self.get_client()
        # body dict'inden query ve diğer üst seviye anahtarları ayır
        query = body.get("query")
        kwargs: dict = {"index": index, "size": size}
        if query is not None:
            kwargs["query"] = query
        # Diğer body parametrelerini de destekle (sort, _source, aggs vb.)
        for key in ("sort", "_source", "aggs", "aggregations", "highlight", "post_filter"):
            if key in body:
                kwargs[key] = body[key]
        result = await client.search(**kwargs)
        return result  # type: ignore[return-value]
