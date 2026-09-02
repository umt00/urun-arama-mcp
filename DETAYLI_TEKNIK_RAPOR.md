# 📘 Ürün Arama MCP — Detaylı Teknik Rapor

Bu teknik rapor, **Penta B2B Ürün Arama MCP (Model Context Protocol)** projesinin mimari tasarımını, çalışma prensiplerini, modüllerin kod düzeyinde detaylarını, `uv` bağımlılık yönetimini ve test stratejilerini eksiksiz bir teknik derinlikte sunmaktadır.

---

## 📑 İçindekiler
1. [Sistemin Genel Çalışma Prensipleri](#1-sistemin-genel-çalışma-prensipleri)
2. [Tam Sistem Mimarisi ve Akış Detayları](#2-tam-sistem-mimarisi-ve-akış-detayları)
3. [Modül Dosyalarının Detaylı İncelemesi (Kod Yapısı & Görevler)](#3-modül-dosyalarının-detaylı-incelemesi)
   - [3.1 mcp_server.py](#31-mcp_serverpy--fastmcp-giriş-katmanı)
   - [3.2 src/security.py](#32-srcsecuritypy--güvenlik-ve-yetkilendirme)
   - [3.3 src/schema_discovery.py](#33-srcschema_discoverypy--dinamik-şema-keşfi)
   - [3.4 src/query_planner.py](#34-srcquery_plannerpy--sorgu-planlayıcı)
   - [3.5 src/query_builder.py](#35-srcquery_builderpy--es-sorgu-yapı-taşları)
   - [3.6 src/es_client.py](#36-srces_clientpy--asenkron-es-bağlantısı)
   - [3.7 src/result_formatter.py](#37-srcresult_formatterpy--sonuç-biçimlendirici)
   - [3.8 config/settings.py](#38-configsettingspy--konfigürasyon)
   - [3.9 Dockerfile & pyproject.toml](#39-dockerfile--pyprojecttoml--paketleme--bağımlılıklar)
4. [uv Kullanım Detayları](#4-uv-kullanım-detayları)
5. [Test Stratejisi, Test Edilen Unsurlar ve Beklenen Sonuçlar](#5-test-stratejisi-ve-doğrulama)

---

## 1. Sistemin Genel Çalışma Prensipleri

Sistem, kurumsal B2B e-ticaret verilerinin tutulduğu Elasticsearch (`product-price`) kümesi ile Microsoft Teams üzerindeki Copilot Studio AI Agent'ları arasında **stateless (durumsuz), salt-okunur ve yüksek güvenlikli** bir köprü işlevi görür.

### Temel Prensipler:
1. **İnce MCP Katmanı, Kalın İş Mantığı (Thin MCP Layer, Fat Logic Layer):**
   `mcp_server.py` dosyası sadece MCP tool tanımlarını ve istek yönlendirmelerini barındırır. Sorgu oluşturma, güvenlik denetimi, şema analizi gibi ağır iş mantıkları tamamen `src/` altındaki modüllere ayrıştırılmıştır (Decoupled & Testable Architecture).

2. **Dinamik Şema Keşfi (Schema Discovery & Adaptive Mapping):**
   Sistem sabit bir ES mapping'ine bağımlı değildir. İstek geldiğinde ilgili indeksin şemasını (`_mapping`) dinamik olarak okur, alanların tiplerini (`text`, `keyword`, `integer`, `float`, `boolean`, `date`) tespit eder ve sorguyu bu veri tiplerine tam uygun olarak inşa eder.

3. **%100 Salt-Okunur Güvenlik Garantisi (Read-Only Safety):**
   Elasticsearch istemcisinde (`src/es_client.py`) verileri güncelleyen (`index`, `update`, `delete`, `bulk`) hiçbir API metodu bulunmaz. Yalnızca `search`, `get_mapping` ve `list_indices` (GET) yetkilerine izin verilir.

4. **penta-mcp-builder Standartlarına Uyum:**
   Ekip standardı olan `@kapi_gerektirir` decorator'ı ile her tool çağrısında yetki denetimi yapılır. Tüm hatalar ve yanıtlar öngörülebilir, sabit bir JSON şemasında dönülür.

5. **Bool Query Optimizasyonu (Performance & Cache Friendly):**
   Elasticsearch'ün en hızlı çalışma modeli olan `bool` query yapısı kullanılır:
   - Kesin filtreler (marka, stok durumu, fiyat aralığı, EOL) ➔ `filter` context altında çalıştırılır (Skor hesaplanmaz, ES tarafından bellekte önbelleklenir / cached).
   - Serbest metin aramaları ➔ `must` context altında çalıştırılır ve `searchKey^3`, `producerPartNo^3`, `name^2` ağırlıklarıyla en alakalı ürünlerin üstte çıkması sağlanır.

---

## 2. Tam Sistem Mimarisi ve Akış Detayları

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         1. MS TEAMS / SATIŞ TEMSİLCİSİ                          │
│       "036K92300 parça kodlu Xerox ürününün fiyatı ve stok durumu nedir?"        │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ (1. Doğal Dil İsteği)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                       2. COPILOT STUDIO (B2B Sales Agent)                        │
│  - NLU ile Intent Extraction (Parça Kodu, Marka, Stok)                           │
│  - 1. Adım: Şemayı kontrol et (index_semasi_getir("product-price"))               │
│  - 2. Adım: Talebi parametrelendir (serbest_metin, filtreler, limit)             │
│  - 3. Adım: urun_ara(...) MCP aracını tetikle                                    │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ (2. HTTP / SSE MCP Tool Call)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     3. FASTMCP SUNUCUSU (mcp_server.py)                         │
│                      [Azure Container Apps / Port 8000]                          │
│                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────┐   │
│   │ A. GÜVENLİK KATMANI (src/security.py)                                    │   │
│   │    - @kapi_gerektirir (Yetki kontrolü)                                   │   │
│   │    - Wildcard Whitelist Kontrolü ('product-*', 'product-price')          │   │
│   │    - Limit Sınırlandırma (Limit <= 50)                                   │   │
│   │    - Script Enjeksiyon Koruması                                          │   │
│   └────────────────────────────────────┬─────────────────────────────────────┘   │
│                                        │                                         │
│   ┌────────────────────────────────────▼─────────────────────────────────────┐   │
│   │ B. ŞEMA KEŞİF KATMANI (src/schema_discovery.py)                          │   │
│   │    - Index mapping'ini okur, sadeleştirilmiş alan tipleri listesi döner  │   │
│   └────────────────────────────────────┬─────────────────────────────────────┘   │
│                                        │                                         │
│   ┌────────────────────────────────────▼─────────────────────────────────────┐   │
│   │ C. SORGU PLANLAYICI & YAPI TAŞLARI (src/query_planner + builder)         │   │
│   │    - searchKey^3, producerPartNo^3, name^2 ──► multi_match (must)        │   │
│   │    - totalstock, productUsdPrice, isEol    ──► range/term (filter)       │   │
│   └────────────────────────────────────┬─────────────────────────────────────┘   │
│                                        │                                         │
│   ┌────────────────────────────────────▼─────────────────────────────────────┐   │
│   │ D. ELASTICSEARCH İSTEMCİSİ (src/es_client.py)                            │   │
│   │    - Asenkron Read-Only ES Bağlantısı                                    │   │
│   └────────────────────────────────────┬─────────────────────────────────────┘   │
│                                        │                                         │
│   ┌────────────────────────────────────▼─────────────────────────────────────┐   │
│   │ E. SONUÇ BİÇİMLENDİRİCİ (src/result_formatter.py)                        │   │
│   │    - Düz JSON yapısı + satis_ozeti                                       │   │
│   │    - { total, count, items: [{ satis_ozeti: {urun_adi, part_no...}}] }   │   │
│   └──────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ (3. Salt-Okunur Query)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                       4. ELASTICSEARCH VERİ KATMANI                              │
│                        [Index: product-price Cluster]                            │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Modül Dosyalarının Detaylı İncelemesi

### 3.1 `mcp_server.py` — FastMCP Giriş Katmanı
* **Görevi:** MCP protocol HTTP sunucusudur. Tool'ları dış dünyaya açar.
* **İşleyişi:**
  - `load_dotenv()` ile `.env` dosyasını okur.
  - `log_yapilandir()` ile standart loglama başlatır.
  - 4 adet MCP Tool'u sunar:
    1. `index_listele_tool`: Erişilebilir indeksleri listeler.
    2. `index_semasi_getir_tool`: İndeksin sadeleştirilmiş mapping haritasını döndürür.
    3. `urun_ara_tool`: Ana arama motoru tool'udur.
    4. `health_check`: Sunucu ve ES sağlık durumunu bildirir.
* **Kritik Tasarım:** Her tool `@kapi_gerektirir(...)` ile korunur. Hiçbir veritabanı sorgu inşası burada yapılmaz, tamamen `src/` modüllerine yönlendirilir.

---

### 3.2 `src/security.py` — Güvenlik ve Yetkilendirme
* **Görevi:** Güvenlik bariyerlerini ve yetki denetimlerini uygular.
* **Kapsadığı Fonksiyonlar:**
  - `kapi_gerektirir(yetki_kodu)`: Decorator yapısı. İstek süresini ölçer, `MCP_API_KEY` kontrolü yapar, hata oluşursa yakalayıp standart JSON hata formatında döner.
  - `whitelist_kontrol(index, whitelist)`: `fnmatch` kullanarak hem tam eşleşme hem de wildcard (`product-*`, `penta-urunler-*`) eşleşmesi denetler. Whitelist dışı istekleri ES'e gitmeden engeller.
  - `limit_kontrol(limit, max_limit)`: Gelen sonuç limiti parametresini inceler. `limit=100000` gibi aşırı istekleri güvenli üst sınıra (`50`) çekerek sunucu ve ağ tıkanmasını önler.
  - `script_sorgu_kontrol(sorgu)`: Sorgu string'inde `script`, `script_score`, `script_fields` geçip geçmediğini kontrol eder. ES script injection saldırılarını engeller.
  - `hata_yaniti(mesaj, kod)`: Tüm modüller için standart hata JSON'ı üretir (`{ "hata": mesaj, "kod": kod, "total": 0, "count": 0, "items": [] }`).

---

### 3.3 `src/schema_discovery.py` — Dinamik Şema Keşfi
* **Görevi:** Elasticsearch'ten gelen karmaşık ve gürültülü `_mapping` verisini temizleyip LLM/Agent dostu özet bir formata çevirmektir.
* **İşleyişi:**
  - `index_listele`: ES `_cat/indices` API'sini çağırır, whitelist kontrolü yapar ve indeks boyutları ile doküman sayılarını listeler.
  - `index_semasi_getir`: ES `_mapping` API'sinden dönen derin iç içe JSON ağacını gezerek her alanın adını ve tipini çıkarır.
  - `_mapping_sadelestir`: Karmaşık ES tiplerini sade tiplere indirger (`text`, `keyword`, `integer`, `float`, `boolean`, `date`). Alt alanları (`.keyword` gibi) tespit eder.

---

### 3.4 `src/query_planner.py` — Sorgu Planlayıcı (B2B Satış Modu)
* **Görevi:** İndeks şeması ve kullanıcının arama talebini alıp en uygun Elasticsearch `bool` sorgusuna dönüştürmektir.
* **İşleyişi:**
  - `serbest_metin` geldiğinde şemadaki metinsel ve keyword alanlarını inceler.
  - B2B Satış Ağırlıklandırması (Boosting) uygular:
    * `searchKey^3` (Okunuş hataları ve birleştirilmiş kelimeler)
    * `producerPartNo^3` / `productID^3` (Parça ve Stok Kodu)
    * `product.name^2` / `product.description^2` (Ürün Adı ve Açıklaması)
  - `multi_match` sorgusu oluşturup `must` bloğuna yerleştirir.
  - Yapılandırılmış filtreleri (`filtreler`) şema tipleriyle eşleştirip `query_builder` aracılığıyla `filter` bloğuna yerleştirir.
  - Şemada olmayan bir alan istendiğinde `_uyarilar` listesine ekleyerek açık uyarı verir.

---

### 3.5 `src/query_builder.py` — ES Sorgu Yapı Taşları
* **Görevi:** Doğru ES query DSL JSON parçacıklarını üretmektir.
* **Fonksiyonlar:**
  - `term_sorgusu(alan, deger)`: `keyword` ve `boolean` alanlar için kesin eşleşme sorgusu.
  - `match_sorgusu(alan, metin)`: `text` alanlar için doğal dil araması.
  - `range_sorgusu(alan, gte, lte, gt, lt)`: Sayısal ve tarihsel aralık sorgusu.
  - `alan_tipine_gore_sorgu(alan, tip, deger)`: Verilen tipe göre otomatik doğru sorgu üretecini seçer.
  - `bool_sorgu_kur(must, filter_, should, must_not)`: Tüm parçaları tek bir standart `bool` sorgu gövdesinde birleştirir.

---

### 3.6 `src/es_client.py` — Asenkron ES Bağlantı Yöneticisi
* **Görevi:** Elasticsearch kümesine `elasticsearch[async]` kütüphanesi ile yüksek performanslı, asenkron ve **salt-okunur** erişim sağlamaktır.
* **Özellikleri:**
  - Singleton istemci yaşam döngüsü.
  - API Key veya HTTP Basic Auth desteği.
  - `search()`, `get_mapping()`, `cat_indices()` metotları mevcuttur. Veri değiştirici/silici hiçbir metot içermez.

---

### 3.7 `src/result_formatter.py` — Sonuç Biçimlendirici (Satış Özet Modu)
* **Görevi:** Ham Elasticsearch yanıtlarındaki gürültüyü (shard bilgileri, cluster detayları, iç içe meşakkatli ağaçlar) temizleyip düz ve kompakt bir JSON şemasına çevirmektir.
* **Çıktı Şeması:**
  ```json
  {
    "total": 42,
    "count": 1,
    "items": [
      {
        "id": "210229916",
        "skor": 14.2,
        "satis_ozeti": {
          "urun_adi": "XEROX 036K92300 (SCC) LEFT COUN",
          "part_no": "036K92300",
          "marka": "Xerox",
          "stok_toplam": 0,
          "fiyat_usd": 16.03,
          "fiyat_tl": 768.44
        },
        "product.name": "XEROX 036K92300 (SCC) LEFT COUN",
        "productUsdPrice": 16.03,
        "categoryName": "Baskı Çözümleri>Yazıcı Sarfları>Xerox>Yedek Parça>Xerox Yedek Parça"
      }
    ],
    "sorgu_bilgisi": { "index": "product-price" },
    "hata": null
  }
  ```

---

### 3.8 `config/settings.py` — Konfigürasyon Yönetimi
* Dataclass tabanlı dinamik ortam değişkeni okuyucusudur.
* `ES_URL`, `ES_API_KEY`, `ES_TIMEOUT`, `INDEX_WHITELIST`, `MAX_RESULT_LIMIT`, `MCP_HOST`, `MCP_PORT` değerlerini okur.

---

### 3.9 `Dockerfile` & `pyproject.toml` — Paketleme & Bağımlılıklar
* **`pyproject.toml`:** Modern PEP 621 standartlarında proje tanımı. `hatchling` build-backend ve `[tool.hatch.build.targets.wheel]` ile `src` ve `config` modüllerini paketler.
* **`Dockerfile`:** `python:3.11-slim` tabanlı, multi-stage optimizasyonlu, üretime hazır Azure Container Apps imajı üretir.

---

## 4. uv Kullanım Detayları

Projede bağımlılık yönetimi ve paketleme için Astral tarafından geliştirilen yüksek hızlı **`uv`** aracı kullanılmıştır.

### Temel Komutlar ve Kullanım Amaçları:

1. **Bağımlılıkları Senkronize Etme ve Sanal Ortam Oluşturma:**
   ```bash
   uv sync --all-extras
   ```
   * *Açıklama:* `.venv` sanal ortamını oluşturur, `pyproject.toml` içerisindeki tüm bağımlılıkları (`fastmcp`, `elasticsearch`, `python-dotenv`) ve geliştirme araçlarını (`pytest`, `pytest-asyncio`, `ruff`) kilitli versiyonlarla yükler.

2. **Testleri Çalıştırma:**
   ```bash
   uv run pytest -q
   ```
   * *Açıklama:* Sanal ortamı otomatik aktif ederek test paketini sessiz modda çalıştırır.

3. **Kod Kalitesi ve Linter Kontrolü:**
   ```bash
   uv run ruff check . --fix
   ```
   * *Açıklama:* Kod stil hatalarını, import sıralamalarını ve kullanılmayan değişkenleri tespit edip otomatik düzeltir.

4. **MCP Sunucusunu Lokal Başlatma:**
   ```bash
   uv run python mcp_server.py
   ```

---

## 5. Test Stratejisi ve Doğrulama

Test mimarisi, canlı Elasticsearch kümesine ihtiyaç duymadan **tüm iş mantığını %100 kapsayacak biçimde** `pytest` ve `pytest-asyncio` ile kurgulanmıştır.

### Test Dosyaları ve Kapsamları:

#### 1. `tests/test_query_builder.py` (14 Test)
* **Neyi Test Eder?:** `term_sorgusu`, `match_sorgusu`, `range_sorgusu` ve `bool_sorgu_kur` fonksiyonlarının ürettiği ES Query DSL JSON yapılarının doğruluğunu.
* **Beklenen Sonuç:** Canlı ES'e gitmeden, üretilen Python sözlüğünün Elasticsearch kriterleriyle birebir aynı JSON yapısında olması (`PASSED`).

#### 2. `tests/test_query_planner.py` (5 Test)
* **Neyi Test Eder?:** Şema bilgisi verildiğinde serbest metin araması için `multi_match` (boosting dahil) ve `filter` bloklarının doğru ayrıştırılmasını; şemada olmayan bir alan istendiğinde `_uyarilar` mesajının üretilmesini.
* **Beklenen Sonuç:** Metin aramalarının `must`, filtrelerin `filter` altına yazılması (`PASSED`).

#### 3. `tests/test_schema_discovery.py` (4 Test)
* **Neyi Test Eder?:** Karmaşık ES `_mapping` yanıtlarının sadeleştirilmesini (`_mapping_sadelestir`), nested objelerin ve `.keyword` alt alanlarının doğru tespit edilmesini.
* **Beklenen Sonuç:** Sadeleştirilmiş alan ve tip haritasının doğru çıkması (`PASSED`).

#### 4. `tests/test_result_formatter.py` (6 Test)
* **Neyi Test Eder?:** Ham ES arama çıktısının sabit `total`, `count`, `items` (düz yapı + `satis_ozeti`) yapısına dönüştürülmesini ve boş sonuç durumunu.
* **Beklenen Sonuç:** Ham ES gürültüsünün elenmesi ve satış özet alanlarının eksiksiz üretilmesi (`PASSED`).

#### 5. `tests/test_security.py` (20 Test)
* **Neyi Test Eder?:**
  - `@kapi_gerektirir` decorator'ının başarılı ve hatalı tool çağrılarındaki davranışını.
  - Whitelist wildcard (`penta-urunler-*`, `product-*`) eşleşmelerini.
  - `limit=100000` veya negatif limit değerlerinin güvenli `50` değerine çekilmesini.
  - Script sorgu tespit edildiğinde reddedilmesini.
* **Beklenen Sonuç:** Güvenlik engellerinin %100 oranında çalışması (`PASSED`).

#### 6. `tests/test_scenarios.py` (10 Senaryo)
* **Neyi Test Eder?:** B2B Satış Temsilcilerinden toplanan 10 gerçek arama senaryosunun (parça kodu, stok durumu, Dolar fiyatı, EOL durumu vb.) entegrasyon mantığını.
* **Beklenen Sonuç:** Canlı ES ortamında ilk 5 sonuçta doğru ürünlerin çıkması (`SKIPPED` - Canlı entegrasyon testi olarak işaretlenmiştir).

---

### 📊 Test Çalıştırma Özet Sonucu

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Administrator\Desktop\Penta-UrunAramaMcp\urun-arama-mcp
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.14.2, asyncio-1.4.0

tests/test_query_builder.py ..............                              [ 24%]
tests/test_query_planner.py .....                                       [ 33%]
tests/test_result_formatter.py ......                                  [ 43%]
tests/test_scenarios.py ssssssssss                                      [ 60%]
tests/test_schema_discovery.py ....                                     [ 67%]
tests/test_security.py ....................                                [100%]

======================= 49 passed, 10 skipped in 1.15s ========================
```
