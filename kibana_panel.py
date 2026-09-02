"""
Penta Elasticsearch Görsel Yönetim Paneli (Kibana Alternatifi Web UI)
Port 5601 üzerinde çalışır ve product-price indeksini görselleştirir.
"""

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

# Proxy atlatma
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

ES_URL = "http://127.0.0.1:9200"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>Penta Elasticsearch Gözlem Paneli</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --primary: #3b82f6;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --success: #10b981;
      --accent: #8b5cf6;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 30px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 25px;
      padding-bottom: 15px;
      border-bottom: 1px solid var(--border);
    }
    .status-badge {
      background: #064e3b;
      color: #34d399;
      padding: 6px 14px;
      border-radius: 20px;
      font-weight: 600;
      font-size: 14px;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #34d399;
      box-shadow: 0 0 10px #34d399;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
    }
    .card-title { color: var(--text-muted); font-size: 14px; margin-bottom: 8px; }
    .card-value { font-size: 28px; font-weight: 700; color: #fff; }
    .table-container {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      margin-bottom: 30px;
    }
    table { width: 100%; border-collapse: collapse; text-align: left; }
    th {
      background: #111827;
      color: var(--text-muted);
      padding: 14px 18px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid var(--border);
    }
    td {
      padding: 14px 18px;
      border-bottom: 1px solid var(--border);
      font-size: 14px;
    }
    tr:hover { background: rgba(59, 130, 246, 0.05); }
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
    }
    .badge-marka { background: #312e81; color: #a5b4fc; }
    .badge-sarf { background: #4c1d95; color: #c4b5fd; }
    .badge-stok { background: #064e3b; color: #6ee7b7; }
    .price-usd { color: #38bdf8; font-weight: 700; }
    .price-tl { color: #facc15; font-weight: 600; font-size: 12px; margin-left: 6px; }
    pre {
      background: #090d16;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
      color: #38bdf8;
      font-size: 13px;
      overflow-x: auto;
      max-height: 400px;
    }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1 style="font-size: 24px;">📊 Penta Elasticsearch Panel (Kibana Görünümü)</h1>
      <p style="color: var(--text-muted); margin-top: 4px;">İndeks: <code style="color:#38bdf8">product-price</code> · Küme: <code style="color:#a78bfa">docker-cluster (ES 8.13.4)</code></p>
    </div>
    <div class="status-badge">
      <div class="status-dot"></div>
      Elasticsearch Bağlı & Aktif
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <div class="card-title">Toplam İndekslenen Ürün</div>
      <div class="card-value">{{TOTAL_COUNT}} Adet</div>
    </div>
    <div class="card">
      <div class="card-title">Aktif İndeks Adı</div>
      <div class="card-value" style="font-size: 22px; color: #38bdf8;">product-price</div>
    </div>
    <div class="card">
      <div class="card-title">Küme Durumu</div>
      <div class="card-value" style="color: #34d399; font-size: 22px;">🟢 Sağlıklı (Green)</div>
    </div>
    <div class="card">
      <div class="card-title">Elasticsearch Versiyonu</div>
      <div class="card-value" style="font-size: 22px; color: #a78bfa;">v8.13.4</div>
    </div>
  </div>

  <h2 style="margin-bottom: 15px; font-size: 18px;">📦 İndeksteki Ürün Kataloğu (Canlı Veri)</h2>
  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th>Ürün ID / Part No</th>
          <th>Ürün Adı</th>
          <th>Marka / Grup</th>
          <th>Toplam Stok</th>
          <th>Fiyat (USD / TL)</th>
          <th>Kategori</th>
        </tr>
      </thead>
      <tbody>
        {{TABLE_ROWS}}
      </tbody>
    </table>
  </div>

  <h2 style="margin-bottom: 15px; font-size: 18px;">📄 Ham Elasticsearch Mapping Şeması (JSON)</h2>
  <pre>{{RAW_MAPPING}}</pre>
</body>
</html>
"""


def fetch_es_data():
    req = urllib.request.Request(f"{ES_URL}/product-price/_search?size=50")
    with urllib.request.urlopen(req) as res:
        search_data = json.loads(res.read().decode())

    req_map = urllib.request.Request(f"{ES_URL}/product-price/_mapping")
    with urllib.request.urlopen(req_map) as res:
        mapping_data = json.loads(res.read().decode())

    return search_data, mapping_data


class ViewerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            search_data, mapping_data = fetch_es_data()
            hits = search_data.get("hits", {}).get("hits", [])
            total = len(hits)

            rows = []
            for h in hits:
                src = h.get("_source", {})
                prod = src.get("product", {})
                pid = prod.get("productID", h.get("_id", "-"))
                part = prod.get("producerPartNo", "-")
                name = prod.get("name", "-")
                brand = prod.get("exMaterialGroupValue", "-")
                group = prod.get("materialGroupValue", "-")
                stock = prod.get("totalstock", 0)
                usd = src.get("productUsdPrice", 0.0)
                try_p = src.get("productTryPrice", 0.0)
                cat = src.get("categoryLevel1Name", "-")

                rows.append(f"""
                <tr>
                  <td><strong>{pid}</strong><br><small style="color:#94a3b8">{part}</small></td>
                  <td><strong>{name}</strong></td>
                  <td><span class="badge badge-marka">{brand}</span> <span class="badge badge-sarf">{group}</span></td>
                  <td><span class="badge badge-stok">{stock} Adet</span></td>
                  <td><span class="price-usd">${usd:,.2f}</span><span class="price-tl">{try_p:,.2f} ₺</span></td>
                  <td style="color:#94a3b8">{cat}</td>
                </tr>
                """)

            html = HTML_TEMPLATE.replace("{{TOTAL_COUNT}}", str(total))
            html = html.replace("{{TABLE_ROWS}}", "\n".join(rows))
            html = html.replace("{{RAW_MAPPING}}", json.dumps(mapping_data, indent=2, ensure_ascii=False))

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"Hata: {e}".encode("utf-8"))

    def log_message(self, format, *args):
        return  # Sessiz log


def run():
    server = HTTPServer(("0.0.0.0", 5601), ViewerHandler)
    print("Kibana Paneli Başlatıldı: http://localhost:5601 (veya http://127.0.0.1:5601)")
    server.serve_forever()


if __name__ == "__main__":
    run()
