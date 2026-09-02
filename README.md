# 🏢 Kurumsal B2B Ürün Arama MCP (MS Teams & Copilot Studio Bot Altyapısı)

Penta Teknoloji B2B e-ticaret altyapısı ve kurumsal Elasticsearch (`product-price` vb.) kataloğu için tasarlanmış **FastMCP tabanlı salt-okunur arama sunucusu**. 

Satış temsilcilerinin **Microsoft Teams** üzerinden ürün parça kodu, stok durumu, Dolar/TL fiyatları ve malzeme gruplarını anında sorgulamalarını ve müşterilerine hızlı dönüş yapmalarını sağlar.

---

## 📑 İçindekiler
- [B2B Satış Temsilcisi Kullanım Senaryoları](#-b2b-sat-temsilcisi-kullan-m-senaryolar)
- [Sistem Mimarisi ve Akışı](#-sistem-mimarisi-ve-ak-)
- [Elasticsearch Veri Yapısı ve Haritalama](#-elasticsearch-veri-yap-s-ve-haritalama)
- [Hızlı Başlangıç (uv)](#-h-zl-ba-lang-)
- [Ortam Değişkenleri (.env)](#-ortam-de-i-kenleri-env)
- [Testler ve Doğrulama](#-testler-ve-do-rulama)

---

## 💼 B2B Satış Temsilcisi Kullanım Senaryoları

Satış ekibi MS Teams botu üzerinden doğal dille sorgu yaptığında arka planda şu alanlar otomatik haritalanır:

| Kullanıcı Sorgu Örneği | Haritalanan ES Alanları ve Filtreleri |
|---|---|
| *"036K92300 kodlu ürün var mı?"* | `serbest_metin: "036K92300"` ➔ `producerPartNo` & `searchKey^3` |
| *"Stokta olan Xerox sarfları"* | `product.exMaterialGroupValue: "Xerox"`, `product.totalstock: {gt: 0}` |
| *"50 USD altındaki yedek parçalar"* | `productUsdPrice: {lte: 50}`, `categoryLevel4Name: "Yedek Parça"` |
| *"Zeroks drum kartuş"* | `serbest_metin: "zeroks drum"` ➔ `searchKey^3` (okunuş/yazım toleransı) |
| *"210229916 stok kodu kaç para?"* | `serbest_metin: "210229916"` ➔ `productID` & `searchKey` |

---

## 🏗️ Sistem Mimarisi ve Akışı

```
[ 1. MS TEAMS / SATIŞ TEMSİLCİSİ ]
   │  "036K92300 parça kodlu Xerox ürününün fiyat ve stok durumu nedir?"
   ▼
[ 2. COPILOT STUDIO (B2B Sales Agent) ]
   │  1. Adım: Şemayı kontrol eder (index_semasi_getir)
   │  2. Adım: Satış temsilcisi talebini parametrelendirir:
   │     { serbest_metin: "036K92300", filtreler: { "product.exMaterialGroupValue": "Xerox" } }
   │  3. Adım: urun_ara(...) aracını tetikler
   ▼
[ 3. FASTMCP GÜVENLİK SÜZGECİ (penta-mcp-builder) ]
   │  • @kapi_gerektirir (Yetkilendirme denetimi)
   │  • Index Whitelist kontrolü (örn. 'product-*', 'penta-urunler-*')
   │  • Limit sınırı (Maks. 50 ürün)
   │  • Script sorgu ve injection engeli
   ▼
[ 4. DİNAMİK SORGU İNŞASI (Query Planner & Builder) ]
   │  • searchKey^3, producerPartNo^3, name^2 ──► multi_match (must context)
   │  • product.totalstock, productUsdPrice  ──► range / term (filter context)
   ▼
[ 5. ELASTICSEARCH (Salt-Okunur Cluster) ]
   │  • Read-only API Key ile sorgulama
   ▼
[ 6. SONUÇ BİÇİMLENDİRME (Satış Özet Yapısı) ]
   │  • Düz JSON yapısı + satis_ozeti (urun_adi, part_no, stok_toplam, fiyat_usd, fiyat_tl)
   ▼
[ 7. COPILOT STUDIO & TEAMS KARTI (Adaptive Card) ]
      Satış Temsilcisine Anında Görsel Kart Sunulur:
      ┌────────────────────────────────────────────────────────┐
      │  💻 XEROX 036K92300 (SCC) LEFT COUN                    │
      │  • Parça Kodu: 036K92300 | Ürün Kodu: 210229916         │
      │  • Marka: Xerox | Kategori: Baskı Çözümleri>Yazıcı...  │
      │  • Fiyat: 16.03 USD / 768.44 TL                        │
      │  • Stok Durumu: 0 Adet (Depo: Ticari Mrkz Depo)       │
      └────────────────────────────────────────────────────────┘
```

---

## 🛠️ Hızlı Başlangıç

### 1. Kurulum (`uv` ile)
```bash
# Bağımlılıkları ve sanal ortamı yükle
uv sync --all-extras
```

### 2. Ortam Değişkenleri (.env)
```env
ES_URL=http://localhost:9200
ES_API_KEY=your-read-only-api-key
INDEX_WHITELIST=product-price,product-*
MAX_RESULT_LIMIT=50
MCP_HOST=0.0.0.0
MCP_PORT=8000
```

### 3. Sunucuyu Başlatma
```bash
uv run python mcp_server.py
```

---

## 🧪 Testler ve Doğrulama

```bash
# Birim testleri ve güvenlik denetimlerini çalıştır
uv run pytest -q

# Kod stili ve standartları kontrol et (ruff)
uv run ruff check .
```
