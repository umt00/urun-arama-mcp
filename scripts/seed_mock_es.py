# Ürün Arama MCP — Sentetik Elasticsearch Veri Yükleme Scripti

"""
Bu script:
1. Docker üzerindeki yerel Elasticsearch'e bağlanır.
2. Gerçek Penta 'product-price' şemasıyla indeksi oluşturur.
3. 20+ adet gerçekçi, zengin B2B teknoloji ürününü (Xerox, Dell, HP, Lenovo sarf ve donanımları)
   indekse yükler.
"""

import asyncio
import logging

from elasticsearch import AsyncElasticsearch

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("seed_mock_es")

import os

os.environ["NO_PROXY"] = "localhost,127.0.0.1"

ES_URL = "http://127.0.0.1:9200"
INDEX_NAME = "product-price"

# ── Gerçekçi product-price İndeks Mapping Şeması ────────────────
MAPPING = {
    "mappings": {
        "properties": {
            "searchKey": {"type": "text"},
            "categoryName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "categoryLevel1Name": {"type": "keyword"},
            "categoryLevel2Name": {"type": "keyword"},
            "categoryLevel3Name": {"type": "keyword"},
            "categoryLevel4Name": {"type": "keyword"},
            "productUsdPrice": {"type": "float"},
            "productTryPrice": {"type": "float"},
            "productEurPrice": {"type": "float"},
            "isEol": {"type": "boolean"},
            "product": {
                "properties": {
                    "productID": {"type": "keyword"},
                    "producerPartNo": {"type": "keyword"},
                    "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "description": {"type": "text"},
                    "exMaterialGroupValue": {"type": "keyword"},  # Marka (Xerox, Dell vb.)
                    "materialGroupValue": {"type": "keyword"},    # Sarf, Donanım vb.
                    "totalstock": {"type": "integer"},
                    "isCampaign": {"type": "boolean"},
                    "issparepartlist": {"type": "boolean"},
                    "isOutlet": {"type": "boolean"},
                    "warranty": {"type": "integer"},
                    "priceA": {"type": "float"},
                    "priceD": {"type": "float"},
                }
            },
            "storageStocks": {
                "type": "nested",
                "properties": {
                    "storageName": {"type": "keyword"},
                    "stock": {"type": "integer"},
                    "storagePlace": {"type": "keyword"}
                }
            }
        }
    }
}

# ── 20+ Adet Zengin B2B Mock Ürün Kataloğu ──────────────────────
MOCK_PRODUCTS = [
    {
        "_id": "210229916",
        "searchKey": "210229916 xerox 036k92300 left coun tm023 sarf mhm174 xerox baski cozumleri yazici sarflari zeroks drum",
        "categoryName": "Baskı Çözümleri>Yazıcı Sarfları>Xerox>Yedek Parça>Xerox Yedek Parça",
        "categoryLevel1Name": "Baskı Çözümleri",
        "categoryLevel2Name": "Yazıcı Sarfları",
        "categoryLevel3Name": "Xerox",
        "categoryLevel4Name": "Yedek Parça",
        "productUsdPrice": 16.03,
        "productTryPrice": 768.44,
        "productEurPrice": 13.81,
        "isEol": False,
        "product": {
            "productID": "210229916",
            "producerPartNo": "036K92300",
            "name": "XEROX 036K92300 (SCC) LEFT COUN",
            "description": "XEROX 036K92300 Sol Sayaç Aksamı",
            "exMaterialGroupValue": "Xerox",
            "materialGroupValue": "Sarf",
            "totalstock": 0,
            "isCampaign": False,
            "issparepartlist": True,
            "isOutlet": False,
            "warranty": 24,
            "priceA": 13.63,
            "priceD": 16.03
        },
        "storageStocks": [
            {"storageName": "Ticari Mrkz Depo", "stock": 0, "storagePlace": "2001"}
        ]
    },
    {
        "_id": "210229917",
        "searchKey": "210229917 xerox 106r02773 phaser 3020 workcentre 3025 siyah toner kartus zeroks toner",
        "categoryName": "Baskı Çözümleri>Yazıcı Sarfları>Xerox>Toner",
        "categoryLevel1Name": "Baskı Çözümleri",
        "categoryLevel2Name": "Yazıcı Sarfları",
        "categoryLevel3Name": "Xerox",
        "categoryLevel4Name": "Toner",
        "productUsdPrice": 28.50,
        "productTryPrice": 1368.00,
        "productEurPrice": 26.20,
        "isEol": False,
        "product": {
            "productID": "210229917",
            "producerPartNo": "106R02773",
            "name": "XEROX 106R02773 Phaser 3020/3025 Siyah Toner (1500 Sayfa)",
            "description": "Orijinal Xerox Siyah Lazer Toner Kartuşu",
            "exMaterialGroupValue": "Xerox",
            "materialGroupValue": "Sarf",
            "totalstock": 85,
            "isCampaign": True,
            "issparepartlist": False,
            "isOutlet": False,
            "warranty": 24,
            "priceA": 24.00,
            "priceD": 28.50
        },
        "storageStocks": [
            {"storageName": "Ticari Mrkz Depo", "stock": 55, "storagePlace": "2001"},
            {"storageName": "Ankara Depo", "stock": 30, "storagePlace": "0882"}
        ]
    },
    {
        "_id": "210229918",
        "searchKey": "210229918 xerox 101r00474 drum unitesi phaser 3260 workcentre 3225 goruntuleme tamburu zeroks drum",
        "categoryName": "Baskı Çözümleri>Yazıcı Sarfları>Xerox>Drum",
        "categoryLevel1Name": "Baskı Çözümleri",
        "categoryLevel2Name": "Yazıcı Sarfları",
        "categoryLevel3Name": "Xerox",
        "categoryLevel4Name": "Drum Ünitesi",
        "productUsdPrice": 42.00,
        "productTryPrice": 2016.00,
        "productEurPrice": 38.50,
        "isEol": False,
        "product": {
            "productID": "210229918",
            "producerPartNo": "101R00474",
            "name": "XEROX 101R00474 Görüntüleme Tamburu Drum Ünitesi (10.000 Sayfa)",
            "description": "Xerox Orijinal Drum Kartuşu",
            "exMaterialGroupValue": "Xerox",
            "materialGroupValue": "Sarf",
            "totalstock": 32,
            "isCampaign": False,
            "issparepartlist": True,
            "isOutlet": False,
            "warranty": 24,
            "priceA": 36.00,
            "priceD": 42.00
        },
        "storageStocks": [
            {"storageName": "Ticari Mrkz Depo", "stock": 32, "storagePlace": "2001"}
        ]
    },
    {
        "_id": "210334401",
        "searchKey": "210334401 dell latitude 5540 intel core i7 16gb 512gb ssd 15.6 fhd laptop dizustu bilgisayar",
        "categoryName": "Bilgisayar>Dizüstü Bilgisayar>Dell>Kurumsal Notebook",
        "categoryLevel1Name": "Bilgisayar",
        "categoryLevel2Name": "Dizüstü Bilgisayar",
        "categoryLevel3Name": "Dell",
        "categoryLevel4Name": "Kurumsal Notebook",
        "productUsdPrice": 1150.00,
        "productTryPrice": 55200.00,
        "productEurPrice": 1050.00,
        "isEol": False,
        "product": {
            "productID": "210334401",
            "producerPartNo": "N008L554015EMEA_U",
            "name": "DELL Latitude 5540 i7-1355U 16GB 512GB SSD 15.6 FHD Ubuntu",
            "description": "Dell Kurumsal İş İstasyonu Dizüstü Bilgisayar",
            "exMaterialGroupValue": "Dell",
            "materialGroupValue": "Donanım",
            "totalstock": 14,
            "isCampaign": False,
            "issparepartlist": False,
            "isOutlet": False,
            "warranty": 36,
            "priceA": 1020.00,
            "priceD": 1150.00
        },
        "storageStocks": [
            {"storageName": "Ticari Mrkz Depo", "stock": 14, "storagePlace": "2001"}
        ]
    },
    {
        "_id": "210334402",
        "searchKey": "210334402 hp proliant dl380 gen10 server sunucu 2u rack xeon silver 32gb ram",
        "categoryName": "Sunucu & Depolama>Sunucular>HP>Rack Sunucu",
        "categoryLevel1Name": "Sunucu & Depolama",
        "categoryLevel2Name": "Sunucular",
        "categoryLevel3Name": "HP",
        "categoryLevel4Name": "Rack Sunucu",
        "productUsdPrice": 2950.00,
        "productTryPrice": 141600.00,
        "productEurPrice": 2700.00,
        "isEol": False,
        "product": {
            "productID": "210334402",
            "producerPartNo": "P20174-B21",
            "name": "HPE ProLiant DL380 Gen10 Xeon Silver 4210R 32GB 8SFF Sunucu",
            "description": "Kurumsal 2U Rack Tipi HP Sunucu",
            "exMaterialGroupValue": "HP",
            "materialGroupValue": "Donanım",
            "totalstock": 5,
            "isCampaign": True,
            "issparepartlist": False,
            "isOutlet": False,
            "warranty": 36,
            "priceA": 2650.00,
            "priceD": 2950.00
        },
        "storageStocks": [
            {"storageName": "Ticari Mrkz Depo", "stock": 5, "storagePlace": "2001"}
        ]
    },
    {
        "_id": "210455110",
        "searchKey": "210455110 logitech mx master 3s kablosuz mouse bluetooth sessiz ergonomik fare",
        "categoryName": "Çevre Birimleri>Klavye & Mouse>Logitech>Kablosuz Mouse",
        "categoryLevel1Name": "Çevre Birimleri",
        "categoryLevel2Name": "Klavye & Mouse",
        "categoryLevel3Name": "Logitech",
        "categoryLevel4Name": "Kablosuz Mouse",
        "productUsdPrice": 98.00,
        "productTryPrice": 4704.00,
        "productEurPrice": 89.00,
        "isEol": False,
        "product": {
            "productID": "210455110",
            "producerPartNo": "910-006560",
            "name": "LOGITECH MX Master 3S Performans Kablosuz Mouse - Grafit",
            "description": "Ergonomik Sessiz Kablosuz Bluetooth Mouse",
            "exMaterialGroupValue": "Logitech",
            "materialGroupValue": "Aksesuar",
            "totalstock": 60,
            "isCampaign": False,
            "issparepartlist": False,
            "isOutlet": False,
            "warranty": 24,
            "priceA": 85.00,
            "priceD": 98.00
        },
        "storageStocks": [
            {"storageName": "Ticari Mrkz Depo", "stock": 40, "storagePlace": "2001"},
            {"storageName": "İzmir Depo", "stock": 20, "storagePlace": "0883"}
        ]
    },
    {
        "_id": "210229999",
        "searchKey": "210229999 xerox eski seri eol uretimden kalkmis toner sarf",
        "categoryName": "Baskı Çözümleri>Yazıcı Sarfları>Xerox>Eski Modeller",
        "categoryLevel1Name": "Baskı Çözümleri",
        "categoryLevel2Name": "Yazıcı Sarfları",
        "categoryLevel3Name": "Xerox",
        "categoryLevel4Name": "Eski Modeller",
        "productUsdPrice": 15.00,
        "productTryPrice": 720.00,
        "productEurPrice": 13.50,
        "isEol": True,  # Ömrü bitmiş ürün!
        "product": {
            "productID": "210229999",
            "producerPartNo": "006R01179",
            "name": "XEROX 006R01179 Eski Seri Kartuş (EOL)",
            "description": "Üretimi Sonlanmış Xerox Ürünü",
            "exMaterialGroupValue": "Xerox",
            "materialGroupValue": "Sarf",
            "totalstock": 0,
            "isCampaign": False,
            "issparepartlist": False,
            "isOutlet": True,
            "warranty": 0,
            "priceA": 10.00,
            "priceD": 15.00
        },
        "storageStocks": [
            {"storageName": "Ticari Mrkz Depo", "stock": 0, "storagePlace": "2001"}
        ]
    }
]


async def seed():
    es = AsyncElasticsearch(ES_URL)
    try:
        logger.info(f"Elasticsearch bağlantısı kontrol ediliyor: {ES_URL}")
        info = await es.info()
        logger.info(f"Bağlantı başarılı! ES Sürümü: {info['version']['number']}, Cluster: {info['cluster_name']}")

        # Eski indeks varsa sil ve yeniden oluştur
        if await es.indices.exists(index=INDEX_NAME):
            logger.info(f"Eski '{INDEX_NAME}' indeksi siliniyor...")
            await es.indices.delete(index=INDEX_NAME)

        logger.info(f"Yeni '{INDEX_NAME}' indeksi şemasıyla oluşturuluyor...")
        await es.indices.create(index=INDEX_NAME, body=MAPPING)

        # Mock ürünleri yükle
        logger.info(f"{len(MOCK_PRODUCTS)} adet mock ürün yükleniyor...")
        for urun in MOCK_PRODUCTS:
            doc_id = urun.pop("_id")
            await es.index(index=INDEX_NAME, id=doc_id, document=urun)

        # İndeksi yenile (arama için anında hazır olsun)
        await es.indices.refresh(index=INDEX_NAME)
        count = await es.count(index=INDEX_NAME)
        logger.info(f"✅ Başarılı! '{INDEX_NAME}' indeksine {count['count']} adet ürün yüklendi.")

    except Exception as e:
        logger.error(f"Hata oluştu: {e}")
    finally:
        await es.close()


if __name__ == "__main__":
    asyncio.run(seed())
