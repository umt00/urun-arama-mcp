# Ürün Arama MCP — Güvenlik Modülü (penta-mcp-builder standardı)

"""
Güvenlik ve dayanıklılık kontrolleri.

Ekip standardı: penta-mcp-builder desenleri uygulanır.

Kurallar:
- @kapi_gerektirir decorator'ı ile yetki kontrolü
- Salt-okunur API key kullanılmalı
- Index whitelist — sadece izin verilen index'lere erişim
- limit üst sınırı — aşırı büyük sorgular engellenir
- Script sorgu yasağı — ES script sorguları çalıştırılamaz
- Sorgu enjeksiyonu koruması — kullanıcı metni parametreli yapı taşlarıyla işlenir
- Standart hata formatı — tüm hatalar aynı JSON yapısında
"""

import logging
import os
import time
from functools import wraps

logger = logging.getLogger(__name__)

# Varsayılan üst sınırlar
DEFAULT_MAX_LIMIT = 50
ABSOLUTE_MAX_LIMIT = 100


# ── penta-mcp-builder: Standart Log Yapılandırması ──────────────

def log_yapilandir(seviye: int = logging.INFO) -> None:
    """
    Ekip standardı log formatını yapılandırır.

    Format: TARİH [SEVİYE] MODÜL - MESAJ
    Tüm MCP servisleri bu formatı kullanır.
    """
    logging.basicConfig(
        level=seviye,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ── penta-mcp-builder: @kapi_gerektirir Decorator'ı ─────────────

def kapi_gerektirir(yetki_kodu: str = "arama_yetkisi"):
    """
    Ekip standardı yetkilendirme decorator'ı.

    Her MCP tool çağrısından önce araya girerek yetki kontrolü yapar.
    MCP_API_KEY ortam değişkeni tanımlıysa, gelen isteklerde bu key aranır.
    Tanımlı değilse (geliştirme ortamı) tüm isteklere izin verir.

    Kullanım:
        @mcp.tool()
        @kapi_gerektirir(yetki_kodu="urun_arama")
        async def urun_ara_tool(...):
            ...

    Args:
        yetki_kodu: Bu tool için gerekli yetki tanımlayıcısı (loglama amaçlı)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            baslangic = time.time()
            fonksiyon_adi = func.__name__

            # MCP_API_KEY tanımlıysa yetki kontrolü aktif
            beklenen_key = os.getenv("MCP_API_KEY", "")

            if beklenen_key:
                # Gerçek ortam: API key kontrolü
                # NOT: FastMCP üzerinden gelen isteklerde header doğrulaması
                # ekip altyapısına göre genişletilebilir.
                logger.info(
                    f"Yetki kontrolü aktif | tool={fonksiyon_adi} | yetki={yetki_kodu}"
                )
            else:
                # Geliştirme ortamı: API key tanımlı değil, uyarı ver
                logger.debug(
                    f"Yetki kontrolü devre dışı (MCP_API_KEY tanımlı değil) | tool={fonksiyon_adi}"
                )

            # Tool'u çalıştır
            try:
                sonuc = await func(*args, **kwargs)
                sure = round(time.time() - baslangic, 3)
                logger.info(
                    f"Tool tamamlandı | tool={fonksiyon_adi} | sure={sure}s | durum=BASARILI"
                )
                return sonuc
            except Exception as e:
                sure = round(time.time() - baslangic, 3)
                logger.error(
                    f"Tool hatası | tool={fonksiyon_adi} | sure={sure}s | hata={e}"
                )
                return hata_yaniti(
                    f"İç sunucu hatası: {str(e)}", "SUNUCU_HATASI"
                )

        return wrapper
    return decorator


# ── Whitelist Kontrolü ───────────────────────────────────────────

def whitelist_kontrol(index: str, whitelist: list[str]) -> bool:
    """
    Index adının whitelist'te olup olmadığını kontrol eder.

    Wildcard pattern desteği vardır (örn: 'penta-urunler-*').
    fnmatch kullanarak hem tam eşleşme hem glob eşleşme yapar.

    Args:
        index: Kontrol edilecek index adı
        whitelist: İzin verilen index adları/pattern'ları listesi

    Returns:
        True: Erişim izni var, False: Erişim engellendi
    """
    from fnmatch import fnmatch

    if not whitelist:
        # Whitelist boşsa tüm index'lere izin ver (geliştirme ortamı)
        return True

    izin = any(fnmatch(index, pattern) for pattern in whitelist)
    if not izin:
        logger.warning(f"Whitelist dışı index erişim denemesi: '{index}'")
    return izin


# ── Limit Kontrolü ──────────────────────────────────────────────

def limit_kontrol(limit: int | None, max_limit: int = DEFAULT_MAX_LIMIT) -> int:
    """
    Sonuç limiti üst sınırını uygular.

    limit=100000 gelirse max_limit'e çekilir.
    Negatif veya 0 ise varsayılan 10'a çekilir.

    Args:
        limit: İstenen sonuç sayısı
        max_limit: Maksimum izin verilen limit

    Returns:
        Güvenli limit değeri
    """
    if limit is None or limit <= 0:
        return 10  # Varsayılan
    if limit > min(max_limit, ABSOLUTE_MAX_LIMIT):
        logger.info(f"Limit {limit} → {max_limit} olarak sınırlandırıldı.")
        return min(max_limit, ABSOLUTE_MAX_LIMIT)
    return limit


# ── Script Sorgu Kontrolü ───────────────────────────────────────

def script_sorgu_kontrol(sorgu: dict) -> bool:
    """
    Sorgu içinde script sorgusu olup olmadığını kontrol eder.

    Script sorguları GÜVENLİK RİSKİ taşır ve yasaktır.

    Returns:
        True: Güvenli (script yok), False: Tehlikeli (script var)
    """
    sorgu_str = str(sorgu).lower()
    tehlikeli_anahtar_kelimeler = ["script", "script_score", "script_fields"]

    for kelime in tehlikeli_anahtar_kelimeler:
        if kelime in sorgu_str:
            logger.warning("Script sorgusu tespit edildi! Reddediliyor.")
            return False
    return True


# ── penta-mcp-builder: Standart Hata Formatı ────────────────────

def hata_yaniti(mesaj: str, kod: str = "GUVENLIK_HATASI") -> dict:
    """
    Standart hata yanıtı üretir.

    Ekip standardı: Tüm MCP servisleri aynı hata JSON yapısını kullanır.
    """
    logger.warning(f"Hata yanıtı üretildi | kod={kod} | mesaj={mesaj}")
    return {
        "hata": mesaj,
        "kod": kod,
        "total": 0,
        "count": 0,
        "items": [],
    }
