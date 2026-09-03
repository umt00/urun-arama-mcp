# Ürün Arama MCP — Sentetik Elasticsearch Veri Yükleme Scripti (Genişletilmiş Şema)

import asyncio
import logging
import os
import random

# Windows localhost proxy atlatma
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("seed_mock_es")

ES_URL = "http://127.0.0.1:9200"
INDEX_NAME = "product-price"

# ── Gerçekçi product-price İndeks Mapping Şeması ────────────────
# Dinamik şemaya güveniyoruz fakat kritik nested alanları belirtiyoruz
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
                    "exMaterialGroupValue": {"type": "keyword"},
                    "materialGroupValue": {"type": "keyword"},
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
                    "storagePlace": {"type": "keyword"},
                },
            },
            "productPropertyRelations": {"type": "nested"},
        }
    }
}

# ── Zenginleştirilmiş Kategori ve Marka Verileri ────────────────
BRANDS = [
    "MSI",
    "Logitech",
    "Asus",
    "Exper",
    "Xerox",
    "HP",
    "Dell",
    "Lenovo",
    "Canon",
    "Epson",
    "BenQ",
    "ViewSonic",
    "Razer",
    "Corsair",
    "SteelSeries",
    "Samsung",
    "LG",
    "AOC",
    "Philips",
    "Kingston",
    "Sandisk",
    "Brother",
    "Lexmark",
]

CATEGORIES = [
    {
        "cat1": "Çevre Birimleri",
        "cat2": "Klavye & Mouse",
        "cat4_list": ["Oyuncu Mouse", "Kablosuz Mouse", "Mekanik Klavye", "Membran Klavye", "Klavye Mouse Seti"],
        "mat_group": "Aksesuar",
    },
    {
        "cat1": "Çevre Birimleri",
        "cat2": "Monitörler",
        "cat4_list": [
            "Oyuncu Monitörü",
            "Ofis Monitörü",
            "Kavisli Monitör",
            "Grafik Tasarım Monitörü",
            "4K Ultra HD Monitör",
        ],
        "mat_group": "Donanım",
    },
    {
        "cat1": "Çevre Birimleri",
        "cat2": "Ses Sistemleri",
        "cat4_list": ["Oyuncu Kulaklığı", "Ofis Kulaklığı", "Bluetooth Hoparlör", "Ses Kartı"],
        "mat_group": "Aksesuar",
    },
    {
        "cat1": "Baskı Çözümleri",
        "cat2": "Yazıcılar",
        "cat4_list": [
            "Lazer Yazıcı",
            "Mürekkep Püskürtmeli Yazıcı",
            "Çok Fonksiyonlu Yazıcı",
            "Nokta Vuruşlu Yazıcı",
            "Barkod Yazıcı",
        ],
        "mat_group": "Donanım",
    },
    {
        "cat1": "Baskı Çözümleri",
        "cat2": "Yazıcı Sarfları",
        "cat4_list": [
            "Siyah Toner",
            "Renkli Toner",
            "Kartuş",
            "Şerit",
            "Drum Ünitesi",
            "Yedek Parça",
            "Atık Toner Kutusu",
        ],
        "mat_group": "Sarf",
    },
    {
        "cat1": "Bilgisayar",
        "cat2": "Dizüstü Bilgisayar",
        "cat4_list": ["Oyun Bilgisayarı", "Kurumsal Notebook", "İş İstasyonu Laptop", "Ultrabook", "Tablet PC"],
        "mat_group": "Donanım",
    },
    {
        "cat1": "Bilgisayar Bileşenleri",
        "cat2": "İç Donanım",
        "cat4_list": [
            "Anakart",
            "Ekran Kartı",
            "Bellek (RAM)",
            "İşlemci (CPU)",
            "NVMe M.2 SSD",
            "SATA SSD",
            "Dahili HDD",
        ],
        "mat_group": "Donanım",
    },
    {
        "cat1": "Sunucu & Ağ",
        "cat2": "Ağ Ürünleri",
        "cat4_list": ["Yönetilebilir Switch", "PoE Anahtar", "Firewall", "Router", "Access Point"],
        "mat_group": "Ağ",
    },
]

DEPOLAR = [
    {"name": "Ticari Mrkz Depo", "code": "2001", "place": "0881"},
    {"name": "Ankara Depo", "code": "0882", "place": "0882"},
    {"name": "İzmir Depo", "code": "0883", "place": "0883"},
    {"name": "Teknopark Lojistik", "code": "0884", "place": "0884"},
]


def generate_unique_product(seq: int) -> dict:
    brand = random.choice(BRANDS)
    category = random.choice(CATEGORIES)
    cat4 = random.choice(category["cat4_list"])

    product_id = f"210{seq:06d}"
    part_no = f"{brand[:3].upper()}{random.randint(100, 99999)}-{chr(random.randint(65, 90))}"

    model_suffix = f"Pro {random.randint(100, 999)}" if random.random() > 0.5 else f"Elite {random.randint(1, 99)}"

    # Donanım detayları (i7, 16GB, 512GB vb.)
    hardware_specs = ""
    if category["cat1"] == "Bilgisayar":
        cpus = ["i5", "i7", "i9", "Ryzen 5", "Ryzen 7", "Ryzen 9", "Core Ultra 7", "Apple M3"]
        rams = ["8GB RAM", "16GB RAM", "32GB RAM", "64GB RAM"]
        storages = ["256GB SSD", "512GB SSD", "1TB SSD", "2TB NVMe SSD"]
        hardware_specs = f"{random.choice(cpus)} {random.choice(rams)} {random.choice(storages)}"
        name = f"{brand} {cat4} {hardware_specs} {part_no} {model_suffix}"
    else:
        name = f"{brand} {part_no} {cat4} {model_suffix}"

    usd_price = round(random.uniform(15, 3500), 2)
    try_price = round(usd_price * 34.5, 2)
    eur_price = round(usd_price * 0.92, 2)

    is_out_of_stock = random.random() < 0.15
    storage_stocks = []

    # Depo Stoklarını ve Dinamik Alanları Ayarlama
    stock_0881 = 0
    stock_0882 = 0
    stock_0883 = 0
    stock_0884 = 0

    if is_out_of_stock:
        total_stock = 0
        storage_stocks.append(
            {
                "createdOn": "2024-01-01T00:00:00.000Z",
                "product": "",
                "productID": product_id,
                "productionPlace": "0881",
                "stock": 0,
                "storageName": "Ticari Mrkz Depo",
                "storagePlace": "2001",
                "storageStockID": random.randint(1000, 9999),
                "updatedOn": "2025-01-01T00:00:00.000Z",
            }
        )
    else:
        total_stock = random.randint(1, 600)
        remaining = total_stock
        selected_depos = random.sample(DEPOLAR, k=random.randint(1, 3))

        for i, depo in enumerate(selected_depos):
            if i == len(selected_depos) - 1:
                stock = remaining
            else:
                stock = random.randint(0, remaining) if remaining > 0 else 0
                remaining -= stock

            if depo["code"] == "2001":
                stock_0881 = stock
            elif depo["code"] == "0882":
                stock_0882 = stock
            elif depo["code"] == "0883":
                stock_0883 = stock
            elif depo["code"] == "0884":
                stock_0884 = stock

            storage_stocks.append(
                {
                    "createdOn": "2024-01-01T00:00:00.000Z",
                    "product": "",
                    "productID": product_id,
                    "productionPlace": depo["place"],
                    "stock": stock,
                    "storageName": depo["name"],
                    "storagePlace": depo["code"],
                    "storageStockID": random.randint(1000, 9999),
                    "updatedOn": "2025-01-01T00:00:00.000Z",
                }
            )

    search_key_parts = [
        product_id,
        part_no.lower(),
        brand.lower(),
        category["cat1"].lower(),
        category["cat2"].lower(),
        cat4.lower(),
        name.lower(),
        hardware_specs.lower(),
        category["mat_group"].lower(),
    ]
    search_key = " ".join(search_key_parts)

    is_eol = random.random() < 0.05
    is_campaign = random.random() < 0.20
    is_sparepart = "Yedek Parça" in cat4 or "Sarf" in category["mat_group"]
    is_outlet = random.random() < 0.05

    # Kapsamlı Doküman Yapısı
    doc = {
        "_index": INDEX_NAME,
        "_id": product_id,
        "_source": {
            "attribute1": f"Türü : {cat4}",
            "attribute10": "",
            "attribute2": "",
            "attribute3": "",
            "attribute4": "",
            "attribute5": "",
            "attribute6": "",
            "attribute7": "",
            "attribute8": "",
            "attribute9": "",
            "boardIds": "null",
            "brandImage": f"http://img.bayinet.com.tr/Content/Brands/images/{brand}.jpg",
            "categoryCode": f"04>04047>04047174>{random.randint(100, 999)}",
            "categoryLevel1": "04",
            "categoryLevel1Name": category["cat1"],
            "categorylevel1name_en": "",
            "categoryLevel2": "04047",
            "categoryLevel2Name": category["cat2"],
            "categorylevel2name_en": "",
            "categoryLevel3": "04047174",
            "categoryLevel3Name": brand,
            "categorylevel3name_en": "",
            "categoryLevel4": "04047aaa099",
            "categoryLevel4Name": cat4,
            "categorylevel4name_en": "",
            "categoryName": f"{category['cat1']}>{category['cat2']}>{brand}>{cat4}",
            "categoryname_en": "",
            "cpuIds": "null",
            "description_en": "",
            "gtipNumber": "8443.99.90.90.00",
            "isBoard": False,
            "isBundle": False,
            "isCpu": False,
            "isdeleted": False,
            "isEol": is_eol,
            "long_description_en": "",
            "minimum_quantity": 0,
            "mstae": "",
            "packaged_product": "",
            "price": {
                "bundleProductPrice": 0,
                "dealerPrice": 0,
                "dealerPriceF": 0,
                "discountRate": 0,
                "isCampign": is_campaign,
                "isPriceScale": False,
                "isSapPrice": False,
                "lastUserPrice": 0,
                "lastUserPriceF": 0,
                "meins": "",
                "orderQty": 0,
                "qty": 0,
                "specialPrice": 0,
                "specialPriceF": 0,
                "stockOnShip": 0,
                "stockQty": 0,
                "vatRate": 20,
                "vatRateF": 0,
            },
            "product": {
                "avgStockAge0881": 0,
                "avgStockAge0882": 0,
                "avgStockAge0883": 0,
                "avgStockAge0884": 0,
                "branchStocks": {"branchcode": "", "branchname": "", "branchstockquantity": ""},
                "categoryID": "04047174099600",
                "createdOn": "2024-01-27T00:00:00.000Z",
                "currencyIDA": "USD",
                "currencyIDB": "USD",
                "currencyIDC": "USD",
                "currencyIDD": "USD",
                "currencyIDSK": "USD",
                "currencyIDTeknosa": "",
                "dealerDocPrice": "",
                "dealerPrice": 0,
                "description": name,
                "discountRate": 0,
                "ean": f"0000{product_id}",
                "eanUnit": "ST",
                "ekEmail": "ayninur.kabak@penta.com.tr",
                "ekGrp": "M20",
                "ekName": "Şevval Ayni.Kabak",
                "exMaterialGroupID": "MHM174",
                "exMaterialGroupValue": brand,
                "explanation": "",
                "grossWeight": "0.180 ",
                "hasDocCurrency": False,
                "hasOutlet": is_outlet,
                "hasZTipPrice": False,
                "heigth": 3,
                "isB2B": False,
                "isBestSeller": False,
                "isCabinet": False,
                "isCampaign": is_campaign,
                "isCampaing": is_campaign,
                "isCloud": False,
                "isDiscount": False,
                "isFavorite": False,
                "isHighlight": False,
                "isLicensing": True,
                "isNew": False,
                "isOnlyPackage": False,
                "isOpportunity": False,
                "isOutlet": is_outlet,
                "isPriceScale": False,
                "isProject": False,
                "isPromotion": False,
                "isSoon": False,
                "issparepartlist": is_sparepart,
                "isSpecialStorage": False,
                "isTogether": False,
                "isTT": False,
                "isXml": False,
                "materialGroupID": "TM023",
                "materialGroupValue": category["mat_group"],
                "materialType": "2001",
                "name": name,
                "netWeight": "0.180 ",
                "origin": "CN",
                "outletPriceRange": "",
                "point": 0,
                "prctr": "0001088012",
                "priceA": round(usd_price * 0.88, 2),
                "priceB": round(usd_price * 0.88, 2),
                "priceC": round(usd_price * 0.88, 2),
                "priceD": usd_price,
                "priceDMarket": 0,
                "priceE": 0,
                "priceScaleID": "",
                "priceSK": round(usd_price * 1.15, 2),
                "pricetT": 0,
                "priority": 1,
                "producerPartNo": part_no,
                "producerWarranty": random.choice([0, 12, 24, 36]),
                "productGroup": "",
                "productID": product_id,
                "productTypeID": 1,
                "profitRateIsSet": False,
                "pypstock": 0,
                "qty": 0,
                "qtyString": "0",
                "sanal_Stok": 0,
                "sanal_Stok_Birim": "ST",
                "shopCategories": "",
                "sKDocPrice": "",
                "specialDocPrice": "",
                "specialPrice": 0,
                "status": False,
                "stock0881": stock_0881,
                "stock0882": stock_0882,
                "stock0883": stock_0883,
                "stock0884": stock_0884,
                "tLPrice": 0,
                "totalstock": total_stock,
                "updatedOn": "2025-03-14T00:00:00.000Z",
                "vatRate": 20,
                "volume": "0.056 ",
                "volumeUnit": "DES",
                "warranty": random.choice([0, 12, 24, 36]),
                "weightUnit": "KG",
                "width": 4,
            },
            "productEurPrice": eur_price,
            "productImagePath": "",
            "productIsForm": False,
            "productPropertyRelations": [
                {
                    "propertyOptionName": cat4,
                    "productID": product_id,
                    "priority": 100,
                    "propertyOptionID": 43216921,
                    "propertyCode": "08047_TURU",
                    "propertyName": "Türü;100;1",
                    "propertyGroupName": f"* {category['cat2']}",
                    "propertyOptionCode": "CODE_GEN",
                    "allowFiltering": True,
                    "propertyGroupID": 432,
                    "propertyID": 1692,
                    "productPropertyID": 0,
                }
            ],
            "productSKEurPrice": round(eur_price * 1.15, 2),
            "productSKTryPrice": round(try_price * 1.15, 2),
            "productSKUsdPrice": round(usd_price * 1.15, 2),
            "productTryPrice": try_price,
            "productUsdPrice": usd_price,
            "searchKey": search_key,
            "shopCategories": "[]",
            "specialBrands": "",
            "specialPriceCustomers": "",
            "storageStocks": storage_stocks,
            "subscriptionText": "",
            "videoPath": "",
        },
    }
    return doc


async def seed():
    es = AsyncElasticsearch(ES_URL)
    try:
        logger.info(f"Elasticsearch bağlantısı kontrol ediliyor: {ES_URL}")
        info = await es.info()
        logger.info(f"Bağlantı başarılı! ES Sürümü: {info['version']['number']}, Cluster: {info['cluster_name']}")

        if await es.indices.exists(index=INDEX_NAME):
            logger.info(f"Eski '{INDEX_NAME}' indeksi siliniyor...")
            await es.indices.delete(index=INDEX_NAME)

        logger.info(f"Yeni '{INDEX_NAME}' indeksi detaylı üretim şemasıyla oluşturuluyor...")
        await es.indices.create(index=INDEX_NAME, body=MAPPING)

        logger.info("Devasa şablon bazlı 1000 eşsiz ürün üretiliyor...")

        actions = []
        for i in range(1, 1001):
            actions.append(generate_unique_product(i))

        logger.info("Elasticsearch'e 1000 adet bulk kayıt atılıyor...")
        success, _ = await async_bulk(es, actions)

        await es.indices.refresh(index=INDEX_NAME)
        count = await es.count(index=INDEX_NAME)
        logger.info(f"✅ Başarılı! '{INDEX_NAME}' indeksine {count['count']} adet eşsiz ürün yüklendi.")

    except Exception as e:
        logger.error(f"Hata oluştu: {e}")
    finally:
        await es.close()


if __name__ == "__main__":
    asyncio.run(seed())
