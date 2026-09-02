# Ürün Arama MCP — FastMCP Sunucusu (penta-mcp-builder standardı)

"""
MCP sunucusu — ince katman (thin layer).

Sorumluluklar:
- Tool tanımları
- İstek kabul
- İş mantığına yönlendirme
- Cevap dönüş

Ekip standardı: penta-mcp-builder desenleri uygulanır.
- @kapi_gerektirir decorator'ı ile yetki kontrolü
- Standart hata ve log formatları
- Stateless HTTP tasarımı

İş mantığı burada OLMAMALI — src/ modüllerine delege edilmeli.
"""

import logging

from dotenv import load_dotenv
from fastmcp import FastMCP

from config.settings import get_settings
from src.es_client import ESClient
from src.query_planner import sorgu_planla
from src.result_formatter import sonuclari_formatla
from src.schema_discovery import index_listele, index_semasi_getir
from src.security import (
    hata_yaniti,
    kapi_gerektirir,
    limit_kontrol,
    log_yapilandir,
    script_sorgu_kontrol,
    whitelist_kontrol,
)

# ── .env ve Log Yapılandırması ───────────────────────────────────

load_dotenv()  # .env dosyasından ortam değişkenlerini yükle
log_yapilandir()  # Ekip standardı log formatı

logger = logging.getLogger("mcp_server")

# ── Ayarlar ve bağlantılar ──────────────────────────────────────

settings = get_settings()
es = ESClient(settings)

# ── MCP Sunucusu ─────────────────────────────────────────────────

mcp = FastMCP(
    "Ürün Arama MCP",
    instructions="Elasticsearch üzerinde salt-okunur ürün arama aracı. "
                 "Index keşfi, şema analizi ve yapılandırılmış arama sağlar.",
)


# ── Tool Tanımları (penta-mcp-builder: @kapi_gerektirir) ────────

@mcp.tool()
@kapi_gerektirir(yetki_kodu="index_listeleme")
async def index_listele_tool() -> list[dict]:
    """
    Erişilebilir tüm Elasticsearch ürün kütüphanesi index'lerini listeler.

    Döndürdüğü bilgi: index adı, doküman sayısı, boyut, durum.
    Whitelist kontrolü uygulanır — sadece yetkili ürün index'leri döner.
    """
    logger.info("index_listele çağrıldı")
    return await index_listele(es, settings.index_whitelist)


@mcp.tool()
@kapi_gerektirir(yetki_kodu="sema_okuma")
async def index_semasi_getir_tool(index: str) -> dict:
    """
    Belirtilen ürün index'inin alan ve veri tip haritasını (mapping) döndürür.

    Satış Temsilcisi İpucu:
    Arama yapmadan önce alan isimlerini (örn: product.producerPartNo, productUsdPrice, product.totalstock)
    ve veri tiplerini öğrenmek için bu aracı kullanın.

    Args:
        index: Şeması istenen index adı (örn: 'product-price')

    Returns:
        Alan adları ve tiplerini içeren sadeleştirilmiş şema özeti
    """
    logger.info(f"index_semasi_getir çağrıldı: {index}")

    if not whitelist_kontrol(index, settings.index_whitelist):
        return hata_yaniti(f"'{index}' index'ine erişim izni yok.", "ERISIM_ENGELLENDI")

    return await index_semasi_getir(es, index, settings.index_whitelist)


@mcp.tool()
@kapi_gerektirir(yetki_kodu="urun_arama")
async def urun_ara_tool(
    index: str,
    filtreler: dict | None = None,
    serbest_metin: str | None = None,
    limit: int = 10,
) -> dict:
    """
    Kurumsal Elasticsearch kataloğunda ürün, stok, fiyat ve parça kodu araması yapar.

    Satış Temsilcileri ve Teams Botu Kullanım İpuçları:
    - Parça Kodu / Ürün Kodu araması için: serbest_metin='036K92300' veya '210229916'
    - Marka Filtresi için: filtreler={'product.exMaterialGroupValue': 'Xerox'} veya {'categoryLevel3Name': 'Dell'}
    - Stok Filtresi için: filtreler={'product.totalstock': {'gt': 0}}
    - Fiyat Aralığı araması için: filtreler={'productUsdPrice': {'gte': 100, 'lte': 500}}

    Args:
        index: Aranacak ürün index'i (örn: 'product-price')
        filtreler: Yapılandırılmış filtreler
        serbest_metin: Parça kodu, stok kodu veya serbest kelime araması
        limit: Döndürülecek sonuç sayısı (varsayılan: 10, maks: 50)

    Returns:
        Satış özetli (satis_ozeti) ve tam doküman içerikli sabit JSON şeması
    """
    logger.info(f"urun_ara çağrıldı: index={index}, filtreler={filtreler}, metin={serbest_metin}, limit={limit}")

    # Güvenlik kontrolleri
    if not whitelist_kontrol(index, settings.index_whitelist):
        return hata_yaniti(f"'{index}' index'ine erişim izni yok.", "ERISIM_ENGELLENDI")

    guvenli_limit = limit_kontrol(limit, settings.max_result_limit)

    # Şemayı al
    sema = await index_semasi_getir(es, index, settings.index_whitelist)
    if "hata" in sema:
        return hata_yaniti(sema["hata"], "SEMA_HATASI")

    # Sorgu planla
    sorgu_body = sorgu_planla(sema, filtreler, serbest_metin)

    # Script sorgu kontrolü
    if not script_sorgu_kontrol(sorgu_body):
        return hata_yaniti("Script sorguları güvenlik nedeniyle engellenmiştir.", "SCRIPT_YASAK")

    # Uyarıları çıkar (sorguya dahil edilmemeli)
    uyarilar = sorgu_body.pop("_uyarilar", None)

    # ES'e sorgu gönder
    try:
        es_yanit = await es.search(index=index, body=sorgu_body, size=guvenli_limit)
    except Exception as e:
        logger.error(f"ES arama hatası: {e}")
        return hata_yaniti(f"Elasticsearch'e erişilemedi: {str(e)}", "ES_HATASI")

    # Sonuçları formatla
    sonuc = sonuclari_formatla(es_yanit, index, filtreler, serbest_metin)

    # Uyarıları ekle
    if uyarilar:
        sonuc["uyarilar"] = uyarilar

    return sonuc



# ── Health Check ─────────────────────────────────────────────────

@mcp.tool()
@kapi_gerektirir(yetki_kodu="health_check")
async def health_check() -> dict:
    """Sunucu sağlık kontrolü. ES bağlantısını test eder."""
    try:
        client = await es.get_client()
        info = await client.info()
        return {
            "durum": "sağlıklı",
            "es_cluster": info.get("cluster_name", "bilinmiyor"),
            "es_versiyon": info.get("version", {}).get("number", "bilinmiyor"),
        }
    except Exception as e:
        return {
            "durum": "sağlıksız",
            "hata": str(e),
        }


# ── Sunucu Başlatma ─────────────────────────────────────────────

if __name__ == "__main__":
    logger.info(f"MCP Sunucusu SSE protokolü ile başlatılıyor: {settings.mcp_host}:{settings.mcp_port}")
    mcp.run(transport="sse", host=settings.mcp_host, port=settings.mcp_port)

