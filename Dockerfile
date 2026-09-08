FROM python:3.11-slim

WORKDIR /app

# uv'yi resmi imajdan kopyala
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Önce bağımlılık dosyalarını kopyalayarak cache avantajı sağla
COPY pyproject.toml uv.lock ./

# Sadece bağımlılıkları kur (uygulama kodunu henüz kopyalamadan)
RUN uv sync --frozen --no-dev --no-install-project

# Tüm uygulama kodunu kopyala
COPY . .

# Projenin kendisini çalışma ortamına kur
RUN uv sync --frozen --no-dev

# Oluşturulan sanal ortamı (.venv) PATH'e ekle
ENV PATH="/app/.venv/bin:$PATH"

# Ortam değişkenleri
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8008

# Sağlık kontrolü — FastMCP SSE endpointine istek atar
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8008/sse')" || exit 1

EXPOSE 8008

CMD ["python", "mcp_server.py"]
