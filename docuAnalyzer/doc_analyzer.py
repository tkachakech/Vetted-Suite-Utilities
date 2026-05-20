"""
╔══════════════════════════════════════════════════════════════════╗
║         DOCPULSE — Local Document Intelligence Suite            ║
║                  Single-file Streamlit App                       ║
╠══════════════════════════════════════════════════════════════════╣
║  SETUP:                                                          ║
║    pip install streamlit pypdf2 pandas matplotlib                ║
║                                                                  ║
║  RUN:                                                            ║
║    streamlit run doc_analyzer.py                                 ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import time
import io
import re
import math
import hashlib
from collections import Counter
from datetime import datetime

# ── Optional dependencies (fail gracefully) ─────────────────────
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    CHART_SUPPORT = True
except ImportError:
    CHART_SUPPORT = False

# ════════════════════════════════════════════════════════════════
#  THEME INJECTION  (one place to restyle the whole app)
# ════════════════════════════════════════════════════════════════
CUSTOM_CSS = """
<style>
/* ── Fonts ─────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Root palette ────────────────────────────────────────────── */
:root {
    --ink:        #0f0f13;
    --surface:    #17171f;
    --panel:      #1e1e2a;
    --border:     #2e2e40;
    --accent:     #7c6ff7;
    --accent2:    #f07c4a;
    --success:    #4ade80;
    --muted:      #6b6b85;
    --text:       #e8e8f0;
    --text-dim:   #9090a8;
}

/* ── Global canvas ──────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--ink) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Sidebar ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Top-bar strip ───────────────────────────────────────────── */
.topbar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 18px 0 10px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
}
.topbar-logo {
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem;
    color: var(--accent);
    letter-spacing: -0.5px;
}
.topbar-badge {
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 0.65rem;
    font-family: 'DM Mono', monospace;
    padding: 2px 8px;
    border-radius: 100px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── Section headings ────────────────────────────────────────── */
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--muted);
    margin: 28px 0 10px;
}

/* ── Stat cards ──────────────────────────────────────────────── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
    margin: 12px 0;
}
.stat-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.stat-value {
    font-family: 'DM Mono', monospace;
    font-size: 1.6rem;
    font-weight: 500;
    color: var(--text);
    line-height: 1;
    margin-bottom: 4px;
}
.stat-label {
    font-size: 0.72rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.stat-delta {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: var(--success);
    margin-top: 6px;
}

/* ── Info pills ──────────────────────────────────────────────── */
.pill-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
.pill {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 100px;
    padding: 4px 12px;
    font-size: 0.72rem;
    font-family: 'DM Mono', monospace;
    color: var(--text-dim);
}
.pill span { color: var(--text); }

/* ── Preview box ─────────────────────────────────────────────── */
.preview-box {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    line-height: 1.7;
    color: var(--text-dim);
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 340px;
    overflow-y: auto;
}
.preview-box .highlight { color: var(--accent); }

/* ── Word-frequency rows ─────────────────────────────────────── */
.freq-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0;
    border-bottom: 1px solid var(--border);
}
.freq-word {
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    color: var(--text);
    width: 120px;
    flex-shrink: 0;
}
.freq-bar-wrap { flex: 1; background: var(--surface); border-radius: 4px; height: 6px; }
.freq-bar { height: 6px; border-radius: 4px;
            background: linear-gradient(90deg, var(--accent), var(--accent2)); }
.freq-count {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--text-dim);
    width: 36px;
    text-align: right;
}

/* ── Alert banner ────────────────────────────────────────────── */
.alert-info {
    background: rgba(124,111,247,0.10);
    border: 1px solid rgba(124,111,247,0.30);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.82rem;
    color: var(--text-dim);
    margin: 12px 0;
}
.alert-warn {
    background: rgba(240,124,74,0.10);
    border: 1px solid rgba(240,124,74,0.30);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.82rem;
    color: var(--text-dim);
    margin: 12px 0;
}

/* ── File-upload zone ────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: var(--panel) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: 12px !important;
}

/* ── Metric overrides ────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 16px;
}
[data-testid="stMetricLabel"] { color: var(--text-dim) !important; font-size: 0.72rem !important; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-family: 'DM Mono', monospace !important; }
[data-testid="stMetricDelta"] { color: var(--success) !important; }

/* ── Expander ────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    background: var(--panel) !important;
}

/* ── Progress bar ────────────────────────────────────────────── */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
}

/* ── Buttons ─────────────────────────────────────────────────── */
[data-testid="stButton"] > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
    transition: opacity 0.15s !important;
}
[data-testid="stButton"] > button:hover { opacity: 0.85 !important; }

/* ── Selectbox & radio ───────────────────────────────────────── */
[data-testid="stSelectbox"] select,
[data-testid="stRadio"] label { color: var(--text) !important; }

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── Divider ─────────────────────────────────────────────────── */
hr { border-color: var(--border) !important; margin: 20px 0 !important; }
</style>
"""

# ════════════════════════════════════════════════════════════════
#  ANALYSIS PIPELINE  ── add more stages here freely
# ════════════════════════════════════════════════════════════════

class DocumentAnalyzer:
    """
    Stateless analysis pipeline.
    Add a new @staticmethod to extend analysis; call it from `analyze()`.
    """

    # ── 1. Extraction ────────────────────────────────────────────
    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> tuple[str, dict]:
        """Return (raw_text, extraction_meta)."""
        ext = filename.rsplit(".", 1)[-1].lower()
        meta = {"extension": ext, "raw_bytes": len(file_bytes)}

        if ext == "pdf":
            if not PDF_SUPPORT:
                return "", {"error": "PyPDF2 not installed. Run: pip install pypdf2"}
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            meta["page_count"] = len(reader.pages)
            meta["pdf_info"] = reader.metadata or {}
            return "\n".join(pages), meta

        # Treat everything else as plain text
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                text = file_bytes.decode(enc)
                meta["encoding"] = enc
                return text, meta
            except UnicodeDecodeError:
                continue
        return file_bytes.decode("utf-8", errors="replace"), meta

    # ── 2. Text statistics ───────────────────────────────────────
    @staticmethod
    def text_stats(text: str) -> dict:
        words       = re.findall(r"\b\w+\b", text)
        sentences   = re.split(r"[.!?]+", text)
        sentences   = [s.strip() for s in sentences if len(s.strip()) > 3]
        paragraphs  = [p for p in text.split("\n\n") if p.strip()]
        lines       = text.splitlines()
        unique_words = set(w.lower() for w in words)

        word_count   = len(words)
        char_count   = len(text)
        char_no_sp   = len(text.replace(" ", ""))
        sent_count   = len(sentences)
        para_count   = len(paragraphs)
        avg_word_len = (sum(len(w) for w in words) / word_count) if word_count else 0
        avg_sent_len = (word_count / sent_count) if sent_count else 0
        lexical_div  = (len(unique_words) / word_count * 100) if word_count else 0

        # Flesch reading ease (approx)
        syllables    = sum(DocumentAnalyzer._count_syllables(w) for w in words)
        if word_count > 0 and sent_count > 0:
            flesch = (206.835
                      - 1.015 * (word_count / sent_count)
                      - 84.6  * (syllables / word_count))
            flesch = max(0, min(100, round(flesch, 1)))
        else:
            flesch = 0

        # Estimated reading time (avg 238 wpm)
        read_minutes = word_count / 238
        read_str = (f"{math.floor(read_minutes)}m {round((read_minutes % 1) * 60)}s"
                    if read_minutes >= 1 else f"{round(read_minutes * 60)}s")

        return {
            "word_count":    word_count,
            "char_count":    char_count,
            "char_no_space": char_no_sp,
            "sentence_count": sent_count,
            "paragraph_count": para_count,
            "line_count":    len(lines),
            "unique_words":  len(unique_words),
            "lexical_diversity": round(lexical_div, 1),
            "avg_word_length": round(avg_word_len, 2),
            "avg_sentence_length": round(avg_sent_len, 1),
            "flesch_score":  flesch,
            "reading_time":  read_str,
        }

    # ── 3. Word frequency ────────────────────────────────────────
    @staticmethod
    def word_frequency(text: str, top_n: int = 20) -> list[tuple[str, int]]:
        STOPWORDS = {
            "the","a","an","and","or","but","in","on","at","to","for","of",
            "is","it","its","be","was","are","were","been","has","have","had",
            "that","this","with","from","by","as","up","not","can","all","we",
            "he","she","they","our","your","their","my","his","her","i","you",
            "do","did","does","will","would","could","should","may","might",
            "if","so","then","than","more","also","no","into","about","what",
            "which","who","how","when","there","here","out","one","two","new",
        }
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        filtered = [w for w in words if w not in STOPWORDS]
        return Counter(filtered).most_common(top_n)

    # ── 4. Fingerprint / file metadata ──────────────────────────
    @staticmethod
    def file_metadata(file_bytes: bytes, filename: str) -> dict:
        size_bytes = len(file_bytes)
        size_kb    = round(size_bytes / 1024, 2)
        size_mb    = round(size_bytes / (1024 * 1024), 4)
        sha256     = hashlib.sha256(file_bytes).hexdigest()
        return {
            "filename":   filename,
            "size_bytes": size_bytes,
            "size_kb":    size_kb,
            "size_mb":    size_mb,
            "sha256":     sha256,
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ── 5. Master orchestrator ───────────────────────────────────
    @staticmethod
    def analyze(file_bytes: bytes, filename: str,
                progress_cb=None) -> dict:
        """
        Run all pipeline stages.
        progress_cb(pct: float, label: str) is called at each stage.
        Returns a single result dict consumed by the UI layer.
        """
        def tick(pct, label):
            if progress_cb:
                progress_cb(pct, label)
            time.sleep(0.35)   # theatrical pause ✨

        tick(0.10, "Reading file…")
        file_meta = DocumentAnalyzer.file_metadata(file_bytes, filename)

        tick(0.30, "Extracting text…")
        text, extraction_meta = DocumentAnalyzer.extract_text(file_bytes, filename)

        tick(0.55, "Computing statistics…")
        stats = DocumentAnalyzer.text_stats(text) if text else {}

        tick(0.75, "Building word frequency…")
        freq = DocumentAnalyzer.word_frequency(text) if text else []

        tick(0.90, "Generating preview…")
        preview = text[:3000] if text else "(No extractable text found)"

        tick(1.00, "Done")
        return {
            "file_meta":      file_meta,
            "extraction_meta": extraction_meta,
            "text":           text,
            "stats":          stats,
            "word_freq":      freq,
            "preview":        preview,
        }

    # ── Helper ───────────────────────────────────────────────────
    @staticmethod
    def _count_syllables(word: str) -> int:
        word = word.lower()
        count = len(re.findall(r'[aeiouy]+', word))
        if word.endswith("e") and count > 1:
            count -= 1
        return max(1, count)


# ════════════════════════════════════════════════════════════════
#  UI HELPERS
# ════════════════════════════════════════════════════════════════

def fmt_number(n: int | float) -> str:
    return f"{n:,}" if isinstance(n, int) else f"{n:,.2f}"

def flesch_label(score: float) -> str:
    if score >= 90: return "Very Easy"
    if score >= 80: return "Easy"
    if score >= 70: return "Fairly Easy"
    if score >= 60: return "Standard"
    if score >= 50: return "Fairly Difficult"
    if score >= 30: return "Difficult"
    return "Very Difficult"

def render_stat_cards(items: list[tuple[str, str, str | None]]) -> str:
    """items = [(value, label, delta_or_None), ...]"""
    cards = ""
    for value, label, delta in items:
        delta_html = f'<div class="stat-delta">▲ {delta}</div>' if delta else ""
        cards += f"""
        <div class="stat-card">
          <div class="stat-value">{value}</div>
          <div class="stat-label">{label}</div>
          {delta_html}
        </div>"""
    return f'<div class="stat-grid">{cards}</div>'

def render_freq_bars(freq: list[tuple[str, int]]) -> str:
    if not freq:
        return ""
    max_count = freq[0][1]
    rows = ""
    for word, count in freq:
        pct = round(count / max_count * 100)
        rows += f"""
        <div class="freq-row">
          <div class="freq-word">{word}</div>
          <div class="freq-bar-wrap">
            <div class="freq-bar" style="width:{pct}%"></div>
          </div>
          <div class="freq-count">{count}</div>
        </div>"""
    return rows

def render_pills(pairs: list[tuple[str, str]]) -> str:
    pills = "".join(
        f'<div class="pill">{k}&nbsp;&nbsp;<span>{v}</span></div>'
        for k, v in pairs
    )
    return f'<div class="pill-row">{pills}</div>'


# ════════════════════════════════════════════════════════════════
#  PAGE: ANALYSIS RESULTS
# ════════════════════════════════════════════════════════════════

def render_results(result: dict):
    fm   = result["file_meta"]
    em   = result["extraction_meta"]
    st_  = result["stats"]
    freq = result["word_freq"]
    prev = result["preview"]

    # ── Header ──────────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin-bottom:6px">
      <span style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:var(--accent)">
        {fm['filename']}
      </span>
      &nbsp;&nbsp;
      <span style="font-family:'DM Mono',monospace;font-size:0.7rem;
                   color:var(--text-dim);background:var(--panel);
                   border:1px solid var(--border);padding:2px 8px;border-radius:100px">
        {em.get('extension','?').upper()}
      </span>
    </div>
    <div style="font-size:0.75rem;color:var(--text-dim);
                font-family:'DM Mono',monospace;margin-bottom:20px">
      Analyzed {fm['analyzed_at']}
    </div>
    """, unsafe_allow_html=True)

    # ── Key metrics ──────────────────────────────────────────────
    st.markdown('<p class="section-label">Core Statistics</p>', unsafe_allow_html=True)

    wc   = st_.get("word_count", 0)
    cc   = st_.get("char_count", 0)
    sc   = st_.get("sentence_count", 0)
    pc   = st_.get("paragraph_count", 0)
    rt   = st_.get("reading_time", "–")
    fl   = st_.get("flesch_score", 0)

    cards_html = render_stat_cards([
        (fmt_number(wc),   "Words",       None),
        (fmt_number(cc),   "Characters",  None),
        (fmt_number(sc),   "Sentences",   None),
        (fmt_number(pc),   "Paragraphs",  None),
        (rt,               "Reading Time",None),
        (str(fl),          f"Readability ({flesch_label(fl)})", None),
    ])
    st.markdown(cards_html, unsafe_allow_html=True)

    # ── Secondary stats in native Streamlit metrics ──────────────
    st.markdown('<p class="section-label">Vocabulary & Style</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unique Words",    fmt_number(st_.get("unique_words", 0)))
    c2.metric("Lexical Diversity", f"{st_.get('lexical_diversity', 0)}%")
    c3.metric("Avg Word Length", st_.get("avg_word_length", 0))
    c4.metric("Avg Sent. Length", f"{st_.get('avg_sentence_length', 0)} words")

    st.markdown("---")

    # ── Two-column lower section ─────────────────────────────────
    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        st.markdown('<p class="section-label">Content Preview</p>',
                    unsafe_allow_html=True)
        # Highlight first 200 chars
        safe_prev = prev.replace("<", "&lt;").replace(">", "&gt;")
        snippet   = safe_prev[:200]
        rest      = safe_prev[200:]
        st.markdown(
            f'<div class="preview-box"><span class="highlight">{snippet}</span>{rest}</div>',
            unsafe_allow_html=True
        )

    with right:
        st.markdown('<p class="section-label">Top Words</p>',
                    unsafe_allow_html=True)
        if freq:
            top_n = st.slider("Show top N words", 5, 20, 15,
                              key="top_n_slider", label_visibility="collapsed")
            st.markdown(render_freq_bars(freq[:top_n]), unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="alert-warn">No word frequency data available.</div>',
                unsafe_allow_html=True
            )

    st.markdown("---")

    # ── File metadata expander ───────────────────────────────────
    with st.expander("🔍  File Metadata & Fingerprint", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<p class="section-label">Size</p>', unsafe_allow_html=True)
            pills_html = render_pills([
                ("Bytes",   fmt_number(fm["size_bytes"])),
                ("KB",      str(fm["size_kb"])),
                ("MB",      str(fm["size_mb"])),
            ])
            st.markdown(pills_html, unsafe_allow_html=True)

            if em.get("page_count"):
                st.markdown(
                    f'<div class="alert-info">📄 PDF — {em["page_count"]} pages extracted</div>',
                    unsafe_allow_html=True
                )
            if em.get("encoding"):
                st.markdown(
                    f'<div class="alert-info">🔤 Encoding detected: <b>{em["encoding"]}</b></div>',
                    unsafe_allow_html=True
                )

        with col_b:
            st.markdown('<p class="section-label">Integrity</p>',
                        unsafe_allow_html=True)
            sha = fm["sha256"]
            st.markdown(f"""
            <div style="font-family:'DM Mono',monospace;font-size:0.7rem;
                        background:var(--surface);border:1px solid var(--border);
                        border-radius:8px;padding:10px 14px;
                        color:var(--text-dim);word-break:break-all;line-height:1.8">
              <span style="color:var(--muted)">SHA-256</span><br>
              <span style="color:var(--accent)">{sha[:32]}</span>{sha[32:]}
            </div>""", unsafe_allow_html=True)

    # ── Raw text expander ────────────────────────────────────────
    with st.expander("📜  Full Extracted Text", expanded=False):
        char_limit = 15_000
        display_text = result["text"][:char_limit]
        truncated = len(result["text"]) > char_limit
        st.code(display_text, language="text")
        if truncated:
            st.markdown(
                f'<div class="alert-warn">⚠️ Showing first {char_limit:,} of '
                f'{len(result["text"]):,} characters.</div>',
                unsafe_allow_html=True
            )


# ════════════════════════════════════════════════════════════════
#  PAGE: COMPARE (stub — shows extensibility)
# ════════════════════════════════════════════════════════════════

def render_compare_page():
    st.markdown('<p class="section-label">Compare Documents</p>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="alert-info">🚧 Upload two documents on the <b>Analyze</b> page '
        'then return here to compare statistics side-by-side. '
        'Hook this function into <code>session_state["results"]</code> to extend it.</div>',
        unsafe_allow_html=True
    )


# ════════════════════════════════════════════════════════════════
#  PAGE: SETTINGS
# ════════════════════════════════════════════════════════════════

def render_settings_page():
    st.markdown('<p class="section-label">Preferences</p>', unsafe_allow_html=True)
    st.toggle("Show SHA-256 fingerprint", value=True, key="show_sha")
    st.toggle("Auto-expand full text", value=False, key="auto_expand")
    st.slider("Preview character limit", 500, 5000, 3000, step=100,
              key="preview_limit")
    st.markdown('<p class="section-label">About</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="alert-info">
      <b>DocPulse</b> v1.0.0 — local-first document intelligence.<br>
      All processing happens in-memory on your machine.
      No data is ever sent to external servers.<br><br>
      <span style="font-family:'DM Mono',monospace;font-size:0.7rem">
      Built with Streamlit · PyPDF2 · pure Python
      </span>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  MAIN APP
# ════════════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="DocPulse",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # ── Sidebar nav ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="padding:20px 0 10px">
          <div style="font-family:'DM Serif Display',serif;font-size:1.4rem;
                      color:#7c6ff7;letter-spacing:-0.5px">DocPulse</div>
          <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
                      color:#6b6b85;letter-spacing:0.12em;
                      text-transform:uppercase;margin-top:4px">
            Document Intelligence
          </div>
        </div>
        <hr style="border-color:#2e2e40;margin:0 0 16px">
        """, unsafe_allow_html=True)

        page = st.radio(
            "Navigation",
            ["⚡  Analyze", "⚖️  Compare", "⚙️  Settings"],
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if "results" in st.session_state and st.session_state.results:
            r = st.session_state.results
            st.markdown("""
            <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
                        text-transform:uppercase;letter-spacing:0.1em;
                        color:#6b6b85;margin-bottom:8px">Last File</div>
            """, unsafe_allow_html=True)
            st.markdown(
                render_pills([
                    ("File",  r["file_meta"]["filename"][:18] + "…"
                              if len(r["file_meta"]["filename"]) > 18
                              else r["file_meta"]["filename"]),
                    ("Words", fmt_number(r["stats"].get("word_count", 0))),
                    ("KB",    str(r["file_meta"]["size_kb"])),
                ]),
                unsafe_allow_html=True
            )

        # Dependency status
        st.markdown("<br>", unsafe_allow_html=True)
        pdf_status  = "🟢 Ready" if PDF_SUPPORT  else "🔴 pip install pypdf2"
        chart_status= "🟢 Ready" if CHART_SUPPORT else "🔴 pip install pandas matplotlib"
        st.markdown(f"""
        <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
                    color:#6b6b85;line-height:2">
          <div style="text-transform:uppercase;letter-spacing:0.1em;
                      margin-bottom:4px">Dependencies</div>
          PDF&nbsp;&nbsp;{pdf_status}<br>
          Charts&nbsp;{chart_status}
        </div>
        """, unsafe_allow_html=True)

    # ── Page routing ─────────────────────────────────────────────
    # Top bar
    st.markdown("""
    <div class="topbar">
      <span class="topbar-logo">DocPulse</span>
      <span class="topbar-badge">Local · Private · Fast</span>
    </div>
    """, unsafe_allow_html=True)

    if "⚙️" in page:
        render_settings_page()
        return
    if "⚖️" in page:
        render_compare_page()
        return

    # ── Analyze page ─────────────────────────────────────────────
    st.markdown('<p class="section-label">Upload a Document</p>',
                unsafe_allow_html=True)

    accepted = ["txt", "md", "csv", "json", "xml", "html", "py",
                "js", "ts", "css", "yaml", "toml", "rst"]
    if PDF_SUPPORT:
        accepted.insert(0, "pdf")

    uploaded = st.file_uploader(
        "Drag & drop or click to browse",
        type=accepted,
        label_visibility="collapsed",
    )

    if not uploaded:
        st.markdown("""
        <div class="alert-info" style="margin-top:20px;font-size:0.85rem">
          ⚡ &nbsp;Drop any text-based file above to begin analysis.
          Supported: <b>PDF, TXT, MD, CSV, JSON, XML, HTML, Python, JS, YAML</b> and more.
          Everything runs locally — nothing leaves your browser.
        </div>
        """, unsafe_allow_html=True)

        # Show stale results from a previous upload if they exist
        if "results" in st.session_state and st.session_state.results:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                '<div class="alert-info">📂 Showing results from previous session.</div>',
                unsafe_allow_html=True
            )
            render_results(st.session_state.results)
        return

    file_bytes = uploaded.read()
    filename   = uploaded.name

    # Re-use cached result for the same file
    cache_key  = hashlib.md5(file_bytes).hexdigest()
    if ("results" not in st.session_state
            or st.session_state.get("cache_key") != cache_key):

        # ── Progress UI ───────────────────────────────────────────
        status_slot = st.empty()
        bar_slot    = st.empty()
        progress_bar = bar_slot.progress(0)

        def progress_cb(pct: float, label: str):
            status_slot.markdown(
                f'<div style="font-family:\'DM Mono\',monospace;font-size:0.8rem;'
                f'color:#9090a8;margin-bottom:6px">⏳ {label}</div>',
                unsafe_allow_html=True
            )
            progress_bar.progress(pct)

        with st.spinner(""):
            result = DocumentAnalyzer.analyze(file_bytes, filename, progress_cb)

        status_slot.empty()
        bar_slot.empty()

        st.session_state.results   = result
        st.session_state.cache_key = cache_key

    render_results(st.session_state.results)


if __name__ == "__main__":
    main()
