# Test — Güvenlik Modülü (penta-mcp-builder standardı)

"""security modülü birim testleri — @kapi_gerektirir dahil."""

import os

import pytest

from src.security import (
    hata_yaniti,
    kapi_gerektirir,
    limit_kontrol,
    log_yapilandir,
    script_sorgu_kontrol,
    whitelist_kontrol,
)


class TestWhitelistKontrol:
    def test_izinli_index(self):
        assert whitelist_kontrol("urunler", ["urunler", "products"]) is True

    def test_yasakli_index(self):
        assert whitelist_kontrol("gizli_veriler", ["urunler", "products"]) is False

    def test_bos_whitelist(self):
        """Boş whitelist → tüm index'lere izin (geliştirme ortamı)."""
        assert whitelist_kontrol("herhangi_index", []) is True

    def test_wildcard_pattern(self):
        """Wildcard pattern eşleşmesi: 'penta-urunler-*' → 'penta-urunler-v2' eşleşmeli."""
        assert whitelist_kontrol("penta-urunler-v2", ["penta-urunler-*"]) is True

    def test_wildcard_pattern_eslesmez(self):
        """Wildcard pattern eşleşmemesi: 'penta-urunler-*' → 'diger-index' eşleşmemeli."""
        assert whitelist_kontrol("diger-index", ["penta-urunler-*"]) is False


class TestLimitKontrol:
    def test_normal_limit(self):
        assert limit_kontrol(10) == 10

    def test_asiri_buyuk_limit(self):
        """limit=100000 → üst sınıra çekilmeli."""
        assert limit_kontrol(100000) == 50

    def test_negatif_limit(self):
        assert limit_kontrol(-5) == 10

    def test_sifir_limit(self):
        assert limit_kontrol(0) == 10

    def test_none_limit(self):
        assert limit_kontrol(None) == 10

    def test_ozel_max_limit(self):
        assert limit_kontrol(30, max_limit=25) == 25


class TestScriptSorguKontrol:
    def test_guvenli_sorgu(self):
        sorgu = {"query": {"bool": {"must": [{"match": {"ad": "laptop"}}]}}}
        assert script_sorgu_kontrol(sorgu) is True

    def test_script_sorgusu(self):
        """Script sorgusu → reddedilmeli."""
        sorgu = {"query": {"script_score": {"query": {"match_all": {}}}}}
        assert script_sorgu_kontrol(sorgu) is False

    def test_script_fields(self):
        sorgu = {"script_fields": {"test": {"script": "doc['field'].value"}}}
        assert script_sorgu_kontrol(sorgu) is False


class TestHataYaniti:
    def test_standart_format(self):
        sonuc = hata_yaniti("Test hatası", "TEST_KODU")
        assert sonuc["hata"] == "Test hatası"
        assert sonuc["kod"] == "TEST_KODU"
        assert sonuc["total"] == 0
        assert sonuc["items"] == []


class TestKapiGerektirir:
    """@kapi_gerektirir decorator'ı testleri."""

    @pytest.mark.asyncio
    async def test_basarili_cagri(self):
        """Decorator ile sarılmış fonksiyon başarıyla çalışmalı."""

        @kapi_gerektirir(yetki_kodu="test_yetkisi")
        async def ornek_tool():
            return {"sonuc": "başarılı"}

        sonuc = await ornek_tool()
        assert sonuc["sonuc"] == "başarılı"

    @pytest.mark.asyncio
    async def test_hata_durumu(self):
        """Tool hata fırlatırsa decorator standart hata yanıtı dönmeli."""

        @kapi_gerektirir(yetki_kodu="test_yetkisi")
        async def hatali_tool():
            raise ValueError("Test hatası")

        sonuc = await hatali_tool()
        assert sonuc["kod"] == "SUNUCU_HATASI"
        assert "Test hatası" in sonuc["hata"]

    @pytest.mark.asyncio
    async def test_api_key_olmadan_gelistirme_modu(self):
        """MCP_API_KEY tanımlı değilse geliştirme modunda çalışmalı."""
        # MCP_API_KEY'i temizle
        os.environ.pop("MCP_API_KEY", None)

        @kapi_gerektirir(yetki_kodu="test_yetkisi")
        async def ornek_tool():
            return {"sonuc": "çalıştı"}

        sonuc = await ornek_tool()
        assert sonuc["sonuc"] == "çalıştı"


class TestLogYapilandir:
    def test_log_yapilandir_calisir(self):
        """log_yapilandir() hata vermeden çalışmalı."""
        log_yapilandir()  # Hata fırlatmadan tamamlanmalı

