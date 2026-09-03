# Test — Sorgu Planlayıcı

"""query_planner modülü birim testleri."""

from src.query_planner import sorgu_planla

# Örnek şema (index_semasi_getir çıktısı formatında)
ORNEK_SEMA = {
    "index": "urunler",
    "toplam_alan": 5,
    "alanlar": [
        {"alan": "urun_adi", "tip": "text"},
        {"alan": "marka", "tip": "keyword"},
        {"alan": "kategori", "tip": "keyword"},
        {"alan": "fiyat", "tip": "float"},
        {"alan": "ram_gb", "tip": "integer"},
    ],
}


class TestSorguPlanla:
    def test_sadece_filtre(self):
        """Sadece filtre ile sorgu planlaması."""
        sonuc = sorgu_planla(ORNEK_SEMA, filtreler={"marka": "Dell"})
        assert "query" in sonuc
        assert "bool" in sonuc["query"]
        assert "filter" in sonuc["query"]["bool"]

    def test_sadece_serbest_metin(self):
        """Sadece serbest metin ile sorgu planlaması."""
        sonuc = sorgu_planla(ORNEK_SEMA, serbest_metin="dizüstü bilgisayar")
        assert "query" in sonuc
        assert "must" in sonuc["query"]["bool"]

    def test_filtre_ve_metin(self):
        """Filtre + serbest metin kombinasyonu."""
        sonuc = sorgu_planla(
            ORNEK_SEMA,
            filtreler={"marka": "Dell", "ram_gb": {"gte": 16}},
            serbest_metin="iş istasyonu",
        )
        assert "must" in sonuc["query"]["bool"]
        assert "filter" in sonuc["query"]["bool"]

    def test_olmayan_alan_uyarisi(self):
        """Index'te olmayan alan için uyarı üretilmeli."""
        sonuc = sorgu_planla(ORNEK_SEMA, filtreler={"ekran_boyutu": 15})
        assert "_uyarilar" in sonuc
        assert any("ekran_boyutu" in u for u in sonuc["_uyarilar"])

    def test_bos_sorgu(self):
        """Filtre ve metin olmadan match_all dönmeli."""
        sonuc = sorgu_planla(ORNEK_SEMA)
        assert sonuc == {"query": {"match_all": {}}}
