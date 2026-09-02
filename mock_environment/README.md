# 🧪 Mock Elasticsearch Ortamı (Sandbox & Test Rehberi)

Bu klasör, gerçek Elasticsearch veritabanına erişim olmadan geliştirme, senaryo testleri ve demolar yapabilmeniz için hazırlanmış **izole test ortamıdır**.

---

## 📁 Klasör İçeriği

* `docker-compose.yml`: Yerel Elasticsearch 8.13.4 kümesini tek komutla ayağa kaldıran Docker yapılandırması.
* `seed_mock_es.py`: Gerçek Penta `product-price` şemasını oluşturan ve zengin B2B teknoloji ürünlerini yükleyen script.
* `kibana_panel.py`: Elasticsearch verilerini ve şemasını tarayıcıda görselleştiren yerel web yönetim paneli (`http://localhost:5601`).

---

## 🚀 Mock Ortamı Nasıl Çalıştırılır?

### 1. Elasticsearch'ü Başlatın (Docker)
```bash
docker compose -f mock_environment/docker-compose.yml up -d
```
*(ES `http://127.0.0.1:9200` adresinde çalışır).*

### 2. Sentetik Verileri Yükleyin
```bash
uv run python mock_environment/seed_mock_es.py
```

### 3. Görsel Yönetim Panelini Açın (Opsiyonel)
```bash
uv run python mock_environment/kibana_panel.py
# Tarayıcıda http://localhost:5601 adresini açın.
```

### 4. Testleri Koşturun
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
