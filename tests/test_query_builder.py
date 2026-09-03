# Test — Sorgu Yapı Taşları

"""query_builder modülü birim testleri — ES'e gitmeden sorgu doğruluğu test edilir."""

from src.query_builder import (
    alan_tipine_gore_sorgu,
    bool_sorgu_kur,
    match_sorgusu,
    range_sorgusu,
    term_sorgusu,
)


class TestTermSorgusu:
    def test_keyword_alan(self):
        sonuc = term_sorgusu("marka", "Dell")
        assert sonuc == {"term": {"marka": "Dell"}}

    def test_boolean_alan(self):
        sonuc = term_sorgusu("stokta", True)
        assert sonuc == {"term": {"stokta": True}}


class TestMatchSorgusu:
    def test_text_alan(self):
        sonuc = match_sorgusu("urun_adi", "dizüstü bilgisayar")
        assert sonuc == {"match": {"urun_adi": "dizüstü bilgisayar"}}


class TestRangeSorgusu:
    def test_gte_lte(self):
        sonuc = range_sorgusu("fiyat", gte=1000, lte=5000)
        assert sonuc == {"range": {"fiyat": {"gte": 1000, "lte": 5000}}}

    def test_sadece_gte(self):
        sonuc = range_sorgusu("ram_gb", gte=16)
        assert sonuc == {"range": {"ram_gb": {"gte": 16}}}

    def test_tarih_araligi(self):
        sonuc = range_sorgusu("tarih", gte="2024-01-01", lte="2024-12-31")
        assert sonuc == {"range": {"tarih": {"gte": "2024-01-01", "lte": "2024-12-31"}}}


class TestAlanTipineGoreSorgu:
    def test_keyword_term(self):
        sonuc = alan_tipine_gore_sorgu("marka", "keyword", "Dell")
        assert sonuc == {"term": {"marka": "Dell"}}

    def test_text_match(self):
        sonuc = alan_tipine_gore_sorgu("aciklama", "text", "hızlı işlemci")
        assert sonuc == {"match": {"aciklama": "hızlı işlemci"}}

    def test_integer_range_dict(self):
        sonuc = alan_tipine_gore_sorgu("ram_gb", "integer", {"gte": 8, "lte": 32})
        assert sonuc == {"range": {"ram_gb": {"gte": 8, "lte": 32}}}

    def test_integer_range_tek_deger(self):
        sonuc = alan_tipine_gore_sorgu("ram_gb", "integer", 16)
        assert sonuc == {"range": {"ram_gb": {"gte": 16, "lte": 16}}}

    def test_boolean_term(self):
        sonuc = alan_tipine_gore_sorgu("aktif", "boolean", True)
        assert sonuc == {"term": {"aktif": True}}


class TestBoolSorguKur:
    def test_must_ve_filter(self):
        sonuc = bool_sorgu_kur(
            must=[{"match": {"urun_adi": "laptop"}}],
            filter_=[{"term": {"marka": "Dell"}}],
        )
        assert "must" in sonuc["query"]["bool"]
        assert "filter" in sonuc["query"]["bool"]

    def test_bos_sorgu(self):
        sonuc = bool_sorgu_kur()
        assert sonuc == {"query": {"match_all": {}}}

    def test_must_not(self):
        sonuc = bool_sorgu_kur(
            must_not=[{"term": {"durum": "pasif"}}],
        )
        assert "must_not" in sonuc["query"]["bool"]
