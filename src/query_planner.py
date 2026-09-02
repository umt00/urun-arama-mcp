# Ürün Arama MCP — Sorgu Planlayıcı (B2B Satış Temsilcileri Modu)

"""
Şema bilgisi + kullanıcı talebi → filtre çıkarımı.

Satış temsilcileri aramaları için optimize edilmiştir:
- Serbest metin aramalarında searchKey, producerPartNo, productID ve name alanlarına öncelik verilir (boosting).
- Text ve keyword alanları akıllıca haritalanır (parça kodu veya stok kodu aramalarında kaçırma olmaz).
- Filtreler 'filter' context (önbellekli/hızlı), arama metinleri 'must' context (skorlamalı) altında birleştirilir.
"""

from src.query_builder import alan_tipine_gore_sorgu, bool_sorgu_kur


def sorgu_planla(
    sema: dict,
    filtreler: dict | None = None,
    serbest_metin: str | None = None,
) -> dict:
    """
    Şema bilgisi ve kullanıcı talebinden ES sorgusu planlar.

    Args:
        sema: index_semasi_getir() çıktısı — alan adları ve tipleri
        filtreler: {"product.exMaterialGroupValue": "Xerox", "product.totalstock": {"gt": 0}}
        serbest_metin: Parça no, ürün adı veya serbest kelime araması

    Returns:
        Hazır ES sorgu body'si veya hata bilgisi içeren dict
    """
    alan_tipleri = _alan_tip_haritasi(sema)

    must_sorgular: list[dict] = []
    filter_sorgular: list[dict] = []
    hatalar: list[str] = []

    # Serbest metin araması (B2B Satış Temsilcileri Arama Mantığı)
    if serbest_metin:
        hedef_alanlar = []

        # Şemadaki aranabilir alanları topla (text ve keyword)
        for alan, tip in alan_tipleri.items():
            if tip in ("text", "keyword"):
                # Kritik satış alanlarına ağırlık (boosting) ver
                if alan == "searchKey":
                    hedef_alanlar.append("searchKey^3")
                elif "producerPartNo" in alan or "productID" in alan:
                    hedef_alanlar.append(f"{alan}^3")
                elif "name" in alan.lower() or "description" in alan.lower():
                    hedef_alanlar.append(f"{alan}^2")
                else:
                    hedef_alanlar.append(alan)

        if hedef_alanlar:
            must_sorgular.append({
                "multi_match": {
                    "query": serbest_metin,
                    "fields": hedef_alanlar,
                    "type": "best_fields",
                }
            })
        else:
            hatalar.append("Index'te metin araması yapılabilecek alan bulunamadı.")

    # Yapılandırılmış filtreler → filter'a ekle (skor etkilemesin, hızlı çalışsın)
    if filtreler:
        for alan, deger in filtreler.items():
            if alan not in alan_tipleri:
                # Esneklik: nokta notasyonlu alan kontrolü veya doğrudan eşleştirme
                hatalar.append(f"'{alan}' alanı bu index'te bulunamadı.")
                continue
            tip = alan_tipleri[alan]
            sorgu = alan_tipine_gore_sorgu(alan, tip, deger)
            filter_sorgular.append(sorgu)

    sonuc = bool_sorgu_kur(
        must=must_sorgular if must_sorgular else None,
        filter_=filter_sorgular if filter_sorgular else None,
    )

    if hatalar:
        sonuc["_uyarilar"] = hatalar

    return sonuc


def _alan_tip_haritasi(sema: dict) -> dict[str, str]:
    """Şema özetinden {alan_adi: tip} haritası oluşturur."""
    harita: dict[str, str] = {}
    for alan_bilgi in sema.get("alanlar", []):
        harita[alan_bilgi["alan"]] = alan_bilgi.get("tip", "text")
    return harita

