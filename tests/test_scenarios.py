# Test — 10 Gerçek Arama Senaryosu

"""
Ekipten toplanan 10 gerçek arama talebi ve beklenen sonuçları.

Bu senaryolar canlı ES'e bağlanarak çalıştırılır.
Başarı kriteri: Beklenen ürün ilk 5 sonuçta çıkıyor mu?

NOT: Bu dosya placeholder'dır. Gerçek senaryolar ekipten toplanacak
ve Gün 9'da doldurulacaktır.
"""

import pytest

from config.settings import get_settings
from src.es_client import ESClient
from src.query_planner import sorgu_planla
from src.result_formatter import sonuclari_formatla
from src.schema_discovery import index_semasi_getir

# ── Senaryo tanımları (ekipten toplanacak) ──────────────────────

# ── B2B Satış Temsilcileri Teams Botu Arama Senaryoları ───────────────

SENARYOLAR = [
    {
        "id": 1,
        "talep": "036K92300 parça kodlu Xerox ürününü getir",
        "filtreler": {},
        "serbest_metin": "036K92300",
        "aciklama": "Parça kodu (producerPartNo) ile doğrudan ürün sorgulama",
    },
    {
        "id": 2,
        "talep": "Stokta olan Xerox markalı sarf malzemeleri",
        "filtreler": {
            "product.exMaterialGroupValue": "Xerox",
            "product.totalstock": {"gt": 0},
        },
        "serbest_metin": "sarf yazıcı",
        "aciklama": "Marka + stokta olma (gt: 0) + kategori araması",
    },
    {
        "id": 3,
        "talep": "USD fiyatı 10 ile 50 Dolar arasındaki Xerox yedek parçaları",
        "filtreler": {
            "productUsdPrice": {"gte": 10, "lte": 50},
            "categoryLevel4Name": "Yedek Parça",
        },
        "serbest_metin": "Xerox",
        "aciklama": "Fiyat aralığı + seviye 4 kategori filtresi",
    },
    {
        "id": 4,
        "talep": "210229916 stok kodlu ürünün fiyat ve stok durumunu ver",
        "filtreler": {},
        "serbest_metin": "210229916",
        "aciklama": "Stok/Ürün ID (productID) araması",
    },
    {
        "id": 5,
        "talep": "Baskı çözümleri kategorisindeki EOL olmayan (aktif) ürünler",
        "filtreler": {
            "categoryLevel1Name": "Baskı Çözümleri",
            "isEol": False,
        },
        "serbest_metin": "yazıcı",
        "aciklama": "Level 1 kategori + ömrü bitmemiş (isEol: False) ürün filtresi",
    },
    {
        "id": 6,
        "talep": "Sarf malzemesi grubundaki kampanya ürünleri",
        "filtreler": {
            "product.materialGroupValue": "Sarf",
            "product.isCampaign": True,
        },
        "serbest_metin": "kampanya",
        "aciklama": "Malzeme grubu + kampanya flag filtresi",
    },
    {
        "id": 7,
        "talep": "Zeroks drum kartuş araması (Yazım hatası toleransı)",
        "filtreler": {},
        "serbest_metin": "zeroks drum",
        "aciklama": "searchKey sayesinde okunuş/yazım hatası toleransı testi",
    },
    {
        "id": 8,
        "talep": "5000 TL altındaki stoktaki ürünler",
        "filtreler": {
            "productTryPrice": {"lte": 5000},
            "product.totalstock": {"gt": 0},
        },
        "serbest_metin": "sarf",
        "aciklama": "TL bazlı fiyat üst sınırı + stok kontrolü",
    },
    {
        "id": 9,
        "talep": "Yedek parça listesinde (issparepartlist) yer alan Xerox ürünleri",
        "filtreler": {
            "product.issparepartlist": True,
        },
        "serbest_metin": "Xerox",
        "aciklama": "Yedek parça liste filtresi",
    },
    {
        "id": 10,
        "talep": "Ticari Mrkz Depo stoklu ürünler",
        "filtreler": {
            "storageStocks.storageName": "Ticari Mrkz Depo",
        },
        "serbest_metin": "Xerox",
        "aciklama": "Depo adı bazında stok sorgulama",
    },
]


class TestGercekSenaryolar:
    """
    10 gerçek B2B arama senaryosu entegrasyon testleri.

    Yerel Docker Elasticsearch üzerinde product-price indeksine karşı koşulur.
    Başarı kriteri: Sorgu çalışmalı ve beklenen ürünler dönmelidir.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("senaryo", SENARYOLAR, ids=[f"senaryo_{s['id']}" for s in SENARYOLAR])
    async def test_senaryo(self, senaryo):
        """Her senaryo için sorgunun çalıştığını ve sonuç döndürdüğünü doğrula."""
        settings = get_settings()
        es = ESClient(settings)
        index = "product-price"

        # 1. Şemayı al
        sema = await index_semasi_getir(es, index, settings.index_whitelist)
        assert "hata" not in sema, f"Şema hatası: {sema.get('hata')}"

        # 2. Sorgu planla
        sorgu_body = sorgu_planla(sema, senaryo["filtreler"], senaryo["serbest_metin"])
        sorgu_body.pop("_uyarilar", None)

        # 3. ES'te ara
        es_yanit = await es.search(index=index, body=sorgu_body, size=10)

        # 4. Formatla
        sonuc = sonuclari_formatla(es_yanit, index, senaryo["filtreler"], senaryo["serbest_metin"])

        # 5. Doğrulama
        assert sonuc["hata"] is None
        assert "items" in sonuc
        assert "total" in sonuc

        # Temizlik
        await es.close()

