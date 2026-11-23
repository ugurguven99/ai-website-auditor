import json
import os
from datetime import datetime
from urllib.parse import urlparse


def calculate_score(
    meta: dict,
    schema: list,
    headings: dict = None,
    images: dict = None,
    content_stats: dict = None,
    http_info: dict = None
) -> dict:
    """
    Teknik SEO, erişilebilirlik, içerik ve güvenlik kriterlerine dayalı
    100 üzerinden ağırlıklı puan ve risk analizi üretir.
    """
    headings = headings or {}
    images = images or {}
    content_stats = content_stats or {}
    http_info = http_info or {}

    score = 100
    issues = []

    # ---------------- 1. TITLE (15 Puan)
    title = meta.get("title", "")
    length = meta.get("title_length", len(title))
    if not title:
        score -= 15
        issues.append("Title etiketi eksik veya boş (-15)")
    else:
        if length < 30:
            score -= 5
            issues.append(f"Title çok kısa ({length} karakter, önerilen: 30-60) (-5)")
        elif length > 60:
            score -= 5
            issues.append(f"Title çok uzun ({length} karakter, SERP'te kesilebilir) (-5)")

    # ---------------- 2. DESCRIPTION (15 Puan)
    desc = meta.get("description", "")
    desc_len = meta.get("description_length", len(desc))
    if not desc:
        score -= 15
        issues.append("Meta description etiketi eksik (-15)")
    else:
        if desc_len < 70:
            score -= 5
            issues.append(f"Meta description çok kısa ({desc_len} karakter, önerilen: 70-160) (-5)")
        elif desc_len > 160:
            score -= 5
            issues.append(f"Meta description çok uzun ({desc_len} karakter) (-5)")

    # ---------------- 3. HEADINGS & İÇERİK (15 Puan)
    h1_count = headings.get("h1_count", 0)
    if "h1_count" in headings:
        if h1_count == 0:
            score -= 10
            issues.append("Sayfada hiç H1 başlığı bulunamadı (-10)")
        elif h1_count > 1:
            score -= 5
            issues.append(f"Birden fazla H1 başlığı tespit edildi (Toplam: {h1_count}) (-5)")

    hierarchy_issues = headings.get("hierarchy_issues", [])
    for issue in hierarchy_issues:
        if "Hiyerarşi atlaması" in issue:
            score -= 3
            issues.append(f"{issue} (-3)")
            break

    if content_stats.get("is_thin_content"):
        wc = content_stats.get("word_count", 0)
        score -= 5
        issues.append(f"Zayıf içerik (Thin content): Yalnızca {wc} kelime bulundu (-5)")

    # ---------------- 4. GÖRSEL VE ERİŞİLEBİLİRLİK (10 Puan)
    total_imgs = images.get("total_images", 0)
    missing_alt = images.get("missing_alt_count", 0)
    if total_imgs > 0 and missing_alt > 0:
        ratio = missing_alt / total_imgs
        if ratio >= 0.5:
            score -= 8
            issues.append(f"Görsellerin çoğunda alt etiketi eksik ({missing_alt}/{total_imgs} görsel) (-8)")
        else:
            score -= 4
            issues.append(f"Bazı görsellerde alt etiketi eksik ({missing_alt}/{total_imgs} görsel) (-4)")

    # ---------------- 5. CANONICAL VE İNDEKSLEME (15 Puan)
    if not meta.get("canonical"):
        score -= 10
        issues.append("Canonical URL tanımlanmamış (kopya içerik riski) (-10)")

    robots = meta.get("robots", "").lower()
    if "noindex" in robots:
        score -= 10
        issues.append("Robots etiketinde 'noindex' tespit edildi (indekslenmeyi engeller) (-10)")
    if "nofollow" in robots:
        score -= 5
        issues.append("Robots etiketinde 'nofollow' tespit edildi (-5)")

    # ---------------- 6. GÜVENLİK VE TEKNİK AĞ METRİKLERİ (10 Puan)
    if "is_https" in http_info and not http_info.get("is_https"):
        score -= 10
        issues.append("Sayfa HTTPS üzerinden sunulmuyor (-10)")

    resp_time = http_info.get("response_time_ms", 0)
    if resp_time > 1500:
        score -= 5
        issues.append(f"Yüksek sunucu yanıt süresi: {resp_time} ms (önerilen: <800ms) (-5)")

    sec_headers = http_info.get("security_headers", {})
    if sec_headers and not sec_headers.get("strict_transport_security"):
        score -= 3
        issues.append("HSTS (Strict-Transport-Security) güvenlik başlığı eksik (-3)")

    # ---------------- 7. OPEN GRAPH & TWITTER (10 Puan)
    og_data = meta.get("og_data", {})
    og_count = meta.get("og_count", len(og_data))
    if og_count == 0:
        score -= 6
        issues.append("Hiçbir Open Graph etiketi bulunamadı (-6)")
    else:
        essential_og = ["og:title", "og:image", "og:url"]
        missing_og = [tag for tag in essential_og if tag not in og_data]
        if missing_og:
            deduction = min(5, len(missing_og) * 2)
            score -= deduction
            issues.append(f"Kritik Open Graph etiketleri eksik: {', '.join(missing_og)} (-{deduction})")

    twitter_data = meta.get("twitter_data", {})
    twitter_count = meta.get("twitter_count", len(twitter_data))
    if twitter_count == 0:
        score -= 4
        issues.append("Twitter Card etiketleri bulunamadı (-4)")
    elif "twitter:card" not in twitter_data:
        score -= 2
        issues.append("'twitter:card' etiketi eksik (-2)")

    # ---------------- 8. STRUCTURED DATA / SCHEMA (10 Puan)
    if not schema:
        score -= 10
        issues.append("Yapılandırılmış veri (JSON-LD) bulunamadı (-10)")
    else:
        has_syntax_error = any(
            isinstance(s, dict) and s.get("parse_error") for s in schema
        )
        if has_syntax_error:
            score -= 5
            issues.append("JSON-LD yapısal verisinde sözdizimi hatası tespit edildi (-5)")

    # ---------------- 9. MOBİL VE KARAKTER KODLAMA (5 Puan)
    if not meta.get("viewport_exists"):
        score -= 3
        issues.append("Viewport etiketi eksik (mobil uyumluluk uyarısı) (-3)")
    if not meta.get("charset_exists"):
        score -= 2
        issues.append("Karakter seti (charset) etiketi eksik (-2)")

    score = max(0, min(100, score))

    return {
        "score": score,
        "risk_level": get_risk_level(score),
        "technical_issues": issues,
    }


def get_risk_level(score: int) -> str:
    """
    Sayısal skora göre risk derecesi döndürür.
    """
    if score >= 90:
        return "Low Risk"
    elif score >= 75:
        return "Moderate Risk"
    elif score >= 60:
        return "High Risk"
    return "Critical"


def save_report(
    target: str or dict,
    arg2: dict = None,
    arg3: dict = None,
    arg4: dict = None,
    filename: str = None,
    extra_data: dict = None
) -> str:
    """
    Teknik SEO denetim sonucunu JSON olarak kaydeder.
    """
    if isinstance(target, str):
        url = target
        meta = arg2 or {}
        ai_report = arg3 or {}
        score_data = arg4 or {}
    else:
        meta = target or {}
        ai_report = arg2 or {}
        score_data = arg3 or {}
        url = meta.get("canonical", "")

    os.makedirs(os.path.dirname(filename or "data/report.json"), exist_ok=True)

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_source = meta.get("canonical") or url or "site"
        parsed = urlparse(raw_source)
        clean_path = (parsed.netloc + parsed.path).strip("/").replace("/", "_")
        safe_name = "".join(c for c in clean_path if c.isalnum() or c in ("-", "_")) or "site"
        filename = f"data/report_{safe_name}_{timestamp}.json"

    report = {
        "url": url,
        "scanned_at": datetime.now().isoformat(),
        "meta": meta,
        "headings": extra_data.get("headings", {}) if extra_data else {},
        "images": extra_data.get("images", {}) if extra_data else {},
        "content_stats": extra_data.get("content_stats", {}) if extra_data else {},
        "http_info": extra_data.get("http_info", {}) if extra_data else {},
        "technical_audit": score_data,
        "ai_report": ai_report,
        "analysis_methodology": {
            "scraping": "requests + BeautifulSoup (Faz 2: Meta, Headings, Images, Network)",
            "meta_analysis": "Rule-based deterministic checks",
            "structured_data_check": "JSON-LD parsing and Schema.org validation",
            "scoring_model": "Weighted comprehensive scoring (0-100)",
            "ai_layer": "Google Gemini 2.5 (Structured Output with Pydantic)"
        }
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Report saved at {filename}")
    return filename


def save_site_summary_report(
    domain: str,
    page_audits: list[dict],
    filename: str = None
) -> str:
    """
    Çoklu sayfa taramasında tüm site için toplu özet raporu oluşturur.
    """
    os.makedirs(os.path.dirname(filename or "data/summary.json"), exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_domain = "".join(c for c in domain if c.isalnum() or c in ("-", "_")) or "site"
    if not filename:
        filename = f"data/summary_{safe_domain}_{timestamp}.json"

    scores = [p.get("score", 0) for p in page_audits if "score" in p]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    # En yaygın teknik sorunları topla
    all_issues = []
    for p in page_audits:
        all_issues.extend(p.get("technical_issues", []))

    issue_counts = {}
    for issue in all_issues:
        clean_issue = issue.split("(-")[0].strip()
        issue_counts[clean_issue] = issue_counts.get(clean_issue, 0) + 1

    sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)

    summary_data = {
        "domain": domain,
        "scanned_at": datetime.now().isoformat(),
        "total_pages_audited": len(page_audits),
        "average_score": avg_score,
        "overall_risk_level": get_risk_level(avg_score),
        "common_issues": [{"issue": k, "frequency": v} for k, v in sorted_issues],
        "pages": page_audits
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print(f"Site summary report saved at {filename}")
    return filename
