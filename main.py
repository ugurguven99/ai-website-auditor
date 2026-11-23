import argparse
import sys
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from src.crawler import SmartCrawler
from src.scraper import (
    fetch_page,
    parse_meta,
    parse_headings,
    parse_images,
    parse_content_stats,
    parse_links,
    extract_schema,
)
from src.ai_engine import analyze_with_ai
from src.utils import calculate_score, save_report, save_site_summary_report, get_risk_level
from src.report_generator import generate_html_report


def audit_website(
    target_url: str,
    max_pages: int = 3,
    max_depth: int = 2,
    output_format: str = "both",
    enable_ai: bool = True
):
    """
    Belirtilen hedef site için otomatik sitemap/BFS tarayıcıyı çalıştırır,
    keşfedilen sayfaları teknik SEO ve yapay zeka ile denetler,
    JSON ve modern HTML raporlarını üretir.
    """
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    parsed = urlparse(target_url)
    domain = parsed.netloc.lower().split(":")[0]

    print(f"\n{'='*75}")
    print(f"🕷️  [AI Website Auditor v2.0] Başlatılıyor: {target_url}")
    print(f"    Maksimum Sayfa : {max_pages}")
    print(f"    Maksimum Derinlik: {max_depth}")
    print(f"    Rapor Formatı   : {output_format.upper()}")
    print(f"    AI Katmanı (Gemini): {'Aktif' if enable_ai else 'Devre Dışı'}")
    print(f"{'='*75}")

    # 1. Sitemap & BFS Otomatik Sayfa Keşfi
    print("\n🔍 1. Adım: robots.txt, Sitemap ve iç bağlantılar taranıyor...")
    crawler = SmartCrawler(
        start_url=target_url,
        max_pages=max_pages,
        max_depth=max_depth
    )
    discovered_urls = crawler.discover_urls()

    if not discovered_urls:
        discovered_urls = [target_url]

    print(f"✅ Toplam {len(discovered_urls)} adet taranabilir sayfa keşfedildi:")
    for idx, u in enumerate(discovered_urls, start=1):
        print(f"   [{idx}] {u}")

    # 2. Keşfedilen Her Sayfa İçin Derinlemesine Denetim
    page_summaries = []
    first_page_ai_report = {}

    print(f"\n{'='*75}")
    print(f"🔬 2. Adım: Sayfaların Teknik ve Yapay Zeka Denetimi")
    print(f"{'='*75}")

    for idx, page_url in enumerate(discovered_urls, start=1):
        print(f"\n--- [{idx}/{len(discovered_urls)}] Denetleniyor: {page_url} ---")

        try:
            html, http_info = fetch_page(page_url)
            soup = BeautifulSoup(html, "html.parser")

            meta_data = parse_meta(soup)
            headings_data = parse_headings(soup)
            images_data = parse_images(soup)
            content_data = parse_content_stats(soup)
            links_data = parse_links(soup, page_url)
            schema_data = extract_schema(soup)

            site_data = {
                "url": page_url,
                "http_info": http_info,
                "meta": meta_data,
                "headings": headings_data,
                "images": images_data,
                "content_stats": content_data,
                "links": links_data,
                "schema": schema_data,
            }

            score_data = calculate_score(
                meta=meta_data,
                schema=schema_data,
                headings=headings_data,
                images=images_data,
                content_stats=content_data,
                http_info=http_info,
            )

            ai_report = {}
            if enable_ai:
                print("   🤖 Google Gemini AI risk analizi yapılıyor...")
                ai_report = analyze_with_ai(site_data)
                if idx == 1:
                    first_page_ai_report = ai_report

            page_file = ""
            if output_format in ("json", "both"):
                page_file = save_report(
                    page_url,
                    meta_data,
                    ai_report,
                    score_data,
                    extra_data=site_data
                )

            print(f"   • Skor        : {score_data['score']}/100 ({score_data['risk_level']})")
            print(f"   • Yanıt Süresi: {http_info['response_time_ms']} ms")
            print(f"   • H1 / Başlık : {headings_data['h1_count']} H1 / Toplam {headings_data['total_headings']} başlık")
            print(f"   • Görseller   : {images_data['total_images']} görsel ({images_data['missing_alt_count']} eksik alt)")
            if page_file:
                print(f"   • JSON Rapor  : {page_file}")

            page_summaries.append({
                "url": page_url,
                "score": score_data["score"],
                "risk_level": score_data["risk_level"],
                "response_time_ms": http_info["response_time_ms"],
                "technical_issues": score_data["technical_issues"],
                "report_file": page_file,
            })

        except Exception as e:
            print(f"   ❌ Sayfa denetlenirken hata oluştu: {e}")

    # 3. Toplu Raporlar (JSON & HTML)
    if page_summaries:
        scores = [p["score"] for p in page_summaries]
        avg_score = round(sum(scores) / len(scores), 1)
        risk_level = get_risk_level(avg_score)

        # En yaygın teknik sorunlar
        all_issues = []
        for p in page_summaries:
            all_issues.extend(p.get("technical_issues", []))

        issue_counts = {}
        for issue in all_issues:
            clean_issue = issue.split("(-")[0].strip()
            issue_counts[clean_issue] = issue_counts.get(clean_issue, 0) + 1

        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        common_issues_list = [{"issue": k, "frequency": v} for k, v in sorted_issues]

        summary_json_file = ""
        if output_format in ("json", "both"):
            summary_json_file = save_site_summary_report(domain, page_summaries)

        html_report_file = ""
        if output_format in ("html", "both"):
            all_ai_issues = []
            if first_page_ai_report:
                for k in ["meta_issues", "content_and_heading_issues", "image_issues", "security_and_technical_issues", "schema_issues"]:
                    all_ai_issues.extend(first_page_ai_report.get(k, []))

            html_report_file = generate_html_report(
                target_url=target_url,
                overall_score=int(avg_score),
                risk_level=risk_level,
                pages=page_summaries,
                common_issues=common_issues_list,
                ai_summary=first_page_ai_report.get("risk_summary", ""),
                detailed_issues=all_ai_issues
            )

        print(f"\n{'='*75}")
        print(f"🏆 SİTE GENELİ DENETİM SONUÇLARI: {domain}")
        print(f"{'='*75}")
        print(f"   • Taranan Sayfa Sayısı : {len(page_summaries)}")
        print(f"   • Ortalama SEO Skoru   : {avg_score}/100 ({risk_level})")
        print(f"   • Sayfa Skor Dağılımı  :")
        for p in page_summaries:
            print(f"     - [{p['score']}/100] ({p['risk_level']}) {p['url']}")

        if summary_json_file:
            print(f"\n📁 Toplu JSON Özeti: {summary_json_file}")
        if html_report_file:
            print(f"🌐 İnteraktif HTML Raporu: {html_report_file}")
        print(f"{'='*75}\n")


def build_parser():
    parser = argparse.ArgumentParser(
        description="AI Website Auditor: Yapay Zeka Destekli Teknik SEO ve Web Sitesi Denetim Aracı",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnek Kullanımlar:
  python main.py https://elgoog.im/
  python main.py https://elgoog.im/ --pages 5 --depth 2 --format html
  python main.py https://mrdoob.com/projects/chromeexperiments/google-gravity/ --pages 1
  python main.py https://elgoog.im/ --no-ai (Hızlı kural bazlı denetim)
        """
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="https://elgoog.im/",
        help="Denetlenecek web sitesi URL adresi (Varsayılan: https://elgoog.im/)"
    )
    parser.add_argument(
        "-p", "--pages",
        type=int,
        default=3,
        help="Sitede taranacak maksimum sayfa sayısı (Varsayılan: 3)"
    )
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=2,
        help="BFS iç bağlantı tarayıcısının maksimum derinliği (Varsayılan: 2)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["json", "html", "both"],
        default="both",
        help="Rapor çıktı formatı: 'json', 'html' veya 'both' (Varsayılan: both)"
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Yapay zeka analizini atlar, yalnızca kural bazlı hızlı teknik denetim yapar"
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    audit_website(
        target_url=args.url,
        max_pages=args.pages,
        max_depth=args.depth,
        output_format=args.format,
        enable_ai=not args.no_ai
    )


if __name__ == "__main__":
    main()
