# Ürün Arama MCP — Sorgu Yapı Taşları

"""
Alan tipine göre Elasticsearch sorgu yapı taşları.

Kurallar:
- keyword → term (kesin eşleşme)
- text    → match (tam metin)
- integer/float/double → range (sayısal aralık)
- date    → range (tarih aralığı)
- boolean → term (true/false)

Bool sorgu yapısı:
- must:     Metin araması (skor etkiler)
- filter:   Filtreleme koşulları (skor etkilemez, daha hızlı)
- must_not: Hariç tutma
- should:   Opsiyonel koşullar
"""

# Alan tipine göre sorgu tipi haritası
ALAN_SORGU_HARITASI: dict[str, str] = {
    "keyword": "term",
    "text": "match",
    "integer": "range",
    "long": "range",
    "float": "range",
    "double": "range",
    "date": "range",
    "boolean": "term",
}


def term_sorgusu(alan: str, deger) -> dict:
    """keyword veya boolean alanlar için kesin eşleşme sorgusu."""
    return {"term": {alan: deger}}


def match_sorgusu(alan: str, metin: str) -> dict:
    """text alanlar için tam metin araması sorgusu."""
    return {"match": {alan: metin}}


def range_sorgusu(alan: str, gte=None, lte=None, gt=None, lt=None) -> dict:
    """Sayısal veya tarih alanlar için aralık sorgusu."""
    kosullar = {}
    if gte is not None:
        kosullar["gte"] = gte
    if lte is not None:
        kosullar["lte"] = lte
    if gt is not None:
        kosullar["gt"] = gt
    if lt is not None:
        kosullar["lt"] = lt
    return {"range": {alan: kosullar}}


def alan_tipine_gore_sorgu(alan: str, tip: str, deger) -> dict:
    """
    Alan tipine göre uygun sorgu yapı taşını seçer ve üretir.

    ⚠️ text alanda term kullanmak boş sonuç döndürür!
    """
    if tip in ("keyword", "boolean"):
        return term_sorgusu(alan, deger)
    elif tip == "text":
        return match_sorgusu(alan, str(deger))
    elif tip in ("integer", "long", "float", "double", "date"):
        # deger dict ise range parametrelerini içerir: {"gte": 10, "lte": 20}
        if isinstance(deger, dict):
            return range_sorgusu(alan, **deger)
        # Tek değer ise eşitlik olarak range
        return range_sorgusu(alan, gte=deger, lte=deger)
    else:
        # Bilinmeyen tip — match ile dene
        return match_sorgusu(alan, str(deger))


def bool_sorgu_kur(
    must: list[dict] | None = None,
    filter_: list[dict] | None = None,
    should: list[dict] | None = None,
    must_not: list[dict] | None = None,
) -> dict:
    """
    Bool sorgu oluşturur.

    Kural:
    - Filtreleme koşulları (marka, kategori) → filter (skor etkilemez, cache'lenir)
    - Metin araması → must (skor etkiler)
    - Hariç tutma → must_not
    - Opsiyonel → should
    """
    bool_query: dict = {}
    if must:
        bool_query["must"] = must
    if filter_:
        bool_query["filter"] = filter_
    if should:
        bool_query["should"] = should
    if must_not:
        bool_query["must_not"] = must_not

    return {"query": {"bool": bool_query}} if bool_query else {"query": {"match_all": {}}}
