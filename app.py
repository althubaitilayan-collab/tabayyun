import streamlit as st
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import pdfplumber
import time

# For Word (.docx) support — Data Ingestion poster claim
from docx import Document

# ==========================================
# Page Configuration & Custom CSS
# ==========================================
st.set_page_config(
    page_title="Tabayyun | تَبيُّن",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Corporate Styling - FIXED TEXT VISIBILITY
# (UNCHANGED — exact same theme as the file we built last week. Nothing here was touched.)
st.markdown("""
<style>
    /* Main Header */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 { font-size: 2.2rem; margin-bottom: 0.5rem; font-weight: 700; }
    .main-header p { font-size: 1.1rem; opacity: 0.9; }
    
    /* Buttons */
    .stButton>button {
        background-color: #1e3a8a;
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 6px;
        font-size: 1rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.2s;
    }
    .stButton>button:hover { background-color: #1e40af; transform: translateY(-1px); }
    
    /* Content Boxes - FIXED: Explicit dark text color + RTL support */
    .doc-box {
        background: #ffffff;
        color: #1e293b !important;
        padding: 1.2rem;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        height: 100%;
        font-family: 'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, Arial, sans-serif;
        line-height: 1.8;
        direction: rtl;
        text-align: right;
        font-size: 1rem;
    }
    .result-box {
        background: #ffffff;
        color: #1e293b !important;
        padding: 1.5rem;
        border-radius: 6px;
        border-right: 4px solid #1e3a8a;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-top: 1rem;
        direction: rtl;
        text-align: right;
        font-family: 'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, Arial, sans-serif;
        line-height: 1.8;
        font-size: 1rem;
    }
    
    /* Stats Cards */
    .stat-card {
        background: white;
        padding: 1.2rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
        border-top: 3px solid #3b82f6;
    }
    .stat-number { font-size: 1.8rem; font-weight: bold; color: #1e3a8a; margin-bottom: 0.3rem; }
    .stat-label { color: #64748b; font-size: 0.85rem; font-weight: 500; }
    
    /* Remove Streamlit default padding/margins where needed */
    .block-container { padding-top: 2rem; }

    /* --- NEW (quick fix, added after screenshot review) --- */

    /* Fix 1: force the AR/EN radio to use the site's blue instead of Streamlit's default red/pink */
    div[role="radiogroup"] label > div:first-child {
        border-color: #1e3a8a !important;
    }
    div[role="radiogroup"] label input:checked + div > div {
        background-color: #1e3a8a !important;
    }

    /* Fix 2: make the 5 methodology-stage buttons small light-blue pills,
       distinct from the big solid-blue action buttons (Start Analysis, etc.).
       Targets only buttons whose Streamlit key starts with "stage_". */
    div[class*="st-key-stage_"] button {
        background-color: #eff6ff !important;
        color: #1e3a8a !important;
        border: none !important;
        border-top: 3px solid #1e3a8a !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        padding: 0.4rem 0.3rem !important;
        box-shadow: none !important;
        transform: none !important;
    }
    div[class*="st-key-stage_"] button:hover {
        background-color: #dbeafe !important;
        transform: none !important;
    }

    /* Fix 3: kill Streamlit's default orange/red focus & active ring on ALL buttons,
       replace with the site's blue everywhere */
    .stButton > button:focus,
    .stButton > button:focus:not(:active),
    .stButton > button:active,
    button[kind="secondary"]:focus,
    button[kind="primary"]:focus {
        box-shadow: none !important;
        outline: none !important;
        border-color: #1e3a8a !important;
        color: #ffffff !important;
    }
    /* Same fix, but for the light-blue stage pills specifically (keep them light, not white text) */
    div[class*="st-key-stage_"] button:focus,
    div[class*="st-key-stage_"] button:focus:not(:active),
    div[class*="st-key-stage_"] button:active {
        box-shadow: none !important;
        outline: none !important;
        border-color: #1e3a8a !important;
        color: #1e3a8a !important;
        background-color: #dbeafe !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# NEW: Interface language labels
# UI chrome (titles, tabs, buttons, headers) toggles between Arabic and English.
# Document content, extracted elements, and analysis results are NEVER translated —
# they always display in Arabic, because that's the actual output of the model
# and the core value proposition of the product.
# ==========================================
L = {
    "header_subtitle": {
        "ar": "منصة ذكاء اصطناعي للتحقق من سلامة الإجراءات والامتثال المؤسسي",
        "en": "AI-Powered Platform for Institutional Compliance & Procedural Integrity",
    },
    "stat1_label": {"ar": "دقة الاكتشاف", "en": "Detection Accuracy"},
    "stat2_label": {"ar": "توفير الوقت", "en": "Time Savings"},
    "stat3_label": {"ar": "صفحة/دقيقة", "en": "Pages/Minute"},
    "stat4_label": {"ar": "دعم اللغة العربية", "en": "Arabic Support"},
    "pipeline_title": {"ar": "مراحل المعالجة", "en": "Processing Pipeline"},
    "tab1": {"ar": "تحليل بيانات تجريبية", "en": "Mock Data Analysis"},
    "tab2": {"ar": "رفع مستند", "en": "Document Upload"},
    "tab3": {"ar": "عن تبيّن", "en": "About Tabayyun"},
    "mock_info": {
        "ar": "محاكاة اكتشاف التناقضات بين 'الإجراء الرسمي' و'الدليل الميداني'.",
        "en": "Simulating contradiction detection between 'Official Procedure' and 'Field Guide'.",
    },
    "source1_label": {"ar": "المصدر الأول: الإجراء الرسمي", "en": "Source 1: Official Procedure"},
    "source2_label": {"ar": "المصدر الثاني: الدليل الميداني", "en": "Source 2: Field Guide"},
    "start_analysis_btn": {"ar": "بدء تحليل التناقضات", "en": "Start Contradiction Analysis"},
    "extracted_elements_header": {"ar": "العناصر الإجرائية المستخرَجة", "en": "Extracted Procedural Elements"},
    "results_header": {"ar": "نتائج التحليل", "en": "Analysis Results"},
    "download_btn": {"ar": "تنزيل التقرير", "en": "Download Report"},
    "upload_info": {
        "ar": "ارفع مستندين (PDF أو Word) للمقارنة واكتشاف التناقضات.",
        "en": "Upload two documents (PDF or Word) to compare and detect contradictions.",
    },
    "doc1_label": {"ar": "المستند الأول", "en": "Document 1"},
    "doc2_label": {"ar": "المستند الثاني", "en": "Document 2"},
    "select_file": {"ar": "اختار ملف PDF أو Word", "en": "Select a PDF or Word file"},
    "analyze_upload_btn": {"ar": "تحليل التناقضات بين المستندين", "en": "Analyze Contradictions Between Documents"},
    "about_title": {"ar": "عن منصة تبيّن", "en": "About Tabayyun Platform"},
    "about_intro": {
        "ar": 'تبيّن منصة ذكاء اصطناعي مبتكرة صُممت لمعالجة "فجوة الامتثال الإجرائي" في الجهات السعودية.',
        "en": 'Tabayyun is an innovative AI platform designed to address the "Procedural Compliance Gap" in Saudi institutions.',
    },
    "problem_header": {"ar": "المشكلة التي نعالجها:", "en": "Problem Addressed:"},
    "problem_items": {
        "ar": [
            "معلومات متناقضة بين المصادر الرسمية",
            "إجراءات قديمة لم تُحدَّث بعد تغييرات الأنظمة",
            "فجوة بين الإجراء الموثّق وطريقة التنفيذ الفعلي",
            "خطوات ناقصة في أدلة الإجراءات",
        ],
        "en": [
            "Contradictory information across official sources",
            "Outdated procedures not updated after system changes",
            "Gap between documented procedures and actual execution",
            "Missing steps in procedural guides",
        ],
    },
    "solution_header": {"ar": "الحل:", "en": "Solution:"},
    "solution_text": {
        "ar": "منصة ذكية تستخدم الذكاء الاصطناعي لمراجعة المستندات آلياً، واكتشاف التناقضات والمعلومات الناقصة، لضمان سلامة المعرفة المؤسسية قبل وقوع الأخطاء.",
        "en": "An intelligent platform using AI to automatically review documents, detect contradictions and missing information, ensuring institutional knowledge integrity before errors occur.",
    },
    "advantages_header": {"ar": "مزايا تنافسية:", "en": "Competitive Advantages:"},
    # NOTE: this list was corrected earlier this week to match the poster/marketing summary —
    # "NDMO" was removed (no basis in your materials), and the hosting model + NCA compliance
    # are now correctly labeled as PLANNED, not as something already in place.
    "advantages_items": {
        "ar": [
            "دعم كامل للغة العربية والسياق الإداري السعودي",
            "نموذج استضافة هجين مخطط له (SaaS + محلي) لأقصى درجات الأمان",
            "خطة للامتثال لضوابط NCA الأساسية للأمن السيبراني قبل أي نشر كامل",
            "اكتشاف استباقي للمشاكل قبل وقوعها",
        ],
        "en": [
            "Full Arabic language and Saudi administrative context support",
            "Planned hybrid hosting model (SaaS + On-Premise) for maximum security",
            "Roadmap to NCA Essential Cybersecurity Controls compliance ahead of full deployment",
            "Proactive problem detection before occurrence",
        ],
    },
    "footer": {"ar": "© 2026 تبيّن | مبادرة طلابية سعودية | SAIF 2026", "en": "© 2026 Tabayyun | Saudi Student Initiative | SAIF 2026"},
    "lang_picker_label": {"ar": "لغة الواجهة", "en": "Interface Language"},
    "theme_picker_label": {"ar": "وضع العرض", "en": "Display Mode"},
    # --- Sidebar ---
    "about_platform_header": {"ar": "عن المنصة", "en": "About Platform"},
    "about_platform_text": {
        "ar": "منصة ذكاء اصطناعي للتحقق من الامتثال المؤسسي وسلامة الإجراءات.",
        "en": "AI-powered platform for institutional compliance and procedural integrity.",
    },
    "system_status_header": {"ar": "حالة النظام", "en": "System Status"},
    "model_active": {"ar": "النموذج يعمل", "en": "Model Active"},
    "model_unavailable": {"ar": "النموذج غير متاح", "en": "Model Unavailable"},
    "prototype_caption": {"ar": "نسخة أولية v1.2 | SAIF 2026", "en": "Prototype v1.2 | SAIF 2026"},
    "model_caption": {"ar": "النموذج: Qwen2.5 7B | تشغيل محلي", "en": "Model: Qwen2.5 7B | Local Deployment"},
    # --- Status / progress messages ---
    "model_unavailable_full": {"ar": "النموذج غير متاح. تأكد من تشغيل Ollama.", "en": "Model unavailable. Please ensure Ollama is running."},
    "model_unavailable_short": {"ar": "النموذج غير متاح.", "en": "Model unavailable."},
    "status_init": {"ar": "جارٍ تجهيز محرك التحليل...", "en": "Initializing analysis engine..."},
    "status_parsing": {"ar": "جارٍ قراءة بنية المستندات...", "en": "Parsing document structures..."},
    "status_extracting": {"ar": "جارٍ استخراج الخطوات والشروط (معالجة ذكية)...", "en": "Extracting steps and conditions (Smart Processing)..."},
    "status_crossref": {"ar": "جارٍ مقارنة البنود الإجرائية...", "en": "Cross-referencing procedural clauses..."},
    "status_generating": {"ar": "جارٍ توليد تقرير التناقضات...", "en": "Generating contradiction report..."},
    "status_complete_label": {"ar": "اكتمل التحليل", "en": "Analysis Complete"},
    "status_failed_label": {"ar": "فشل التحليل", "en": "Analysis Failed"},
    "success_analysis": {"ar": "تم إكمال التحليل بنجاح", "en": "Analysis Completed Successfully"},
    "error_analysis_prefix": {"ar": "خطأ في التحليل:", "en": "Analysis error:"},
    "error_during_analysis_prefix": {"ar": "خطأ أثناء التحليل:", "en": "Error during analysis:"},
    # --- Upload tab ---
    "uploaded_prefix": {"ar": "تم الرفع:", "en": "Uploaded:"},
    "extracted_chars": {"ar": "تم استخراج {n} حرفاً", "en": "Extracted {n} characters"},
    "preview_extracted_text": {"ar": "معاينة النص المستخرَج", "en": "Preview Extracted Text"},
    "no_text_extracted": {"ar": "لم يتم استخراج أي نص من الملف", "en": "No text extracted from file"},
    "please_upload_both": {"ar": "الرجاء رفع المستندين أولاً.", "en": "Please upload both documents first."},
    "could_not_extract": {"ar": "تعذّر استخراج النص من أحد الملفين أو كليهما.", "en": "Could not extract text from one or both files."},
    "status_processing_upload": {"ar": "جارٍ معالجة المستندات المرفوعة...", "en": "Processing uploaded documents..."},
    "status_reading_docs": {"ar": "جارٍ قراءة بنية المستندات...", "en": "Reading document structures..."},
    "status_running_engine": {"ar": "جارٍ تشغيل محرك اكتشاف التناقضات...", "en": "Running AI contradiction engine..."},
    # --- About tab footer ---
    "contact_header": {"ar": "تواصل معنا", "en": "Contact"},
    "github_line": {"ar": "GitHub: github.com/tabayyun", "en": "GitHub: github.com/tabayyun"},
    "pipeline_hint": {
        "ar": "اضغط على أي مرحلة أعلاه لمعرفة حالتها الفعلية.",
        "en": "Click any stage above to see its real status.",
    },
}


def t(key: str) -> str:
    """Translate a UI label into the currently selected interface language."""
    return L[key][st.session_state.get("lang", "ar")]


# NEW: the 5 methodology stages, matching the poster's Methodology box names exactly.
# Each stage's status/description reflects what the code ACTUALLY does today —
# not what the poster describes as the full vision. This keeps the interface honest.
STAGES = [
    {
        "name": {"ar": "الاستيراد", "en": "Ingestion"},
        "status": {"ar": "نشط الآن", "en": "Active now"},
        "desc": {"ar": "استيراد ملفات PDF وWord فعلياً.", "en": "Actually imports PDF and Word files."},
    },
    {
        "name": {"ar": "معالجة ذكية", "en": "Smart Processing"},
        "status": {"ar": "نشط الآن", "en": "Active now"},
        "desc": {
            "ar": "نموذج LLM يستخرج الخطوات والشروط والمدد من كل مستند.",
            "en": "An LLM extracts steps, conditions and timeframes from each document.",
        },
    },
    {
        "name": {"ar": "محرك التحقق", "en": "Verification"},
        "status": {"ar": "نشط جزئياً", "en": "Partially active"},
        "desc": {
            "ar": "يكتشف التناقضات بين مصدرين فعلياً. مقارنة الإجراء ببيانات التنفيذ الفعلي مخطط له لاحقاً.",
            "en": "Actually detects contradictions between two sources. Comparing against real execution data is planned.",
        },
    },
    {
        "name": {"ar": "تصنيف المخاطر", "en": "Risk Classification"},
        "status": {"ar": "مخطط له", "en": "Planned"},
        "desc": {
            "ar": "حالياً: نفس نموذج LLM يحدد الخطورة ضمن نفس الاستدعاء. موديل ML منفصل للتصنيف مخطط له لاحقاً.",
            "en": "Currently: severity is set by the same LLM call. A dedicated ML classification model is planned.",
        },
    },
    {
        "name": {"ar": "التوصيات", "en": "Recommendations"},
        "status": {"ar": "نشط الآن", "en": "Active now"},
        "desc": {
            "ar": "كل تناقض يظهر معه توصية إصلاح مقترحة فعلياً.",
            "en": "Every contradiction now comes with an actual suggested fix.",
        },
    },
]

# ==========================================
# Model Loading
# ==========================================
@st.cache_resource
def load_model():
    try:
        return ChatOllama(model="qwen2.5:7b-instruct-q4_K_M", temperature=0.1)
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

model = load_model()

# ==========================================
# Helper Functions (extraction / analysis — UNCHANGED from last week, still Arabic-only)
# ==========================================
def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from PDF using pdfplumber"""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text.strip() + "\n\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def extract_text_from_docx(docx_file) -> str:
    """Extract text from a Word (.docx) file using python-docx"""
    text = ""
    try:
        document = Document(docx_file)
        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text.strip() + "\n\n"
        for table in document.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    text += row_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading Word file: {e}")
        return ""

def extract_text_from_file(uploaded_file) -> str:
    """Dispatch to the correct extractor depending on file type (PDF or Word)"""
    filename = uploaded_file.name.lower()
    if filename.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        return extract_text_from_pdf(uploaded_file)

def get_mock_documents():
    doc_a = """
    الإجراء الرسمي: إصدار تصريح دخول الزوار
    المادة 3: يجب على الموظف تقديم طلب التصريح عبر نظام البوابة الإلكترونية قبل موعد الزيارة بـ 48 ساعة عمل على الأقل.
    المادة 4: مدة صلاحية التصريح هي يوم واحد فقط ولا يمكن تمديدها إلكترونياً.
    المادة 5: يجب أن يكون طلب التصريح معتمداً من مدير القسم المباشر.
    """
    
    doc_b = """
    دليل الإجراءات الميداني: استقبال الزوار
    الفقرة 2: يُسمح بتقديم طلبات التصريح قبل الزيارة بـ 24 ساعة فقط لضمان المرونة التشغيلية.
    الفقرة 3: يمكن تمديد صلاحية التصريح ليوم إضافي عبر التواصل المباشر مع أمن المنشأة دون الحاجة لطلب إلكتروني.
    الفقرة 4: يمكن لأي موظف تقديم طلب التصريح دون الحاجة لاعتماد المدير.
    """
    return doc_a, doc_b

def extract_procedure_elements(doc_text: str, doc_label: str = "المستند") -> str:
    """Extract structured steps, conditions, timeframes and authorities from one document.
    This prompt is intentionally always Arabic — the analysis language is core to the product,
    independent of the interface language toggle."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """أنت محلل إجراءات مؤسسي. مهمتك قراءة نص إجراء واحد فقط واستخلاص عناصره الأساسية بشكل منظم.
لا تقارن مع أي مصدر آخر، فقط استخرج مما هو مكتوب في هذا النص وحده."""),
        ("user", """
النص: {doc_text}

استخرج من هذا النص فقط، في نقاط مختصرة:
1. الخطوات المطلوبة
2. الشروط والمتطلبات
3. المدد الزمنية المذكورة (إن وجدت)
4. الجهة أو الصلاحية المطلوبة للاعتماد (إن وجدت)

إذا لم يُذكر أحد هذه العناصر في النص، اكتب "غير مذكور" أمامه بدل اختلاق معلومة.""")
    ])
    chain = prompt | model
    response = chain.invoke({"doc_text": doc_text})
    return response.content

def analyze_contradictions(doc_a: str, doc_b: str):
    """Analyze contradictions between two documents. Always Arabic — see note above."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """أنت خبير تدقيق إجرائي ومؤسسي في الجهات السعودية. 
مهمتك هي مقارنة نصين إجرائيين واكتشاف أي تناقضات جوهرية بينهما.
ركز على: المدد الزمنية، الشروط، الصلاحيات، وطرق التنفيذ.
أجب باللغة العربية الفصحى وبشكل منظم ومهني."""),
        ("user", """
المصدر الأول: {doc_a}

المصدر الثاني: {doc_b}

قم بتحليل التناقضات وعرضها في قائمة نقطية واضحة. لكل تناقض، اذكر:
1. بند التناقض
2. ما ورد في المصدر الأول
3. ما ورد في المصدر الثاني
4. مستوى الخطورة (مرتفع/متوسط/منخفض)
5. درجة الثقة (Confidence Score) من 0 إلى 100%
6. التوصية المقترحة لحل هذا التناقض (خطوة عملية واحدة يمكن للمسؤول تنفيذها)

في النهاية، أضف ملخصاً تنفيذياً قصيراً (3-4 أسطر) يوضح أبرز المخاطر والتوصيات.""")
    ])
    
    chain = prompt | model
    response = chain.invoke({"doc_a": doc_a, "doc_b": doc_b})
    return response.content

# ==========================================
# Sidebar
# ==========================================
if "lang" not in st.session_state:
    st.session_state.lang = "ar"
if "theme" not in st.session_state:
    st.session_state.theme = "light"

with st.sidebar:
    st.markdown("## Tabayyun | تَبيُّن")
    st.markdown("---")

    # NEW: interface language toggle. Only affects UI chrome (labels, tabs, buttons).
    # Document content and analysis results always stay in Arabic — see note above L dict.
    st.markdown(f"### {t('lang_picker_label')}")
    lang_choice = st.radio(
        "lang", options=["AR", "EN"],
        index=0 if st.session_state.lang == "ar" else 1,
        horizontal=True, label_visibility="collapsed"
    )
    st.session_state.lang = "ar" if lang_choice == "AR" else "en"

    # Light/Dark display mode — Option 1 palette (classic corporate, navy/blue),
    # the one the team picked after comparing both proposals.
    st.markdown(f"### {t('theme_picker_label')}")
    theme_choice = st.radio(
        "theme", options=["Light", "Dark"],
        index=0 if st.session_state.get("theme", "light") == "light" else 1,
        horizontal=True, label_visibility="collapsed"
    )
    st.session_state.theme = "light" if theme_choice == "Light" else "dark"

    st.markdown("---")
    st.markdown(f"### {t('about_platform_header')}")
    st.info(t("about_platform_text"))
    st.markdown("---")
    st.markdown(f"### {t('system_status_header')}")
    if model:
        st.success(t("model_active"))
    else:
        st.error(t("model_unavailable"))
    st.markdown("---")
    st.caption(t("prototype_caption"))
    st.caption(t("model_caption"))

# Fix 4 (corrected): dynamic text direction — right-aligned for Arabic, left for English.
# This now runs AFTER the sidebar has resolved st.session_state.lang for THIS run,
# which fixes the one-click lag from before.
if st.session_state.lang == "ar":
    st.markdown("""
    <style>
        .block-container, section[data-testid="stSidebar"] .block-container { direction: rtl; }
        .block-container p, .block-container li, .block-container h1,
        .block-container h2, .block-container h3, .block-container h4,
        section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] li {
            text-align: right;
        }
        .stTabs [data-baseweb="tab-list"] { direction: rtl; }
        div[role="radiogroup"] { direction: rtl; }
        ul, ol { padding-right: 20px; padding-left: 0; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .block-container, section[data-testid="stSidebar"] .block-container { direction: ltr; }
        .block-container p, .block-container li, .block-container h1,
        .block-container h2, .block-container h3, .block-container h4,
        section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] li {
            text-align: left;
        }
        .stTabs [data-baseweb="tab-list"] { direction: ltr; }
        div[role="radiogroup"] { direction: ltr; }
        ul, ol { padding-left: 20px; padding-right: 0; }
    </style>
    """, unsafe_allow_html=True)

# Dark mode palette — Option 1 (classic corporate). Only applied when the sidebar
# toggle is set to Dark; Light mode is the original design, untouched.
if st.session_state.theme == "dark":
    st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { background-color: #0f172a; }
        section[data-testid="stSidebar"] { background-color: #111827; }
        section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

        .block-container, .block-container p, .block-container li,
        .block-container h1, .block-container h2, .block-container h3,
        .block-container h4, .stCaption {
            color: #e2e8f0 !important;
        }

        .doc-box {
            background: #1e293b !important;
            color: #e2e8f0 !important;
            border-color: #334155 !important;
        }
        .result-box {
            background: #1e293b !important;
            color: #e2e8f0 !important;
            border-right-color: #3b82f6 !important;
            box-shadow: none !important;
        }
        .stat-card {
            background: #1e293b !important;
            box-shadow: none !important;
            border-top-color: #3b82f6 !important;
        }
        .stat-card .stat-number { color: #93c5fd !important; }
        .stat-card .stat-label { color: #94a3b8 !important; }

        div[class*="st-key-stage_"] button {
            background-color: #1e293b !important;
            color: #93c5fd !important;
            border-top-color: #3b82f6 !important;
        }
        div[class*="st-key-stage_"] button:hover {
            background-color: #273449 !important;
        }
        div[class*="st-key-stage_"] button:focus,
        div[class*="st-key-stage_"] button:active {
            color: #93c5fd !important;
            background-color: #273449 !important;
            border-color: #3b82f6 !important;
        }

        div[data-testid="stAlert"] {
            background-color: #1e293b !important;
            color: #e2e8f0 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# Main Interface
# ==========================================
st.markdown(f"""
<div class="main-header">
    <h1>Tabayyun | تَبيُّن</h1>
    <p>{t('header_subtitle')}</p>
</div>
""", unsafe_allow_html=True)

# Key Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="stat-card"><div class="stat-number">85%</div><div class="stat-label">{t("stat1_label")}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stat-card"><div class="stat-number">70%</div><div class="stat-label">{t("stat2_label")}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="stat-card"><div class="stat-number">100+</div><div class="stat-label">{t("stat3_label")}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="stat-card"><div class="stat-number">100%</div><div class="stat-label">{t("stat4_label")}</div></div>', unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# NEW: Methodology pipeline status bar
# Matches the poster's 5 Methodology stage names exactly. Clicking a stage shows
# its REAL current status (Active / Partially active / Planned) — not the poster's
# full vision. This is the honesty layer we agreed on.
# ==========================================
st.markdown(f"**{t('pipeline_title')}**")
if "selected_stage" not in st.session_state:
    st.session_state.selected_stage = None

stage_cols = st.columns(5)
for i, stage in enumerate(STAGES):
    with stage_cols[i]:
        if st.button(stage["name"][st.session_state.lang], key=f"stage_{i}", use_container_width=True):
            st.session_state.selected_stage = i

if st.session_state.selected_stage is not None:
    s = STAGES[st.session_state.selected_stage]
    lang = st.session_state.lang
    st.info(f"[{s['status'][lang]}] {s['desc'][lang]}")
else:
    st.info(t("pipeline_hint"))

st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs([t("tab1"), t("tab2"), t("tab3")])

# ==========================================
# Tab 1: Mock Data
# ==========================================
with tab1:
    st.info(t("mock_info"))
    
    doc_a, doc_b = get_mock_documents()
    doc_a_html = doc_a.replace("\n", "<br>")
    doc_b_html = doc_b.replace("\n", "<br>")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### {t('source1_label')}")
        st.markdown(f'<div class="doc-box">{doc_a_html}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f"#### {t('source2_label')}")
        st.markdown(f'<div class="doc-box">{doc_b_html}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button(t("start_analysis_btn"), key="btn_mock"):
        if model is None:
            st.error(t("model_unavailable_full"))
        else:
            with st.status(t("status_init"), expanded=True) as status:
                st.write(t("status_parsing"))
                time.sleep(0.8)

                st.write(t("status_extracting"))
                elements_a = extract_procedure_elements(doc_a, "Source 1")
                elements_b = extract_procedure_elements(doc_b, "Source 2")

                st.write(t("status_crossref"))
                time.sleep(0.8)
                st.write(t("status_generating"))
                
                try:
                    result = analyze_contradictions(doc_a, doc_b)
                    status.update(label=t("status_complete_label"), state="complete", expanded=False)
                    
                    st.success(t("success_analysis"))
                    st.markdown("---")

                    st.markdown(f"### {t('extracted_elements_header')}")
                    ecol1, ecol2 = st.columns(2)
                    with ecol1:
                        st.markdown(f"#### {t('doc1_label')}")
                        elements_a_html = elements_a.replace("\n", "<br>")
                        st.markdown(f'<div class="doc-box">{elements_a_html}</div>', unsafe_allow_html=True)
                    with ecol2:
                        st.markdown(f"#### {t('doc2_label')}")
                        elements_b_html = elements_b.replace("\n", "<br>")
                        st.markdown(f'<div class="doc-box">{elements_b_html}</div>', unsafe_allow_html=True)

                    st.markdown("---")
                    st.markdown(f"### {t('results_header')}")
                    
                    result_html = result.replace("\n", "<br>")
                    st.markdown(f'<div class="result-box">{result_html}</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.download_button(
                        label=t("download_btn"),
                        data=result,
                        file_name="Tabayyun_Mock_Analysis_Report.md",
                        mime="text/markdown",
                    )
                except Exception as e:
                    status.update(label=t("status_failed_label"), state="error", expanded=True)
                    st.error(f"{t('error_analysis_prefix')} {e}")

# ==========================================
# Tab 2: Document Upload (PDF and Word)
# ==========================================
with tab2:
    st.info(t("upload_info"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### {t('doc1_label')}")
        uploaded_file_1 = st.file_uploader(t("select_file"), type=["pdf", "docx"], key="file1")
        if uploaded_file_1:
            st.success(f"{t('uploaded_prefix')} {uploaded_file_1.name}")
            text_1 = extract_text_from_file(uploaded_file_1)
            if text_1:
                st.info(t("extracted_chars").format(n=len(text_1)))
                with st.expander(t("preview_extracted_text")):
                    st.text(text_1[:1000] + "..." if len(text_1) > 1000 else text_1)
            else:
                st.warning(t("no_text_extracted"))
    
    with col2:
        st.markdown(f"#### {t('doc2_label')}")
        uploaded_file_2 = st.file_uploader(t("select_file"), type=["pdf", "docx"], key="file2")
        if uploaded_file_2:
            st.success(f"{t('uploaded_prefix')} {uploaded_file_2.name}")
            text_2 = extract_text_from_file(uploaded_file_2)
            if text_2:
                st.info(t("extracted_chars").format(n=len(text_2)))
                with st.expander(t("preview_extracted_text")):
                    st.text(text_2[:1000] + "..." if len(text_2) > 1000 else text_2)
            else:
                st.warning(t("no_text_extracted"))
    
    st.markdown("---")
    
    analyze_btn_disabled = not (uploaded_file_1 and uploaded_file_2)
    if st.button(t("analyze_upload_btn"), key="btn_pdf", disabled=analyze_btn_disabled):
        if model is None:
            st.error(t("model_unavailable_short"))
        elif not (uploaded_file_1 and uploaded_file_2):
            st.warning(t("please_upload_both"))
        else:
            text_1 = extract_text_from_file(uploaded_file_1)
            text_2 = extract_text_from_file(uploaded_file_2)
            
            if not text_1 or not text_2:
                st.error(t("could_not_extract"))
            else:
                with st.status(t("status_processing_upload"), expanded=True) as status:
                    st.write(t("status_reading_docs"))
                    time.sleep(0.5)

                    st.write(t("status_extracting"))
                    elements_1 = extract_procedure_elements(text_1, "Document 1")
                    elements_2 = extract_procedure_elements(text_2, "Document 2")

                    st.write(t("status_running_engine"))
                    
                    try:
                        result = analyze_contradictions(text_1, text_2)
                        status.update(label=t("status_complete_label"), state="complete", expanded=False)
                        
                        st.success(t("success_analysis"))
                        st.markdown("---")

                        st.markdown(f"### {t('extracted_elements_header')}")
                        ecol1, ecol2 = st.columns(2)
                        with ecol1:
                            st.markdown(f"#### {t('doc1_label')}")
                            elements_1_html = elements_1.replace("\n", "<br>")
                            st.markdown(f'<div class="doc-box">{elements_1_html}</div>', unsafe_allow_html=True)
                        with ecol2:
                            st.markdown(f"#### {t('doc2_label')}")
                            elements_2_html = elements_2.replace("\n", "<br>")
                            st.markdown(f'<div class="doc-box">{elements_2_html}</div>', unsafe_allow_html=True)

                        st.markdown("---")
                        st.markdown(f"### {t('results_header')}")
                        
                        result_html = result.replace("\n", "<br>")
                        st.markdown(f'<div class="result-box">{result_html}</div>', unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.download_button(
                            label=t("download_btn"),
                            data=result,
                            file_name="Tabayyun_Document_Analysis_Report.md",
                            mime="text/markdown",
                        )
                    except Exception as e:
                        status.update(label=t("status_failed_label"), state="error", expanded=True)
                        st.error(f"{t('error_during_analysis_prefix')} {e}")

# ==========================================
# Tab 3: About — corrected content, now bilingual
# ==========================================
with tab3:
    st.markdown(f"### {t('about_title')}")
    st.markdown(t("about_intro"))

    st.markdown(f"#### {t('problem_header')}")
    for item in L["problem_items"][st.session_state.lang]:
        st.markdown(f"- {item}")

    st.markdown(f"#### {t('solution_header')}")
    st.markdown(t("solution_text"))

    st.markdown(f"#### {t('advantages_header')}")
    for item in L["advantages_items"][st.session_state.lang]:
        st.markdown(f"- {item}")

    st.markdown("---")
    st.markdown(f"### {t('contact_header')}")
    st.markdown(t("github_line"))
    st.markdown("---")
    st.caption(t("footer"))