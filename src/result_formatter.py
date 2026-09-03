# Ürün Arama MCP — Sonuç Biçimlendirici (B2B Satış Temsilcileri Modu)

"""
ES yanıtını B2B satış temsilcileri ve Teams Botu için optimize edilmiş sabit JSON şemasına dönüştürür.

Satış Temsilcileri İçin Öne Çıkarılan Alanlar:
- urun_adi (product.name / product.description)
- urun_kodu (product.productID)
- part_no (product.producerPartNo)
- marka (product.exMaterialGroupValue / categoryLevel3Name)
- kategori (categoryName)
- stok_toplam (product.totalstock)
"""


def _nested_get(source: dict, key: str, default=None):
    """Nokta-notasyonlu anahtarı nested dict içinde çözer.

    Örnek:
        _nested_get({"product": {"productID": "123"}}, "product.productID")
        → "123"

        _nested_get({"categoryName": "Baskı"}, "categoryName")
        → "Baskı"
    """
    keys = key.split(".")
    value = source
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
        if value is None:
            return default
    return value


def sonuclari_formatla(
    es_yanit: dict,
    index: str,
    filtreler: dict | None = None,
    serbest_metin: str | None = None,
) -> dict:
    """
    Ham ES arama yanıtını B2B Satış Temsilcileri için optimize edilmiş düz JSON şemasına dönüştürür.

    Args:
        es_yanit: Elasticsearch search API yanıtı
        index: Sorgulanan index adı
        filtreler: Kullanılan filtreler
        serbest_metin: Kullanılan serbest metin

    Returns:
        Kompakt ve satış özetli JSON yapısı
    """
    try:
        hits = es_yanit.get("hits", {})
        total = hits.get("total", {})
        total_value = total.get("value", 0) if isinstance(total, dict) else total

        items = []
        for hit in hits.get("hits", []):
            source = hit.get("_source", {})

            # Satış Temsilcisi için Özet Bilgiler (Hızlı Teams Kartı Oluşturma İçin)
            urun_adi = (
                _nested_get(source, "product.name")
                or _nested_get(source, "product.description")
                or source.get("name")
                or ""
            )
            if isinstance(urun_adi, list):
                urun_adi = urun_adi[0] if urun_adi else ""

            part_no = _nested_get(source, "product.producerPartNo") or source.get("producerPartNo") or ""
            if isinstance(part_no, list):
                part_no = part_no[0] if part_no else ""

            marka = (
                _nested_get(source, "product.exMaterialGroupValue")
                or source.get("categoryLevel3Name")
                or source.get("brand")
                or ""
            )
            if isinstance(marka, list):
                marka = marka[0] if marka else ""

            stok = _nested_get(source, "product.totalstock")
            if stok is None:
                stok = source.get("totalstock", 0)
            if isinstance(stok, list):
                stok = stok[0] if stok else 0

            # Temel item yapısını oluştur
            item = {
                "id": hit.get("_id", ""),
                "skor": hit.get("_score"),
                "satis_ozeti": {
                    "urun_adi": urun_adi,
                    "part_no": part_no,
                    "marka": marka,
                    "stok_toplam": stok,
                },
            }

            # Tüm orijinal alanları da düz (flat) olarak ekle
            item.update(source)
            items.append(item)

        sorgu_bilgisi: dict = {"index": index}
        if filtreler:
            sorgu_bilgisi["filtreler"] = filtreler
        if serbest_metin:
            sorgu_bilgisi["serbest_metin"] = serbest_metin

        return {
            "total": total_value,
            "count": len(items),
            "items": items,
            "sorgu_bilgisi": sorgu_bilgisi,
            "hata": None,
        }
    except Exception as e:
        return {
            "total": 0,
            "count": 0,
            "items": [],
            "sorgu_bilgisi": {"index": index},
            "hata": f"Sonuç biçimlendirme hatası: {str(e)}",
        }


def bos_sonuc(index: str, mesaj: str = "Bu kriterlere uyan ürün bulunamadı.") -> dict:
    """Boş sonuç için standart yanıt üretir."""
    return {
        "total": 0,
        "count": 0,
        "items": [],
        "sorgu_bilgisi": {"index": index},
        "hata": None,
        "mesaj": mesaj,
    }
