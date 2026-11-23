import json
import re
from urllib.parse import urlparse, urljoin
import requests
import httpx
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
}


def fetch_page(url: str, timeout: int = 15) -> tuple[str, dict]:
    """
    Belirtilen URL'deki web sayfasını senkron olarak çeker.
    HTML içeriği ve HTTP ağ seviyesi metriklerini döndürür.
    """
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()

    resp_headers = {k.lower(): v for k, v in response.headers.items()}

    http_info = {
        "status_code": response.status_code,
        "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
        "final_url": response.url,
        "is_https": response.url.startswith("https://"),
        "is_redirected": len(response.history) > 0,
        "redirect_count": len(response.history),
        "security_headers": {
            "strict_transport_security": "strict-transport-security" in resp_headers,
            "x_content_type_options": "x-content-type-options" in resp_headers,
            "content_security_policy": "content-security-policy" in resp_headers,
            "x_frame_options": "x-frame-options" in resp_headers,
        },
    }

    return response.text, http_info


async def async_fetch_page(client: httpx.AsyncClient, url: str) -> tuple[str, dict]:
    """
    Belirtilen URL'deki web sayfasını asenkron olarak çeker.
    Çoklu sayfa taramalarında eşzamanlı (concurrent) hız sağlar.
    """
    response = await client.get(url, headers=DEFAULT_HEADERS, follow_redirects=True)
    response.raise_for_status()

    resp_headers = {k.lower(): v for k, v in response.headers.items()}

    http_info = {
        "status_code": response.status_code,
        "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
        "final_url": str(response.url),
        "is_https": str(response.url).startswith("https://"),
        "is_redirected": len(response.history) > 0,
        "redirect_count": len(response.history),
        "security_headers": {
            "strict_transport_security": "strict-transport-security" in resp_headers,
            "x_content_type_options": "x-content-type-options" in resp_headers,
            "content_security_policy": "content-security-policy" in resp_headers,
            "x_frame_options": "x-frame-options" in resp_headers,
        },
    }

    return response.text, http_info


def parse_meta(soup: BeautifulSoup) -> dict:
    """
    HTML içindeki temel ve sosyal medya (OG, Twitter) meta etiketlerini ayıklar.
    """
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.title:
        title = soup.title.get_text().strip()

    desc_tag = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "description"})
    canonical_tag = soup.find("link", attrs={"rel": lambda x: x and "canonical" in x.lower()})
    robots_tag = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "robots"})
    viewport_tag = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "viewport"})
    charset_tag = soup.find("meta", charset=True) or soup.find(
        "meta", attrs={"http-equiv": lambda x: x and "content-type" in x.lower()}
    )

    description = desc_tag.get("content", "").strip() if desc_tag else ""
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""
    robots = robots_tag.get("content", "").strip() if robots_tag else ""

    og_data = {}
    for tag in soup.find_all("meta", property=lambda x: x and x.lower().startswith("og:")):
        prop = tag.get("property", "").strip()
        content = tag.get("content", "").strip()
        if prop and content:
            og_data[prop] = content

    twitter_data = {}
    for tag in soup.find_all(
        "meta",
        attrs={
            "name": lambda x: x and x.lower().startswith("twitter:"),
            "property": lambda x: x and x.lower().startswith("twitter:"),
        },
    ):
        name = (tag.get("name") or tag.get("property") or "").strip()
        content = tag.get("content", "").strip()
        if name and content:
            twitter_data[name] = content

    return {
        "title": title,
        "title_length": len(title),
        "description": description,
        "description_length": len(description),
        "canonical": canonical,
        "robots": robots,
        "viewport_exists": bool(viewport_tag),
        "charset_exists": bool(charset_tag),
        "og_data": og_data,
        "og_count": len(og_data),
        "twitter_data": twitter_data,
        "twitter_count": len(twitter_data),
    }


def parse_headings(soup: BeautifulSoup) -> dict:
    """
    Sayfadaki H1-H6 başlık yapısını ve hiyerarşik sıralamasını denetler.
    """
    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]
    h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3") if h.get_text(strip=True)]

    heading_elements = soup.find_all(re.compile(r"^h[1-6]$", re.IGNORECASE))
    hierarchy_order = [int(el.name[1]) for el in heading_elements]

    hierarchy_issues = []
    if len(h1_tags) == 0:
        hierarchy_issues.append("Sayfada hiç H1 başlığı bulunamadı")
    elif len(h1_tags) > 1:
        hierarchy_issues.append(f"Birden fazla H1 başlığı tespit edildi (Toplam: {len(h1_tags)})")

    # Hiyerarşi atlaması kontrolü (Örn: H1'den sonra H2 olmadan H3 gelmesi)
    for i in range(len(hierarchy_order) - 1):
        current_level = hierarchy_order[i]
        next_level = hierarchy_order[i + 1]
        if next_level > current_level + 1:
            hierarchy_issues.append(f"Hiyerarşi atlaması: H{current_level} etiketinden doğrudan H{next_level} etiketine geçilmiş")
            break

    return {
        "h1_count": len(h1_tags),
        "h1_samples": h1_tags[:3],
        "h2_count": len(h2_tags),
        "h3_count": len(h3_tags),
        "total_headings": len(heading_elements),
        "hierarchy_issues": hierarchy_issues,
    }


def parse_images(soup: BeautifulSoup) -> dict:
    """
    Sayfadaki tüm görselleri, eksik alt etiketlerini ve lazy-loading durumunu denetler.
    """
    images = soup.find_all("img")
    missing_alt = []
    lazy_loaded = 0

    for img in images:
        alt = img.get("alt")
        src = img.get("src") or img.get("data-src") or "isimsiz_gorsel"
        if alt is None or not alt.strip():
            missing_alt.append(src[:100])
        if img.get("loading", "").lower() == "lazy":
            lazy_loaded += 1

    return {
        "total_images": len(images),
        "missing_alt_count": len(missing_alt),
        "missing_alt_samples": missing_alt[:5],
        "lazy_loaded_count": lazy_loaded,
    }


def parse_content_stats(soup: BeautifulSoup) -> dict:
    """
    Sayfa içi görünür metin miktarını ve 'thin content' (zayıf içerik) durumunu analiz eder.
    """
    body = soup.find("body")
    if not body:
        return {"word_count": 0, "is_thin_content": True}

    text_soup = BeautifulSoup(str(body), "html.parser")
    for tag in text_soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    clean_text = text_soup.get_text(separator=" ", strip=True)
    words = [w for w in clean_text.split() if len(w) > 1]
    word_count = len(words)

    return {
        "word_count": word_count,
        "is_thin_content": word_count < 200,
    }


def parse_links(soup: BeautifulSoup, base_url: str = "") -> dict:
    """
    Dahili ve harici bağlantıların dağılımını ve nofollow kullanımını analiz eder.
    """
    links = soup.find_all("a", href=True)
    base_netloc = urlparse(base_url).netloc.lower()

    internal_count = 0
    external_count = 0
    nofollow_count = 0

    for a in links:
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        rel = [r.lower() for r in a.get("rel", [])]
        if "nofollow" in rel:
            nofollow_count += 1

        resolved = urljoin(base_url, href)
        parsed_resolved = urlparse(resolved)

        if not parsed_resolved.netloc or parsed_resolved.netloc.lower() == base_netloc:
            internal_count += 1
        else:
            external_count += 1

    return {
        "total_links": len(links),
        "internal_count": internal_count,
        "external_count": external_count,
        "nofollow_count": nofollow_count,
    }


def extract_schema(soup: BeautifulSoup) -> list:
    """
    JSON-LD yapısal verilerini ayıklar ve JSON doğrulaması yapar.
    """
    schemas = []
    for tag in soup.find_all("script", type="application/ld+json"):
        raw_text = tag.get_text().strip()
        if not raw_text:
            continue
        try:
            parsed = json.loads(raw_text)
            schemas.append(parsed)
        except json.JSONDecodeError:
            schemas.append({"raw": raw_text[:200], "parse_error": True})

    return schemas
