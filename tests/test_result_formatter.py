# Test — Sonuç Biçimlendirici

"""result_formatter modülü birim testleri — yeni düz yapı şeması."""

from src.result_formatter import bos_sonuc, sonuclari_formatla

# Örnek ES yanıtı
ORNEK_ES_YANIT = {
    "hits": {
        "total": {"value": 42, "relation": "eq"},
        "hits": [
            {
                "_id": "abc123",
                "_score": 8.45,
                "_source": {
                    "urun_adi": "Dell Latitude 5540",
                    "marka": "Dell",
                    "ram_gb": 16,
                    "fiyat": 45000,
                },
            },
            {
                "_id": "def456",
                "_score": 7.20,
                "_source": {
                    "urun_adi": "Lenovo ThinkPad T14",
                    "marka": "Lenovo",
                    "ram_gb": 16,
                    "fiyat": 42000,
                },
            },
        ],
    }
}


class TestSonuclariFormatla:
    def test_sabit_sema(self):
        """Çıktının sabit şemaya uyduğunu kontrol et."""
        sonuc = sonuclari_formatla(ORNEK_ES_YANIT, "urunler")
        assert "total" in sonuc
        assert "count" in sonuc
        assert "items" in sonuc
        assert "sorgu_bilgisi" in sonuc
        assert "hata" in sonuc

    def test_total(self):
        sonuc = sonuclari_formatla(ORNEK_ES_YANIT, "urunler")
        assert sonuc["total"] == 42

    def test_count(self):
        sonuc = sonuclari_formatla(ORNEK_ES_YANIT, "urunler")
        assert sonuc["count"] == 2

    def test_item_duz_yapi(self):
        """Alanlar düz yapıda — iç içe 'alanlar' dict'i yok."""
        sonuc = sonuclari_formatla(ORNEK_ES_YANIT, "urunler")
        item = sonuc["items"][0]
        assert item["id"] == "abc123"
        assert item["skor"] == 8.45
        # _source alanları doğrudan item seviyesinde
        assert item["urun_adi"] == "Dell Latitude 5540"
        assert item["marka"] == "Dell"
        assert item["ram_gb"] == 16
        assert item["fiyat"] == 45000

    def test_sorgu_bilgisi(self):
        sonuc = sonuclari_formatla(
            ORNEK_ES_YANIT,
            "urunler",
            filtreler={"marka": "Dell"},
            serbest_metin="laptop",
        )
        assert sonuc["sorgu_bilgisi"]["index"] == "urunler"
        assert sonuc["sorgu_bilgisi"]["filtreler"] == {"marka": "Dell"}
        assert sonuc["sorgu_bilgisi"]["serbest_metin"] == "laptop"

    def test_hata_none(self):
        sonuc = sonuclari_formatla(ORNEK_ES_YANIT, "urunler")
        assert sonuc["hata"] is None


class TestBosSonuc:
    def test_varsayilan_mesaj(self):
        sonuc = bos_sonuc("urunler")
        assert sonuc["total"] == 0
        assert sonuc["count"] == 0
        assert sonuc["items"] == []
        assert "mesaj" in sonuc
