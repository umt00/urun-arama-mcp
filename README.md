# 🔍 Ürün Arama MCP (Product Search MCP Server)

[![CI](https://github.com/umt00/urun-arama-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/umt00/urun-arama-mcp/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/protocol-FastMCP%202.0-brightgreen.svg)](https://github.com/jlowin/fastmcp)
[![Tests](https://img.shields.io/badge/tests-59%20passed-success.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Elasticsearch üzerinde **dinamik şema keşfi** ve **kurumsal güvenlik denetimleri** sunan, **FastMCP** tabanlı, salt-okunur B2B ürün ve stok arama sunucusu. 

Microsoft Copilot Studio (Teams), Claude Desktop, Cursor ve tüm MCP uyumlu istemciler ile doğrudan entegre çalışır.

---

## ✨ Temel Özellikler

- **🔒 Kurumsal Güvenlik Standartları:**
  - Salt-okunur (read-only) veri erişimi; yazma/silme operasyonları kesinlikle engellenir.
  - İndeks Whitelist (`INDEX_WHITELIST`) ve wildcard deseni desteği (`product-*`).
  - Maksimum sonuç sınırı (`MAX_RESULT_LIMIT`) ile DoS ve bellek patlaması koruması.
  - Kod/script enjeksiyonuna karşı özyinelemeli `script` filtresi denetimi.
  - `@kapi_gerektirir` API anahtarı doğrulaması (`MCP_API_KEY`).
- **🧠 Dinamik Şema Keşfi (`Schema Discovery`):**
  - İndeks haritalamalarını (mapping) otomatik okur, LLM dostu özet şemaya dönüştürür.
  - Çok katmanlı iç içe (`nested`) alanları otomatik olarak nokta notasyonuyla (`product.productID`) düzleştirir.
- **⚡ Akıllı Sorgu Planlama (`Query Planner`):**
  - LLM'den gelen serbest metin veya yapısal istekleri `searchKey^3`, `producerPartNo^3`, `productID^3`, `name^2` ağırlıklı optimize `multi_match` ve `filter` bloklarına çevirir.
  - Elasticsearch filtre önbelleklemesinden maksimum verim alır.
- **🌐 Çift Protokol & Entegrasyon Uyumluğu:**
  - FastMCP Streamable HTTP (`/mcp`) protokolü.
  - Copilot Studio / eski istemciler için `/` ve `/sse` yönlendirmeleri (`307 Redirect`).
- **🎛️ Entegre Komuta Merkezi (`main.py`):**
  - Docker Elasticsearch, Kibana, MCP Sunucusu ve Cloudflare Tünelini tek arayüzden yönetme.
- **🧪 İzole Mock Ortamı:**
  - Gerçekçi B2B teknoloji ürün şeması (`mock_environment/`), sentetik veri yükleyici ve hafif Kibana alternatifi Web UI.

---

## 🏛️ Mimari

```
┌────────────────────────────────────────────────────────┐
│  İstemciler: MS Teams / Copilot Studio / Claude / Cursor│
└───────────────────────────┬────────────────────────────┘
                            │ Streamable HTTP (Port 8008)
                            ▼
┌────────────────────────────────────────────────────────┐
│               mcp_server.py (İnce Katman)              │
│      - Yetkilendirme & Güvenlik Kalkanı (@kapi_...)     │
│      - Tool Tanımları & HTTP Yönlendirmeleri           │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────────┐ ┌──────────────────────┐
│  src/schema_discovery.py     │ │ src/query_planner.py │
│  - Otomatik Şema Haritalama  │ │ src/query_builder.py │
│  - Nested Alan Çıkarımı      │ │ - Akıllı Filtreleme  │
└──────────────┬───────────────┘ └──────────┬───────────┘
               │                            │
               └──────────────┬─────────────┘
                              ▼
┌────────────────────────────────────────────────────────┐
│                  src/es_client.py                      │
│            Elasticsearch (Async Client)                │
└─────────────────────────────┬──────────────────────────┘
                              ▼
┌────────────────────────────────────────────────────────┐
│                Elasticsearch Kümesi                     │
│               Index: product-price                     │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Hızlı Başlangıç

### 1. Depoyu Klonlayın ve Ortam Dosyasını Hazırlayın

```bash
git clone https://github.com/umt00/urun-arama-mcp.git
cd urun-arama-mcp

# Örnek ortam dosyasını kopyalayın
cp .env.example .env
```

`.env` dosyasını ihtiyacınıza göre düzenleyin (varsayılanlar mock ortamı için hazırdır):
```env
ES_URL=http://127.0.0.1:9200
INDEX_WHITELIST=product-price,product-*
MAX_RESULT_LIMIT=50
MCP_PORT=8008
```

### 2. Bağımlılıkları Yükleyin

Önerilen paket yöneticisi **uv**'dir:

```bash
# uv ile (Önerilen)
uv sync --all-extras

# veya standart pip ile
pip install -r requirements.txt
pip install pytest pytest-asyncio ruff
```

### 3. Komuta Merkezi ile Tek Komutta Başlatın (En Kolay Yol)

```bash
python main.py
```

İnteraktif menüden seçim yapabilir veya doğrudan komutları kullanabilirsiniz:

```bash
python main.py start    # Docker ES, MCP sunucu ve tüneli başlatır
python main.py status   # Canlı servis durumlarını gösterir
python main.py seed     # Sentetik mock ürün verilerini yükler
python main.py stop     # Tüm servisleri temiz bir şekilde kapatır
```

### 4. Veya Bağımsız Olarak MCP Sunucusunu Başlatın

```bash
uv run python mcp_server.py
```

Sunucu `http://0.0.0.0:8008` adresinde çalışmaya başlar.

---

## 🛠️ MCP Tool Sözleşmeleri

Sunucu 4 temel MCP aracını dışa aktarır:

### 1. `urun_ara`
Ürün kataloğunda serbest metin veya yapısal filtreler ile arama yapar.

* **Parametreler:**
  - `index` *(str)*: Arama yapılacak Elasticsearch indeksi (varsayılan: `product-price`).
  - `filtreler` *(dict, opsiyonel)*: Alan bazlı tam eşleşme filtreleri (örn: `{"brand": "Dell", "isCampaign": True}`).
  - `serbest_metin` *(str, opsiyonel)*: Kullanıcının doğal dil sorgusu (örn: `"i7 16gb laptop"`).
  - `limit` *(int, opsiyonel)*: Döndürülecek maksimum kayıt sayısı (varsayılan: `10`, maks: `50`).
* **Dönüş Formatı:**
  ```json
  {
    "total": 42,
    "count": 1,
    "items": [
      {
        "satis_ozeti": {
          "urun_adi": "Dell Latitude 5540",
          "part_no": "N004L554015EMEA_U",
          "marka": "Dell",
          "stok_toplam": 14
        },
        "detay": { ... }
      }
    ]
  }
  ```

### 2. `index_listele`
Sistemde izin verilen (`INDEX_WHITELIST`) ve erişilebilir durumdaki indeksleri listeler.

### 3. `index_semasi_getir`
Belirtilen indeksin veri haritalamasını (mapping) okur, çok katmanlı alanları sadeleştirip LLM'in doğru filtreler üretebilmesi için optimize edilmiş şema olarak döndürür.

### 4. `health_check`
Elasticsearch kümesinin erişilebilirliğini, bağlantı gecikmesini ve küme durumunu doğrular.

---

## 🧪 Test ve Kod Kalitesi

Proje kapsamlı birim ve senaryo test paketine sahiptir:

```bash
# Tüm testleri koştur (59 test)
uv run pytest -v

# Kod stili ve linter denetimi
uv run ruff check .

# Otomatik formatlama kontrolü
uv run ruff format --check .
```

---

## 🐳 Docker ile Dağıtım

### Docker ile Çalıştırma

```bash
# Docker imajı oluşturma
docker build -t urun-arama-mcp .

# Konteyneri başlatma
docker run -d \
  -p 8008:8008 \
  --env-file .env \
  --name urun-arama-mcp-server \
  urun-arama-mcp
```

### Azure Container Apps Dağıtımı

```bash
az containerapp up \
  --name urun-arama-mcp \
  --source . \
  --ingress external \
  --target-port 8008
```

---

## ⚙️ Ortam Değişkenleri Referansı

| Değişken | Açıklama | Varsayılan | Zorunlu mu? |
|---|---|---|:---:|
| `ES_URL` | Elasticsearch bağlantı adresi | `http://127.0.0.1:9200` | Hayır |
| `ES_API_KEY` | Salt-okunur Elasticsearch API Anahtarı | *(boş)* | Canlıda Evet |
| `ES_TIMEOUT` | Elasticsearch sorgu zaman aşımı (saniye) | `30` | Hayır |
| `INDEX_WHITELIST` | İzin verilen indeksler (virgülle ayrılmış) | `product-price,product-*` | Hayır |
| `MAX_RESULT_LIMIT` | Tek sorguda çekilebilecek azami ürün adedi | `50` | Hayır |
| `MCP_API_KEY` | Sunucu erişim yetkilendirme anahtarı | *(boş - dev mod)* | Canlıda Önerilir |
| `MCP_HOST` | MCP dinleme IP adresi | `0.0.0.0` | Hayır |
| `MCP_PORT` | MCP dinleme portu | `8008` | Hayır |

---

## 📂 Dizin Yapısı

```
├── .github/workflows/ci.yml # GitHub Actions CI (Test & Lint)
├── config/
│   └── settings.py          # Yapılandırma ve ortam değişkenleri
├── mock_environment/        # İzole test & sandbox ortamı
│   ├── docker-compose.yml   # Yerel Elasticsearch konteyneri
│   ├── seed_mock_es.py      # Sentetik kurumsal ürün yükleyici
│   └── kibana_panel.py      # Görsel ES gözetim web paneli
├── src/
│   ├── es_client.py         # Async Elasticsearch istemcisi
│   ├── query_builder.py     # ES sorgu bileşenleri
│   ├── query_planner.py     # Akıllı filtre & sorgu planlayıcı
│   ├── result_formatter.py  # Standartlaştırılmış yanıt biçimlendirici
│   ├── schema_discovery.py  # Dinamik şema keşfi & nested çözümleme
│   └── security.py          # Güvenlik, doğrulama, API key kalkanı
├── tests/                   # 59 birim ve senaryo testi
├── Dockerfile               # Çok aşamalı optimize Dockerfile
├── LICENSE                  # MIT Lisansı
├── main.py                  # Komuta Merkezi CLI
├── mcp_server.py            # FastMCP sunucu giriş noktası
├── pyproject.toml           # Proje metadata & bağımlılıkları
└── requirements.txt         # Standart pip bağımlılıkları
```

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında lisanslanmıştır.