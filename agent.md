# 🤖 B2B Satış Temsilcileri Ürün Arama MCP — Birleşik Teknik Doküman

Bu doküman, Kurum İçi B2B Satış Temsilcilerinin **MS Teams** üzerinden ürün kataloğunda arama yapması, stok ve Dolar/TL fiyatı sorgulaması için geliştirilen MCP sunucusunun birleşik teknik kılavuzudur.

---

## 🎯 Projenin Amacı ve Kapsamı
- **Hedef Kitle:** Kurum içi B2B Satış Temsilcileri ve Müşteri Temsilcileri.
- **Kullanım Kanalı:** Microsoft Teams (Copilot Studio Agent Entegrasyonu).
- **Veri Kaynağı:** Elasticsearch (`product-price` indeksleri).
- **Temel Fonksiyonlar:**
  - Parça Kodu (`producerPartNo`) veya Stok Kodu (`productID`) ile anında arama.
  - Marka, Malzeme Grubu ve Kategori filtreleme.
  - Stok durumu (`totalstock`) ve Depo bazlı stok kontrolleri.
  - Dolar (`productUsdPrice`) ve TL (`productTryPrice`) bazlı fiyat sorgulama.
  - EOL (ömrü bitmiş ürünler) ve Kampanya filtreleri.

---

## 🛠️ Mimari Katmanlar

1. **Giriş ve Yetkilendirme (`mcp_server.py` & `src/security.py`):**
   - `@kapi_gerektirir` decorator'ı (penta-mcp-builder altyapısı).
   - `INDEX_WHITELIST` kontrolü (örn: `product-price`, `product-*`). Wildcard fnmatch desteği mevcut.
   - Maksimum 50 ürün limiti (`MAX_RESULT_LIMIT`).
   - Script sorgu ve injection engeli.

2. **Şema Keşfi (`src/schema_discovery.py`):**
   - `index_semasi_getir` aracı ile indeks mapping'i okunur ve sadeleştirilir.

3. **Sorgu Planlayıcı ve Yapı Taşları (`src/query_planner.py` & `src/query_builder.py`):**
   - Serbest metin aramalarında `searchKey^3`, `producerPartNo^3`, `productID^3`, `name^2` öncelikli `multi_match` oluşturulur.
   - Filtreler `filter` bloğuna konularak ES önbelleklemesinden yararlanılır.

4. **Sonuç Biçimlendirici (`src/result_formatter.py`):**
   - Düz JSON yapısı (`total`, `count`, `items`).
   - Her item nesnesi içinde `satis_ozeti` (`urun_adi`, `part_no`, `marka`, `stok_toplam`, `fiyat_usd`, `fiyat_tl`) ile sunulur.

---

## 🚀 Komutlar ve Testler

```bash
# Kurulum
uv sync --all-extras

# Testler
uv run pytest -q

# Code Style (Ruff)
uv run ruff check .

# Sunucu Başlatma
uv run python mcp_server.py
```
