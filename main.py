# Ürün Arama MCP — Komuta Merkezi (Control Center)

"""
Penta Ürün Arama MCP Komuta Merkezi.

Tüm sistemi tek noktadan yönetmenizi sağlar:
1. Elasticsearch & Kibana (Docker)
2. FastMCP Sunucusu (Streamable HTTP, Port 8008)
3. Cloudflare Tüneli (Copilot Studio Entegrasyonu)
4. Sentetik Veri Yükleme (Seed Data)

Kullanım:
    python main.py           -> İnteraktif Menü
    python main.py start     -> Tüm sistemi başlatır
    python main.py stop      -> Tüm sistemi kapatır
    python main.py status    -> Canlı servis durumunu gösterir
    python main.py seed      -> Sentetik ürün verilerini yükler
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Windows UTF-8 konsol desteği
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Windows localhost proxy atlatma
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

BASE_DIR = Path(__file__).resolve().parent
PID_FILE = BASE_DIR / ".system_pids.json"
MOCK_DIR = BASE_DIR / "mock_environment"
DOCKER_COMPOSE_FILE = MOCK_DIR / "docker-compose.yml"
TUNNEL_LOG = BASE_DIR / ".tunnel_current.log"
MCP_LOG = BASE_DIR / ".mcp_server.log"


# ── Renkli Konsol Çıktıları ──────────────────────────────────────
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════╗
║              🎛️  PENTA ÜRÜN ARAMA MCP KOMUTA MERKEZİ            ║
║          Elasticsearch • Kibana • FastMCP • Cloudflare           ║
╚══════════════════════════════════════════════════════════════════╝{Colors.END}"""
    print(banner)


# ── PID Yönetimi ────────────────────────────────────────────────
def load_pids() -> dict:
    if PID_FILE.exists():
        try:
            return json.loads(PID_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_pids(pids: dict):
    PID_FILE.write_text(json.dumps(pids, indent=2), encoding="utf-8")


def is_pid_running(pid: int) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        # Windows tasklist kontrolü
        out = subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True, text=True, stderr=subprocess.DEVNULL)
        return str(pid) in out
    except Exception:
        return False


def is_cloudflared_running() -> bool:
    try:
        cmd = 'tasklist /FI "IMAGENAME eq cloudflared.exe"'
        out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
        return "cloudflared.exe" in out
    except Exception:
        return False


def kill_pid(pid: int):
    if pid and is_pid_running(pid):
        try:
            subprocess.run(
                f"taskkill /F /T /PID {pid}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


# ── Sağlık Kontrolleri ──────────────────────────────────────────
def check_http(url: str, timeout: float = 2.0) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ControlCenter/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 400, 406)  # MCP 400/406 dönse bile ayaktadır
    except urllib.error.HTTPError as e:
        return e.code in (200, 400, 406)
    except Exception:
        return False


def get_tunnel_url_from_log() -> str | None:
    if not TUNNEL_LOG.exists():
        return None
    try:
        content = TUNNEL_LOG.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
        if match:
            return match.group(0)
    except Exception:
        pass
    return None


# ── Servis Yönetim Fonksiyonları ─────────────────────────────────


def start_docker():
    print(f"\n{Colors.BLUE}📦 [1/4] Docker Konteynerleri Kontrol Ediliyor...{Colors.END}")
    cmd = f'docker compose -f "{DOCKER_COMPOSE_FILE}" up -d'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"  {Colors.GREEN}✓ Elasticsearch ve Kibana konteynerleri başlatıldı.{Colors.END}")
    else:
        print(f"  {Colors.YELLOW}⚠ Docker uyarısı:{Colors.END} {res.stderr.strip()}")

    # ES hazır olana kadar kısa bekleme
    print("  ⏳ Elasticsearch sağlık kontrolü bekleniyor...", end="", flush=True)
    for _ in range(15):
        if check_http("http://127.0.0.1:9200"):
            print(f" {Colors.GREEN}SAĞLIKLI!{Colors.END}")
            return True
        time.sleep(1)
        print(".", end="", flush=True)
    print(f" {Colors.YELLOW}(Devam ediliyor...){Colors.END}")
    return False


def seed_mock_data():
    print(f"\n{Colors.BLUE}🌱 20.000 Benzersiz Sentetik Ürün Verisi Yükleniyor...{Colors.END}")
    cmd = f'uv run python "{MOCK_DIR / "generate_20k_products.py"}"'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"  {Colors.GREEN}✓ 20.000 adet ürün 'product-price' indeksine başarıyla yüklendi.{Colors.END}")
    else:
        print(f"  {Colors.RED}✗ Mock veri yüklenemedi:{Colors.END} {res.stderr.strip() or res.stdout.strip()}")


WIN_DETACHED = 0x00000008 | 0x00000200 if sys.platform == "win32" else 0


def start_mcp_server(pids: dict):
    print(f"\n{Colors.BLUE}⚡ [2/4] FastMCP Sunucusu Başlatılıyor (Port 8008)...{Colors.END}")
    if check_http("http://127.0.0.1:8008/"):
        print(f"  {Colors.YELLOW}ℹ FastMCP sunucusu zaten çalışıyor ve yanıt veriyor.{Colors.END}")
        return

    mcp_script = BASE_DIR / "mcp_server.py"
    mcp_log_file = open(MCP_LOG, "a", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(mcp_script)],
        stdout=mcp_log_file,
        stderr=subprocess.STDOUT,
        creationflags=WIN_DETACHED,
    )
    pids["mcp_server"] = proc.pid
    save_pids(pids)

    # Hazır olmasını bekle
    print("  ⏳ FastMCP hazır olması bekleniyor...", end="", flush=True)
    for _ in range(15):
        if check_http("http://127.0.0.1:8008/"):
            print(f" {Colors.GREEN}AKTİF! (PID: {proc.pid}){Colors.END}")
            return
        time.sleep(1)
        print(".", end="", flush=True)
    print(f" {Colors.GREEN}Başlatıldı (PID: {proc.pid}){Colors.END}")


def start_cloudflare_tunnel(pids: dict) -> str | None:
    print(f"\n{Colors.BLUE}🌐 [3/4] Cloudflare HTTPS Tüneli Başlatılıyor...{Colors.END}")

    # Eski tüm zombi cloudflared süreçlerini kesinlikle öldür (port çakışmasını önler)
    subprocess.run(
        "taskkill /F /IM cloudflared.exe",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Eski logu temizle
    if TUNNEL_LOG.exists():
        try:
            TUNNEL_LOG.unlink()
        except Exception:
            pass

    tunnel_cmd = ["cloudflared", "tunnel", "--url", "http://127.0.0.1:8008"]
    log_file = open(TUNNEL_LOG, "a", encoding="utf-8")
    proc = subprocess.Popen(
        tunnel_cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=WIN_DETACHED,
    )
    pids["cloudflare_tunnel"] = proc.pid
    save_pids(pids)

    print("  ⏳ Public HTTPS URL alınıyor...", end="", flush=True)
    tunnel_url = None
    for _ in range(20):
        tunnel_url = get_tunnel_url_from_log()
        if tunnel_url:
            break
        time.sleep(1)
        print(".", end="", flush=True)

    if not tunnel_url:
        print(f" {Colors.RED}URL alınamadı!{Colors.END}")
        return None

    # Tünelin Cloudflare edge sunucularında aktifleşmesini bekle
    print(f" {Colors.GREEN}Alındı: {tunnel_url}{Colors.END}")
    print("  ⏳ Cloudflare ağ doğrulaması yapılıyor...", end="", flush=True)
    for _ in range(15):
        if check_http(f"{tunnel_url}/"):
            print(f" {Colors.GREEN}DOĞRULANDI & CANLI!{Colors.END}")
            return tunnel_url
        time.sleep(1)
        print(".", end="", flush=True)

    print(f" {Colors.GREEN}Yayında!{Colors.END}")
    return tunnel_url


def stop_all(pids: dict, stop_docker: bool = False):
    print(f"\n{Colors.YELLOW}🛑 Sistem Bileşenleri Durduruluyor...{Colors.END}")

    # 1. Cloudflared durdur
    tunnel_pid = pids.get("cloudflare_tunnel")
    if tunnel_pid:
        kill_pid(tunnel_pid)
        print(f"  {Colors.GREEN}✓ Cloudflare tüneli kapatıldı.{Colors.END}")
        pids.pop("cloudflare_tunnel", None)

    # 2. FastMCP durdur
    mcp_pid = pids.get("mcp_server")
    if mcp_pid:
        kill_pid(mcp_pid)
        print(f"  {Colors.GREEN}✓ FastMCP sunucusu kapatıldı.{Colors.END}")
        pids.pop("mcp_server", None)

    # Ekstra port 8008 temizliği
    port_kill_cmd = "for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :8008') do taskkill /F /PID %a"
    subprocess.run(port_kill_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 3. Docker (İsteğe bağlı)
    if stop_docker:
        print("  ⏳ Docker konteynerleri durduruluyor...")
        down_cmd = f'docker compose -f "{DOCKER_COMPOSE_FILE}" down'
        subprocess.run(down_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  {Colors.GREEN}✓ Elasticsearch ve Kibana konteynerleri durduruldu.{Colors.END}")

    save_pids(pids)
    print(f"{Colors.GREEN}✅ Tüm servisler güvenli şekilde durduruldu.{Colors.END}\n")


def show_status(pids: dict):
    print(f"\n{Colors.BOLD}📊 CANLI SİSTEM DURUM RAPORU:{Colors.END}")
    print("─" * 66)

    # ES
    es_ok = check_http("http://127.0.0.1:9200")
    es_status = f"{Colors.GREEN}🟢 ÇALIŞIYOR (Healthy){Colors.END}" if es_ok else f"{Colors.RED}🔴 KAPALI{Colors.END}"
    print(f" • Elasticsearch (9200) : {es_status}")

    # Kibana
    kibana_ok = check_http("http://localhost:5601")
    kibana_status = (
        f"{Colors.GREEN}🟢 ÇALIŞIYOR (http://localhost:5601){Colors.END}"
        if kibana_ok
        else f"{Colors.RED}🔴 KAPALI{Colors.END}"
    )
    print(f" • Kibana Web UI (5601)  : {kibana_status}")

    # FastMCP
    mcp_ok = check_http("http://127.0.0.1:8008/mcp")
    mcp_pid = pids.get("mcp_server")
    mcp_status = (
        f"{Colors.GREEN}🟢 ÇALIŞIYOR (Port 8008/mcp - PID: {mcp_pid}){Colors.END}"
        if mcp_ok
        else f"{Colors.RED}🔴 KAPALI{Colors.END}"
    )
    print(f" • FastMCP Sunucu       : {mcp_status}")

    # Tunnel
    tunnel_url = get_tunnel_url_from_log()
    tunnel_pid = pids.get("cloudflare_tunnel")
    if tunnel_url and (is_cloudflared_running() or is_pid_running(tunnel_pid)):
        tunnel_status = (
            f"{Colors.GREEN}🟢 AKTİF{Colors.END}\n   👉 {Colors.BOLD}{Colors.CYAN}{tunnel_url}/mcp{Colors.END}"
        )
    else:
        tunnel_status = f"{Colors.RED}🔴 KAPALI{Colors.END}"
    print(f" • Cloudflare Tüneli    : {tunnel_status}")
    print("─" * 66)


def print_copilot_banner(tunnel_url: str):
    mcp_url = f"{tunnel_url}/mcp"
    print(f"""
{Colors.GREEN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════════╗
║                   🎉 TÜM SİSTEM HAZIR & YAYINDA!                 ║
╚══════════════════════════════════════════════════════════════════╝{Colors.END}

{Colors.BOLD}Copilot Studio'ya Eklenecek Güncel MCP URL:{Colors.END}
{Colors.CYAN}{Colors.BOLD}👉  {mcp_url}  👈{Colors.END}

{Colors.YELLOW}Not: Copilot Studio'da 'Araçlar (+)' -> 'Model Context Protocol'{Colors.END}
{Colors.YELLOW}seçip bu adresi yapıştırmanız yeterlidir.{Colors.END}
""")


def start_all():
    pids = load_pids()
    start_docker()
    start_mcp_server(pids)
    tunnel_url = start_cloudflare_tunnel(pids)
    if tunnel_url:
        print_copilot_banner(tunnel_url)
    else:
        print(f"\n{Colors.YELLOW}⚠ Tünel başlatıldı. URL için 'status' çalıştırın.{Colors.END}")

    # Windows Job Object temizliğini engellemek için canlı tutma döngüsü
    print(f"{Colors.GREEN}💡 Sistem şu anda arka planda CANLI çalışıyor.{Colors.END}")
    print(f"{Colors.YELLOW}Durdurmak için Ctrl+C tuşlarına basabilirsiniz.{Colors.END}\n")
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Durdurma sinyali alındı...{Colors.END}")
        stop_all(pids, stop_docker=False)


# ── Ana İnteraktif Menü & CLI ────────────────────────────────────
def main():
    pids = load_pids()

    # CLI Argüman Desteği
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("start", "up", "run"):
            start_all()
        elif arg in ("stop", "down", "kill"):
            stop_all(pids, stop_docker=True)
        elif arg in ("stop-soft",):
            stop_all(pids, stop_docker=False)
        elif arg in ("status", "info"):
            show_status(pids)
        elif arg in ("seed", "mock"):
            seed_mock_data()
        elif arg in ("tunnel", "url"):
            url = get_tunnel_url_from_log()
            if url:
                print(f"\n{Colors.GREEN}Aktif Tünel URL:{Colors.END} {Colors.BOLD}{url}/mcp{Colors.END}")
            else:
                print(f"\n{Colors.RED}Aktif tünel bulunamadı.{Colors.END}")
        else:
            print(f"Bilinmeyen komut: {arg}. Seçenekler: start | stop | status | seed | tunnel")
        return

    # İnteraktif Döngü
    while True:
        print_banner()
        show_status(pids)
        print(f"""
{Colors.BOLD}Seçenekler:{Colors.END}
 [{Colors.GREEN}1{Colors.END}] 🚀 Tüm Sistemi Başlat (ES + Kibana + FastMCP + Tünel)
 [{Colors.YELLOW}2{Colors.END}] 🛑 Uygulama Servislerini Durdur (MCP + Tünel Kapat)
 [{Colors.RED}3{Colors.END}] 💥 Tüm Sistemi Tamamen Durdur (Docker Dahil Her Şeyi Kapat)
 [{Colors.CYAN}4{Colors.END}] 🌱 Mock Ürün Verilerini Tekrar Yükle (Seed Data)
 [{Colors.BLUE}5{Colors.END}] 🔄 Durumu Yenile (Refresh Status)
 [{Colors.BOLD}0{Colors.END}] 🚪 Çıkış
""")
        secim = input(f"{Colors.BOLD}Seçiminiz [0-5]: {Colors.END}").strip()

        if secim == "1":
            start_all()
            input(f"\n{Colors.BOLD}Menüye dönmek için [Enter] tuşuna basın...{Colors.END}")
        elif secim == "2":
            stop_all(pids, stop_docker=False)
            input(f"\n{Colors.BOLD}Menüye dönmek için [Enter] tuşuna basın...{Colors.END}")
        elif secim == "3":
            stop_all(pids, stop_docker=True)
            input(f"\n{Colors.BOLD}Menüye dönmek için [Enter] tuşuna basın...{Colors.END}")
        elif secim == "4":
            seed_mock_data()
            input(f"\n{Colors.BOLD}Menüye dönmek için [Enter] tuşuna basın...{Colors.END}")
        elif secim == "5":
            continue
        elif secim == "0":
            print(f"\n{Colors.CYAN}Görüşmek üzere! Servisler arka planda çalışmaya devam eder.{Colors.END}")
            break
        else:
            print(f"{Colors.RED}Geçersiz seçim!{Colors.END}")
            time.sleep(1)


if __name__ == "__main__":
    main()
