import os
from datetime import datetime
from jinja2 import Template


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Teknik SEO & AI Denetim Raporu - {{ domain }}</title>
  <style>
    :root {
      --bg-primary: #0f172a;
      --bg-card: #1e293b;
      --bg-subtle: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --border: #334155;
      --accent: #3b82f6;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: var(--bg-primary);
      color: var(--text-main);
      line-height: 1.6;
      padding: 2rem 1rem;
    }
    .container { max-width: 1100px; margin: 0 auto; }
    
    /* Header */
    .header {
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      border: 1px solid var(--border);
      border-radius: 1rem;
      padding: 2rem;
      margin-bottom: 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1.5rem;
    }
    .header h1 { font-size: 1.8rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }
    .header p { color: var(--text-muted); font-size: 0.95rem; }
    .header-badge {
      display: inline-block;
      padding: 0.25rem 0.75rem;
      background: var(--bg-subtle);
      border-radius: 9999px;
      font-size: 0.85rem;
      margin-top: 0.5rem;
      color: #38bdf8;
    }
    
    /* Score Box */
    .score-badge-large {
      text-align: center;
      padding: 1.25rem 2rem;
      border-radius: 1rem;
      background: rgba(15, 23, 42, 0.6);
      border: 2px solid;
    }
    .score-badge-large .score-num { font-size: 2.75rem; font-weight: 800; line-height: 1; }
    .score-badge-large .score-label { font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-top: 0.25rem; }

    .score-low-risk { border-color: var(--success); color: var(--success); }
    .score-moderate-risk { border-color: var(--accent); color: var(--accent); }
    .score-high-risk { border-color: var(--warning); color: var(--warning); }
    .score-critical { border-color: var(--danger); color: var(--danger); }

    /* Metric Grid */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }
    .metric-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 0.75rem;
      padding: 1.25rem;
    }
    .metric-title { font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600; margin-bottom: 0.5rem; }
    .metric-val { font-size: 1.4rem; font-weight: 700; color: #fff; }
    .metric-sub { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem; }

    /* AI Box */
    .ai-box {
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%);
      border: 1px solid rgba(59, 130, 246, 0.3);
      border-radius: 0.75rem;
      padding: 1.5rem;
      margin-bottom: 2rem;
    }
    .ai-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; font-weight: 700; color: #60a5fa; }
    .ai-text { font-size: 0.95rem; line-height: 1.7; color: #e2e8f0; }

    /* Section Cards */
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 0.75rem;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }
    .card-title {
      font-size: 1.2rem;
      font-weight: 700;
      margin-bottom: 1rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    /* Issue list */
    .issue-item {
      background: var(--bg-primary);
      border: 1px solid var(--border);
      border-radius: 0.5rem;
      padding: 1rem;
      margin-bottom: 0.75rem;
    }
    .issue-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
    .issue-title { font-weight: 600; font-size: 1rem; color: #fff; }
    .badge {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
    }
    .badge-high { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid #ef4444; }
    .badge-medium { background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid #f59e0b; }
    .badge-low { background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid #3b82f6; }

    .issue-desc { font-size: 0.9rem; color: #cbd5e1; margin-bottom: 0.5rem; }
    .recommendation-box {
      background: rgba(30, 41, 59, 0.8);
      border-left: 3px solid #3b82f6;
      padding: 0.6rem 0.8rem;
      border-radius: 0.25rem;
      font-size: 0.85rem;
      color: #93c5fd;
    }
    .recommendation-box strong { color: #fff; }

    /* Multi-page table */
    .pages-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
    .pages-table th, .pages-table td {
      padding: 0.75rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
      font-size: 0.9rem;
    }
    .pages-table th { background: var(--bg-subtle); color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; }
    .pages-table tr:hover { background: rgba(51, 65, 85, 0.3); }

    /* Footer */
    .footer { text-align: center; color: var(--text-muted); font-size: 0.85rem; margin-top: 3rem; }
  </style>
</head>
<body>
  <div class="container">
    
    <!-- Header -->
    <div class="header">
      <div>
        <h1>🔍 Teknik SEO & AI Denetim Raporu</h1>
        <p><strong>Hedef:</strong> {{ target_url }}</p>
        <span class="header-badge">Tarih: {{ scanned_at }}</span>
      </div>
      <div class="score-badge-large {{ score_class }}">
        <div class="score-num">{{ overall_score }}</div>
        <div class="score-label">{{ risk_level }}</div>
      </div>
    </div>

    <!-- AI Executive Summary -->
    {% if ai_summary %}
    <div class="ai-box">
      <div class="ai-header">
        <span>🤖</span>
        <span>Google Gemini Yapay Zeka Risk Özeti</span>
      </div>
      <div class="ai-text">{{ ai_summary }}</div>
    </div>
    {% endif %}

    <!-- Key Metrics Grid -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-title">Ortalama Skor</div>
        <div class="metric-val">{{ overall_score }}/100</div>
        <div class="metric-sub">{{ risk_level }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-title">Taranan Sayfa</div>
        <div class="metric-val">{{ pages|length }}</div>
        <div class="metric-sub">Otomatik Sitemap / BFS</div>
      </div>
      <div class="metric-card">
        <div class="metric-title">Ortalama Yanıt</div>
        <div class="metric-val">{{ avg_response_time }} ms</div>
        <div class="metric-sub">Sunucu İlk Bayt Süresi</div>
      </div>
      <div class="metric-card">
        <div class="metric-title">Tespit Edilen Sorun</div>
        <div class="metric-val">{{ total_issues }}</div>
        <div class="metric-sub">Kural & AI Kontrolleri</div>
      </div>
    </div>

    <!-- Taranan Sayfalar Listesi -->
    <div class="card">
      <div class="card-title">
        <span>📄 Taranan Sayfalar & Skor Tablosu</span>
        <span style="font-size: 0.85rem; color: var(--text-muted);">{{ pages|length }} Sayfa</span>
      </div>
      <table class="pages-table">
        <thead>
          <tr>
            <th>Sayfa URL</th>
            <th>SEO Skoru</th>
            <th>Risk Derecesi</th>
            <th>Yanıt Süresi</th>
            <th>Sorun Sayısı</th>
          </tr>
        </thead>
        <tbody>
          {% for p in pages %}
          <tr>
            <td><a href="{{ p.url }}" target="_blank" style="color: #60a5fa; text-decoration: none;">{{ p.url }}</a></td>
            <td><strong>{{ p.score }}/100</strong></td>
            <td>{{ p.risk_level }}</td>
            <td>{{ p.response_time_ms }} ms</td>
            <td>{{ p.technical_issues|length }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- Sık Tekrarlanan Teknik Sorunlar -->
    {% if common_issues %}
    <div class="card">
      <div class="card-title">
        <span>⚠️ Site Genelinde En Çok Tekrarlanan Sorunlar</span>
      </div>
      {% for item in common_issues %}
      <div class="issue-item">
        <div class="issue-header">
          <span class="issue-title">{{ item.issue }}</span>
          <span class="badge badge-medium">{{ item.frequency }} Sayfada Tespit Edildi</span>
        </div>
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <!-- Detaylı Yapay Zeka ve Teknik Sorunlar (İlk sayfa / Ana sayfa bazlı) -->
    {% if detailed_issues %}
    <div class="card">
      <div class="card-title">
        <span>🛠️ Detaylı Teknik & AI Bulguları ve Düzeltme Önerileri</span>
      </div>
      {% for issue in detailed_issues %}
      <div class="issue-item">
        <div class="issue-header">
          <span class="issue-title">{{ issue.title or issue }}</span>
          <span class="badge badge-{{ issue.risk_level or 'medium' }}">{{ issue.risk_level or 'Risk' }}</span>
        </div>
        {% if issue.description %}
        <p class="issue-desc">{{ issue.description }}</p>
        {% endif %}
        {% if issue.recommendation %}
        <div class="recommendation-box">
          <strong>💡 Çözüm Önerisi:</strong> {{ issue.recommendation }}
        </div>
        {% endif %}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <div class="footer">
      <p>Rapor AI Website Auditor v2.0 tarafından oluşturuldu. • Güçlendirici: Google Gemini & Python BeautifulSoup Engine</p>
    </div>

  </div>
</body>
</html>
"""


def generate_html_report(
    target_url: str,
    overall_score: int,
    risk_level: str,
    pages: list[dict],
    common_issues: list[dict],
    ai_summary: str = "",
    detailed_issues: list[dict] = None,
    output_filename: str = None
) -> str:
    """
    Jinja2 şablonu kullanarak modern, bağımsız bir HTML denetim raporu üretir.
    """
    detailed_issues = detailed_issues or []
    
    # Skor renk sınıfı belirleme
    score_class = "score-critical"
    if overall_score >= 90:
        score_class = "score-low-risk"
    elif overall_score >= 75:
        score_class = "score-moderate-risk"
    elif overall_score >= 60:
        score_class = "score-high-risk"

    # Ortalama yanıt süresi ve toplam sorun sayısı
    response_times = [p.get("response_time_ms", 0) for p in pages if "response_time_ms" in p]
    avg_resp = round(sum(response_times) / len(response_times), 1) if response_times else 0

    total_issues = sum(len(p.get("technical_issues", [])) for p in pages)

    template = Template(HTML_TEMPLATE)
    rendered_html = template.render(
        target_url=target_url,
        domain=target_url.replace("https://", "").replace("http://", "").split("/")[0],
        scanned_at=datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        overall_score=overall_score,
        risk_level=risk_level,
        score_class=score_class,
        pages=pages,
        common_issues=common_issues,
        ai_summary=ai_summary,
        detailed_issues=detailed_issues,
        avg_response_time=avg_resp,
        total_issues=total_issues,
    )

    if not output_filename:
        os.makedirs("data", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_domain = "".join(c for c in target_url.split("/")[2] if c.isalnum() or c in ("-", "_"))
        output_filename = f"data/report_{safe_domain}_{timestamp}.html"

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    print(f"HTML Report generated at: {output_filename}")
    return output_filename
