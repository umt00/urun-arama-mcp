FROM python:3.11-slim

WORKDIR /app

# Bağımlılıkları önce kopyala (Docker cache optimizasyonu)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Ortam değişkenleri
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

# Sağlık kontrolü
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

CMD ["python", "mcp_server.py"]
