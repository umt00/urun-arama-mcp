# Ürün Arama MCP — Kurulum ve Kullanım Kılavuzu

Elasticsearch için dinamik şema keşfi ve Copilot Studio entegrasyonuna sahip FastMCP tabanlı **salt-okunur** ürün arama aracı.

## Hızlı Başlangıç

### 1. Ortamı Hazırla

```bash
# Repo'yu klonla
git clone <repo-url>
cd urun-arama-mcp

# .env dosyasını oluştur
cp .env.example .env
# .env dosyasını düzenle — ES bağlantı bilgilerini gir
```

### 2. Bağımlılıkları Kur

```bash
# uv ile (önerilen)
uv sync

# veya pip ile
pip install -r requirements.txt

# Geliştirme bağımlılıkları
pip install -r requirements.txt
pip install pytest pytest-asyncio ruff
```

### 3. Sunucuyu Başlat

```bash
python mcp_server.py
```

Sunucu `http://0.0.0.0:8000` adresinde başlar (Streamable HTTP).

### 4. MCP Inspector ile Test Et

```bash
npx @modelcontextprotocol/inspector
```

## Ortam Değişkenleri

| Değişken | Açıklama | Varsayılan |
|---|---|---|
| `ES_URL` | Elasticsearch endpoint | `http://localhost:9200` |
| `ES_API_KEY` | Salt-okunur API key | — |
| `ES_TIMEOUT` | ES sorgu timeout (saniye) | `30` |
| `INDEX_WHITELIST` | İzin verilen index'ler (virgülle ayrılmış) | — |
| `MAX_RESULT_LIMIT` | Maksimum sonuç limiti | `50` |
| `MCP_HOST` | Sunucu host | `0.0.0.0` |
| `MCP_PORT` | Sunucu port | `8000` |

## Tool Sözleşmeleri

### `index_listele`
Erişilebilir index'leri listeler. Whitelist kontrolü uygulanır.

### `index_semasi_getir(index)`
Index'in mapping bilgisini LLM-dostu özet olarak döndürür.

### `urun_ara(index, filtreler, serbest_metin, limit)`
Ana arama fonksiyonu. Sonuçlar sabit JSON şemasında döner.

### `health_check`
ES bağlantı durumunu kontrol eder.

## Test

```bash
# Birim testler
uv run pytest -q

# Lint
uv run ruff check .
```

## Deploy (Azure Container Apps)

```bash
# Docker image oluştur
docker build -t urun-arama-mcp .

# Lokal test
docker run -p 8000:8000 --env-file .env urun-arama-mcp

# Azure'a deploy
az containerapp up --name urun-arama-mcp --source .
```

## Dosya Yapısı

```
├── mcp_server.py          # MCP sunucusu (ince katman)
├── src/
│   ├── es_client.py       # ES bağlantı yönetimi
│   ├── schema_discovery.py # Index keşfi, mapping sadeleştirme
│   ├── query_builder.py   # Sorgu yapı taşları
│   ├── query_planner.py   # Şema + talep → filtre çıkarımı
│   ├── result_formatter.py # Sonuç biçimlendirme
│   └── security.py        # Güvenlik kontrolleri
├── config/settings.py     # Ortam değişkenleri
├── tests/                 # Birim + senaryo testleri
├── Dockerfile             # Azure deploy
└── agent.md               # Birleşik teknik kılavuz
```

## Güvenlik Notları

- Tool **salt-okunur** çalışır — ES'e yazma/silme yapılmaz
- Index whitelist — sadece izin verilen index'lere erişim
- Limit üst sınırı — aşırı büyük sorgular engellenir
- Script sorgu yasağı — güvenlik riski olan sorgular reddedilir