# Ürün Arama MCP — Şema Keşif Modülü

"""
Index keşfi ve mapping sadeleştirme.

- index_listele(): Erişilebilir index'leri listeler (whitelist filtreli)
- index_semasi_getir(): Mapping'i LLM-dostu özete dönüştürür
"""

from src.es_client import ESClient
from src.security import whitelist_kontrol


async def index_listele(es: ESClient, whitelist: list[str]) -> list[dict]:
    """
    Erişilebilir tüm index'leri listeler.

    Whitelist varsa sadece izin verilen index'leri döndürür.
    Dönen bilgi: index adı, doküman sayısı, boyut.
    """
    raw_indices = await es.list_indices()
    sonuc = []
    for idx in raw_indices:
        index_adi = idx.get("index", "")
        # Sistem index'lerini atla
        if index_adi.startswith("."):
            continue
        # Whitelist kontrolü
        if whitelist and not whitelist_kontrol(index_adi, whitelist):
            continue
        sonuc.append(
            {
                "index": index_adi,
                "dokuman_sayisi": idx.get("docs.count", "0"),
                "boyut": idx.get("store.size", "0"),
                "durum": idx.get("health", "unknown"),
            }
        )
    return sonuc


async def index_semasi_getir(es: ESClient, index: str, whitelist: list[str]) -> dict:
    """
    Belirtilen index'in mapping bilgisini sadeleştirilmiş özet olarak döndürür.

    Ham mapping'i LLM'in okuyabileceği formata dönüştürür:
    - alan adı, tip, analyzer bilgisi
    """
    # Güvenlik: whitelist kontrolü
    if whitelist and not whitelist_kontrol(index, whitelist):
        return {"hata": f"'{index}' index'ine erişim izni yok."}

    raw_mapping = await es.get_mapping(index)

    # Mapping'i sadeleştir
    return _mapping_sadelestir(raw_mapping, index)


def _mapping_sadelestir(raw_mapping: dict, index: str) -> dict:
    """Ham ES mapping çıktısını LLM-dostu özete dönüştürür.

    Object ve nested alanlar recursive olarak düzleştirilir:
    product.productID, product.totalstock gibi nokta-notasyonlu
    alan adları üretilir. Bu sayede sorgu planlayıcı ve filtreler
    doğrudan bu alan adlarını kullanabilir.
    """
    try:
        properties = raw_mapping[index]["mappings"].get("properties", {})
    except (KeyError, TypeError):
        return {"hata": f"'{index}' için mapping bilgisi alınamadı.", "alanlar": []}

    alanlar = _ozellikleri_duzlestir(properties)

    return {
        "index": index,
        "toplam_alan": len(alanlar),
        "alanlar": alanlar,
    }


def _ozellikleri_duzlestir(properties: dict, prefix: str = "") -> list[dict]:
    """Mapping properties'i recursive olarak düzleştirir.

    Nested/object altındaki alanlar 'parent.child' notasyonuyla
    tek seviyeye indirgenir.
    """
    alanlar: list[dict] = []
    for alan_adi, alan_bilgi in properties.items():
        tam_ad = f"{prefix}{alan_adi}" if not prefix else f"{prefix}.{alan_adi}"

        # Alt özellikleri olan alan (object veya nested)
        if "properties" in alan_bilgi:
            alt_tip = alan_bilgi.get("type", "object")
            # Üst alan bilgisini de ekle (object/nested olarak)
            alanlar.append(
                {
                    "alan": tam_ad,
                    "tip": alt_tip,
                    "alt_alanlar": list(alan_bilgi["properties"].keys()),
                }
            )
            # Alt alanları recursive olarak düzleştir
            alanlar.extend(_ozellikleri_duzlestir(alan_bilgi["properties"], tam_ad))
        else:
            # Yaprak alan (leaf field)
            alan: dict = {
                "alan": tam_ad,
                "tip": alan_bilgi.get("type", "text"),
            }
            if "analyzer" in alan_bilgi:
                alan["analyzer"] = alan_bilgi["analyzer"]
            if "fields" in alan_bilgi and "keyword" in alan_bilgi.get("fields", {}):
                alan["keyword_alt_alan"] = True
            alanlar.append(alan)

    return alanlar
