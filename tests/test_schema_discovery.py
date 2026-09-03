# Test — Şema Keşif Modülü

"""index_listele ve index_semasi_getir fonksiyonlarının birim testleri."""

from src.schema_discovery import _mapping_sadelestir


class TestMappingSadelestir:
    """Mapping sadeleştirme fonksiyonu testleri."""

    def test_basit_mapping(self):
        """Basit bir mapping'in doğru sadeleştirildiğini kontrol et."""
        raw_mapping = {
            "urunler": {
                "mappings": {
                    "properties": {
                        "urun_adi": {"type": "text", "analyzer": "standard"},
                        "marka": {"type": "keyword"},
                        "fiyat": {"type": "float"},
                        "stokta": {"type": "boolean"},
                    }
                }
            }
        }
        sonuc = _mapping_sadelestir(raw_mapping, "urunler")

        assert sonuc["index"] == "urunler"
        assert sonuc["toplam_alan"] == 4
        assert len(sonuc["alanlar"]) == 4

        # Alan tipleri doğru mu?
        alan_map = {a["alan"]: a["tip"] for a in sonuc["alanlar"]}
        assert alan_map["urun_adi"] == "text"
        assert alan_map["marka"] == "keyword"
        assert alan_map["fiyat"] == "float"
        assert alan_map["stokta"] == "boolean"

    def test_keyword_alt_alan(self):
        """text alanının keyword alt-alanını tespit ettiğini kontrol et."""
        raw_mapping = {
            "urunler": {
                "mappings": {
                    "properties": {
                        "baslik": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        }
                    }
                }
            }
        }
        sonuc = _mapping_sadelestir(raw_mapping, "urunler")
        assert sonuc["alanlar"][0].get("keyword_alt_alan") is True

    def test_bos_mapping(self):
        """Boş mapping için hata döndüğünü kontrol et."""
        sonuc = _mapping_sadelestir({}, "yok")
        assert "hata" in sonuc

    def test_nested_object(self):
        """Nested object alanlarını tespit ettiğini kontrol et."""
        raw_mapping = {
            "urunler": {
                "mappings": {
                    "properties": {
                        "ozellikler": {
                            "properties": {
                                "renk": {"type": "keyword"},
                                "boyut": {"type": "keyword"},
                            }
                        }
                    }
                }
            }
        }
        sonuc = _mapping_sadelestir(raw_mapping, "urunler")
        alan = sonuc["alanlar"][0]
        assert alan["tip"] == "object"
        assert "renk" in alan["alt_alanlar"]
