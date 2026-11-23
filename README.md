# 🔍 AI Website Auditor

**AI Website Auditor**, web sitelerini teknik SEO, erişilebilirlik, içerik kalitesi ve güvenlik başlıkları açısından denetleyen, kural bazlı deterministik puanlama motoru ile **Google Gemini AI** katmanını birleştiren yeni nesil bir web sitesi denetim aracıdır.

---

## ✨ Öne Çıkan Özellikler

* **🕷️ Akıllı Tarayıcı (SmartCrawler):**
  * `robots.txt` ve `sitemap.xml` dosyalarını otomatik keşfeder.
  * Site haritası bulunamadığında BFS (*Breadth-First Search*) kuyruk algoritması ile iç bağlantıları derinlemesine tarar.
* **🔬 Çok Boyutlu Teknik SEO & Ağ Analizi:**
  * **Meta Etiketleri:** Title ve Description uzunlukları, Canonical URL, Robots direktifleri (`noindex`/`nofollow`), Charset ve Viewport.
  * **Sosyal Medya Optimizasyonu:** Open Graph (`og:title`, `og:image`, `og:url` vb.) ve Twitter Card etiketlerinin spesifik doğrulaması.
  * **Başlık Hiyerarşisi:** Sayfadaki `H1` sayısı ve H1 ➔ H2 ➔ H3 sıra atlaması kontrolü.
  * **Görsel & Erişilebilirlik:** Eksik `alt` etiketleri ve `loading="lazy"` kullanımı.
  * **İçerik Kalitesi:** Görünür kelime sayısı analizi ve zayıf içerik (*Thin Content*) tespiti.
  * **Ağ & Güvenlik:** HTTPS kontrolü, milisaniye cinsinden sunucu yanıt süresi (TTFB) ve kritik güvenlik başlıkları (`HSTS`, `CSP`, `X-Content-Type-Options`, `X-Frame-Options`).
  * **Yapılandırılmış Veri:** JSON-LD formatındaki `application/ld+json` scriptlerinin sözdizimi doğrulaması.
* **🤖 Google Gemini AI Analizi (Pydantic Structured Outputs):**
  * Tespit edilen her sorun için risk seviyesi (`high`, `medium`, `low`), teknik açıklama ve **doğrudan kopyalanabilir HTML kod çözümü** üretir.
* **📊 Çift Formatlı Raporlama:**
  * **JSON:** Hem tekil sayfa bazlı hem de site geneli toplu özet raporu.
  * **İnteraktif HTML (Jinja2):** Koyu tema (Dark Mode), grafiksel skor rozetleri ve modern metrik kartları içeren tek sayfalık bağımsız web raporu.
* **⚡ Parametrik CLI:** Komut satırından sayfa sayısı, derinlik ve çıktı formatı kontrolü.

---

## 🚀 Kurulum

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/KULLANICI_ADINIZ/ai-website-auditor.git
cd ai-website-auditor
```

### 2. Sanal Ortamı Oluşturun ve Etkinleştirin
```bash
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Ortam Değişkenlerini Tanımlayın
`.env.example` dosyasını `.env` olarak kopyalayın ve Google Gemini API anahtarınızı ekleyin:
```bash
cp .env.example .env
```
`.env` dosyasını açıp anahtarınızı girin:
```env
GGAI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

---

## 💻 Kullanım Örnekleri

```bash
# 1. Varsayılan denetim (3 sayfa tarar, JSON ve HTML rapor üretir):
python main.py https://elgoog.im/

# 2. 5 sayfa tara ve sadece görsel HTML raporu oluştur:
python main.py https://elgoog.im/ --pages 5 --format html

# 3. Yalnızca tek bir sayfayı tara:
python main.py https://mrdoob.com/projects/chromeexperiments/google-gravity/ --pages 1

# 4. Hızlı denetim (Yapay zeka katmanını atlar, sadece kural bazlı puanlar):
python main.py https://elgoog.im/ --no-ai

# 5. Yardım menüsü ve parametre listesi:
python main.py --help
```

---

## 📁 Proje Dizin Yapısı

```text
ai-website-auditor/
├── data/                  # Üretilen JSON ve HTML raporları (.gitignore ile korunur)
├── src/
│   ├── ai_engine.py       # Google Gemini LLM ve Pydantic yapılandırılmış çıktı katmanı
│   ├── crawler.py         # Sitemap XML ve BFS iç bağlantı gezgini
│   ├── report_generator.py# Jinja2 tabanlı interaktif HTML rapor motoru
│   ├── scraper.py         # HTTP istekleri, DOM analizi ve metrik ayıklama
│   └── utils.py           # Ağırlıklı puanlama motoru ve rapor kaydedici
├── .env.example           # Güvenli ortam değişkenleri şablonu
├── .gitignore             # API anahtarları, venv ve rapor koruma kuralları
├── main.py                # CLI arayüzü ve ana orkestrasyon
├── requirements.txt       # Gerekli Python kütüphaneleri
└── README.md              # Dokümantasyon
```

---

## 📄 Lisans
Bu proje MIT lisansı ile lisanslanmıştır.
