# 🧪 Mock Elasticsearch Ortamı (Sandbox & Test Rehberi)

Bu klasör, gerçek Elasticsearch veritabanına erişim olmadan geliştirme, senaryo testleri ve demolar yapabilmeniz için hazırlanmış **izole test ortamıdır**.

---

## 📁 Klasör İçeriği

* `docker-compose.yml`: Yerel Elasticsearch 8.13.4 kümesini tek komutla ayağa kaldıran Docker yapılandırması.
* `seed_mock_es.py`: Gerçek Penta `product-price` şemasını oluşturan ve 7 adet zengin B2B teknoloji ürününü yükleyen script.

---

## 🚀 Mock Ortamı Nasıl Çalıştırılır?

### 1. Elasticsearch'ü Başlatın (Docker)
```bash
# Bu klasör içindeyken:
docker compose up -d
```
*(ES `http://127.0.0.1:9200` adresinde çalışır).*

### 2. Sentetik Verileri Yükleyin
```bash
uv run python mock_environment/seed_mock_es.py
```

### 3. Testleri Koşturun
```bash
uv run pytest -v
```

---

## 🔄 Canlıya (Production) Geçerken Yapılması Gerekenler

Proje kodlarında **HİÇBİR DEĞİŞİKLİK YAPILMAZ**. Bu klasör tamamen izole bir test ortamıdır.

Canlıya geçerken yapılması gereken **tek işlem**, ana dizindeki `.env` dosyasını gerçek ES bilgileriyle güncellemektir:

```env
# ── ESKİ (Mock Ortamı) ─────────────────────────
# ES_URL=http://127.0.0.1:9200
# ES_API_KEY=

# ── YENİ (Canlı Kurumsal ES) ───────────────────
ES_URL=https://canli-penta-es.kurum.com:9200
ES_API_KEY=gercek_salt_okunur_api_key
INDEX_WHITELIST=product-price
```
