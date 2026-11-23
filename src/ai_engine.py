import os
import json
import time
from typing import List, Literal
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()

# API Key Kontrolü
API_KEY = os.getenv("GGAI_API_KEY")
if not API_KEY:
    raise ValueError("GGAI_API_KEY not found in environment variables.")

# Client Oluşturma
client = genai.Client(api_key=API_KEY)

# Global Model Önbelleği
_CACHED_MODEL = None


# Yapılandırılmış Çıktı Şemaları (Pydantic / Structured Outputs)
class AuditIssue(BaseModel):
    risk_level: Literal["high", "medium", "low"] = Field(
        description="Sorunun risk seviyesi: 'high', 'medium' veya 'low'"
    )
    title: str = Field(
        description="Sorunun kısa ve net teknik başlığı (örn: 'Eksik H1 Başlığı' veya 'Görsellerde Alt Etiketi Eksik')"
    )
    description: str = Field(
        description="Sorunun teknik açıklaması ve SEO / kullanıcı deneyimi üzerindeki etkisi"
    )
    recommendation: str = Field(
        description="Sorunun çözümü için somut, uygulanabilir ve örnek kod/yöntem içeren öneri"
    )


class AIWebsiteAuditReport(BaseModel):
    meta_issues: List[AuditIssue] = Field(
        default_factory=list,
        description="Meta etiketleri (title, description, canonical, robots, OG, Twitter) ile ilgili sorunlar"
    )
    content_and_heading_issues: List[AuditIssue] = Field(
        default_factory=list,
        description="Başlık hiyerarşisi (H1-H6), zayıf içerik (thin content) ve metin yapısı ile ilgili sorunlar"
    )
    image_issues: List[AuditIssue] = Field(
        default_factory=list,
        description="Görsel erişilebilirliği (alt etiketleri), lazy-loading ve medya optimizasyonu sorunları"
    )
    security_and_technical_issues: List[AuditIssue] = Field(
        default_factory=list,
        description="HTTPS, yanıt süresi (TTFB) ve güvenlik başlıkları (HSTS, CSP vb.) ile ilgili sorunlar"
    )
    schema_issues: List[AuditIssue] = Field(
        default_factory=list,
        description="Yapılandırılmış veriler (JSON-LD, Schema.org vb.) ile ilgili sorunlar"
    )
    risk_summary: str = Field(
        description="Sitenin genel teknik SEO sağlığı, risk değerlendirmesi ve en acil aksiyon planı özeti"
    )


def get_valid_model() -> str:
    """
    Model adını belirler ve önbelleğe alır.
    """
    global _CACHED_MODEL
    if _CACHED_MODEL:
        return _CACHED_MODEL

    env_model = os.getenv("GEMINI_MODEL")
    if env_model:
        _CACHED_MODEL = env_model
        return _CACHED_MODEL

    default_model = "gemini-2.5-flash"
    try:
        model_info = client.models.get(model=default_model)
        if "generateContent" in (model_info.supported_actions or []):
            _CACHED_MODEL = default_model
            return _CACHED_MODEL
    except Exception:
        try:
            supported_models = client.models.list()
            for m in supported_models:
                if "generateContent" in (m.supported_actions or []):
                    _CACHED_MODEL = m.name
                    return _CACHED_MODEL
        except Exception as e:
            raise RuntimeError(f"Failed to resolve Gemini model: {e}")

    _CACHED_MODEL = default_model
    return _CACHED_MODEL


def analyze_with_ai(site_data: dict, max_retries: int = 2) -> dict:
    """
    Site verilerini Gemini ile genişletilmiş Faz 2 kriterlerine göre analiz eder
    ve yapılandırılmış JSON döndürür.
    """
    prompt = f"""
Sen Kıdemli bir Teknik SEO, Erişilebilirlik ve Web Güvenliği Denetim Uzmanısın.
Aşağıda verilen web sayfası denetim verilerini (meta, başlık hiyerarşisi, görseller, HTTP/güvenlik metrikleri, şema) incele.

Her kategori için:
1. Meta etiketleri (Title, Description, Canonical, Robots, Open Graph, Twitter Cards)
2. Başlık ve İçerik (H1 sayısı ve sıralaması, hiyerarşi atlamaları, kelime sayısı / thin content)
3. Görseller (Eksik alt etiketleri, lazy-loading, görsel optimizasyonu)
4. Güvenlik ve Teknik Ağ Metrikleri (HTTPS, yanıt süresi TTFB, HSTS/CSP/X-Frame güvenlik başlıkları)
5. Yapılandırılmış Veri (JSON-LD, Schema.org tipleri ve doğruluğu)

Tespit ettiğin her sorun için:
- risk_level: 'high', 'medium' veya 'low'
- title: Kısa ve net teknik başlık
- description: Teknik açıklama ve etkisi
- recommendation: Somut, doğrudan uygulanabilir çözüm önerisi

Cevap tamamen TÜRKÇE olmalıdır. Eğer bir kategoride sorun yoksa o kategorinin listesini boş bırak.

Sayfa Denetim Verisi:
{json.dumps(site_data, ensure_ascii=False, indent=2)}
"""

    model_name = get_valid_model()

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=AIWebsiteAuditReport,
        temperature=0.2
    )

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )

            return json.loads(response.text)

        except Exception as e:
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            return {
                "error": str(e),
                "meta_issues": [],
                "content_and_heading_issues": [],
                "image_issues": [],
                "security_and_technical_issues": [],
                "schema_issues": [],
                "risk_summary": f"Yapay zeka analizi sırasında hata oluştu: {str(e)}"
            }
