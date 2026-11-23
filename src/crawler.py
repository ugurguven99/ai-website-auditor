import re
import xml.etree.ElementTree as ET
from collections import deque
from urllib.parse import urlparse, urljoin, urldefrag
import httpx
from bs4 import BeautifulSoup


# Taranmayacak statik ve medya dosyaları uzantıları
IGNORED_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp", ".tiff",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".tar",
    ".gz", ".rar", ".7z", ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".wav",
    ".css", ".js", ".json", ".xml", ".txt", ".woff", ".woff2", ".ttf", ".eot"
)


def is_same_domain(url: str, base_domain: str) -> bool:
    """
    URL'in verilen ana domain sınırları içinde olup olmadığını doğrular.
    """
    try:
        netloc = urlparse(url).netloc.lower().split(":")[0]
        base_netloc = base_domain.lower().split(":")[0]
        return netloc == base_netloc or netloc.endswith("." + base_netloc)
    except Exception:
        return False


def normalize_url(url: str, base_url: str = "") -> str:
    """
    URL'i temizler, fragment (#) kısımlarını kaldırır ve göreli URL'leri mutlak hale getirir.
    """
    if base_url:
        url = urljoin(base_url, url)

    url, _ = urldefrag(url)
    parsed = urlparse(url)

    # Yalnızca HTTP ve HTTPS protokolleri
    if parsed.scheme not in ("http", "https"):
        return ""

    path = parsed.path or "/"
    # Çift slash temizliği
    path = re.sub(r"/+", "/", path)

    clean_url = f"{parsed.scheme}://{parsed.netloc}{path}"
    if parsed.query:
        clean_url += f"?{parsed.query}"

    return clean_url


def is_valid_crawl_candidate(url: str, base_domain: str) -> bool:
    """
    URL'in taranabilir bir HTML sayfası olup olmadığını kontrol eder.
    """
    if not url:
        return False

    parsed = urlparse(url)
    path_lower = parsed.path.lower()

    if any(path_lower.endswith(ext) for ext in IGNORED_EXTENSIONS):
        return False

    return is_same_domain(url, base_domain)


def parse_sitemap_xml(xml_content: str) -> list[str]:
    """
    Sitemap XML içeriğini ayrıştırır. Hem urlset hem de sitemapindex etiketlerini destekler.
    """
    urls = []
    try:
        # Namespace kaldırma
        xml_content_clean = re.sub(r'\sxmlns="[^"]+"', '', xml_content, count=1)
        root = ET.fromstring(xml_content_clean)

        # 1. Standart sayfa URL'leri (<url><loc>...</loc></url>)
        for loc in root.findall(".//url/loc"):
            if loc.text and loc.text.strip():
                urls.append(loc.text.strip())

        # 2. Sitemap Index alt haritaları (<sitemap><loc>...</loc></sitemap>)
        if not urls:
            for loc in root.findall(".//sitemap/loc"):
                if loc.text and loc.text.strip():
                    urls.append(loc.text.strip())

    except Exception:
        pass

    return urls


class SmartCrawler:
    """
    Sitemap keşfi ve BFS (Breadth-First Search) iç bağlantı tarayıcısını
    birleştiren akıllı site gezgini.
    """

    def __init__(
        self,
        start_url: str,
        max_pages: int = 10,
        max_depth: int = 2,
        timeout: int = 10
    ):
        self.start_url = normalize_url(start_url)
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.timeout = timeout

        parsed = urlparse(self.start_url)
        self.base_domain = parsed.netloc.lower().split(":")[0]
        self.base_origin = f"{parsed.scheme}://{parsed.netloc}"

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36 (Website-Auditor-Bot)"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def discover_sitemap_urls(self, client: httpx.Client) -> list[str]:
        """
        robots.txt ve standart yollar (/sitemap.xml) üzerinden sitemap'leri keşfeder.
        """
        sitemap_candidates = []

        # 1. robots.txt kontrolü
        try:
            robots_url = f"{self.base_origin}/robots.txt"
            res = client.get(robots_url, headers=self.headers, timeout=self.timeout)
            if res.status_code == 200:
                for line in res.text.splitlines():
                    if line.lower().startswith("sitemap:"):
                        sm_url = line.split(":", 1)[1].strip()
                        if sm_url:
                            sitemap_candidates.append(sm_url)
        except Exception:
            pass

        # 2. Standart sitemap yolları
        default_paths = [
            f"{self.base_origin}/sitemap.xml",
            f"{self.base_origin}/sitemap_index.xml",
        ]
        for p in default_paths:
            if p not in sitemap_candidates:
                sitemap_candidates.append(p)

        discovered_urls = []
        for sm_url in sitemap_candidates:
            try:
                res = client.get(sm_url, headers=self.headers, timeout=self.timeout)
                if res.status_code == 200 and ("xml" in res.headers.get("content-type", "") or res.text.startswith("<?xml")):
                    parsed_urls = parse_sitemap_xml(res.text)

                    for u in parsed_urls:
                        # Eğer alt sitemap ise bir seviye daha çek
                        if u.endswith(".xml"):
                            try:
                                sub_res = client.get(u, headers=self.headers, timeout=self.timeout)
                                if sub_res.status_code == 200:
                                    sub_urls = parse_sitemap_xml(sub_res.text)
                                    discovered_urls.extend(sub_urls)
                            except Exception:
                                continue
                        else:
                            discovered_urls.append(u)

                    if len(discovered_urls) >= self.max_pages:
                        break
            except Exception:
                continue

        # Aynı domain ve geçerli olanları filtrele
        clean_urls = []
        for u in discovered_urls:
            norm = normalize_url(u, self.base_origin)
            if is_valid_crawl_candidate(norm, self.base_domain) and norm not in clean_urls:
                clean_urls.append(norm)

        return clean_urls[:self.max_pages]

    def crawl_with_bfs(self, client: httpx.Client) -> list[str]:
        """
        İç bağlantıları BFS (Breadth-First Search) kuyruk algoritması ile derinlemesine tarar.
        """
        discovered = [self.start_url]
        visited = set()
        queue = deque([(self.start_url, 0)])

        while queue and len(discovered) < self.max_pages:
            current_url, depth = queue.popleft()

            if current_url in visited or depth > self.max_depth:
                continue

            visited.add(current_url)

            try:
                res = client.get(current_url, headers=self.headers, timeout=self.timeout, follow_redirects=True)
                if res.status_code != 200:
                    continue

                content_type = res.headers.get("content-type", "").lower()
                if "text/html" not in content_type:
                    continue

                soup = BeautifulSoup(res.text, "html.parser")
                for a_tag in soup.find_all("a", href=True):
                    raw_href = a_tag["href"].strip()
                    norm_url = normalize_url(raw_href, current_url)

                    if (
                        norm_url
                        and is_valid_crawl_candidate(norm_url, self.base_domain)
                        and norm_url not in discovered
                    ):
                        discovered.append(norm_url)
                        if depth + 1 <= self.max_depth:
                            queue.append((norm_url, depth + 1))

                        if len(discovered) >= self.max_pages:
                            break

            except Exception:
                continue

        return discovered

    def discover_urls(self) -> list[str]:
        """
        Hibrit keşif stratejisi:
        Önce Sitemap dener; yeterli URL bulunamazsa BFS iç bağlantı tarayıcısını devreye alır.
        """
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            # 1. Sitemap Denemesi
            sitemap_urls = self.discover_sitemap_urls(client)
            if len(sitemap_urls) >= 2:
                # Başlangıç URL'ini listenin başına ekle (eğer yoksa)
                if self.start_url not in sitemap_urls:
                    sitemap_urls.insert(0, self.start_url)
                return sitemap_urls[:self.max_pages]

            # 2. Fallback: BFS Link Crawling
            bfs_urls = self.crawl_with_bfs(client)
            return bfs_urls[:self.max_pages]
