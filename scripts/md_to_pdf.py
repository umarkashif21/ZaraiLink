"""
Convert SEARCH_ENGINE_DEEP_ANALYSIS.md → styled PDF using weasyprint.
One-off script for the deep analysis report.
"""
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "SEARCH_ENGINE_DEEP_ANALYSIS.md"
PDF_PATH = ROOT / "SEARCH_ENGINE_DEEP_ANALYSIS.pdf"

md_text = MD_PATH.read_text()

# Convert markdown → HTML
md = markdown.Markdown(
    extensions=[
        "extra",
        "tables",
        "fenced_code",
        "codehilite",
        "toc",
        "sane_lists",
    ],
    extension_configs={
        "codehilite": {"css_class": "highlight", "guess_lang": False},
        "toc": {"title": "Table of Contents", "permalink": False},
    },
)
body_html = md.convert(md_text)

# Full HTML shell with inline CSS
html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Zarailink Search Engine — Exhaustive Integrated Analysis</title>
</head>
<body>

<header class="cover">
  <div class="brand">ZARAILINK</div>
  <h1 class="cover-title">Search Engine</h1>
  <h2 class="cover-subtitle">Exhaustive Integrated Analysis</h2>
  <div class="cover-meta">
    <div>Technical Deep Dive</div>
    <div>{date.today().isoformat()}</div>
  </div>
</header>

<main>
{body_html}
</main>

</body>
</html>"""

css = CSS(
    string=r"""
@page {
    size: A4;
    margin: 2cm 1.8cm 2.2cm 1.8cm;

    @bottom-center {
        content: "Zarailink Search Engine — Exhaustive Integrated Analysis";
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 8pt;
        color: #888;
    }
    @bottom-right {
        content: "Page " counter(page) " / " counter(pages);
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 8pt;
        color: #888;
    }
}

@page :first {
    margin: 0;
    @bottom-center { content: none; }
    @bottom-right { content: none; }
}

html, body {
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-size: 10.5pt;
    line-height: 1.55;
    color: #222;
    hyphens: auto;
}

/* ── Cover ────────────────────────────────────── */
.cover {
    page: cover;
    page-break-after: always;
    background: linear-gradient(135deg, #0b3d2e 0%, #14532d 50%, #166534 100%);
    color: #fff;
    padding: 5cm 3cm;
    min-height: 29.7cm;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin: 0;
}
.brand {
    font-size: 13pt;
    letter-spacing: 0.4em;
    color: #bbf7d0;
    margin-bottom: 1.5cm;
    font-weight: 700;
}
.cover-title {
    font-size: 48pt;
    font-weight: 900;
    margin: 0 0 0.3em 0;
    line-height: 1.1;
    border: none;
    padding: 0;
    color: #fff;
}
.cover-subtitle {
    font-size: 22pt;
    font-weight: 400;
    color: #d1fae5;
    margin: 0 0 3cm 0;
    border: none;
    padding: 0;
}
.cover-meta {
    font-size: 11pt;
    color: #d1fae5;
    border-top: 2px solid rgba(255,255,255,0.3);
    padding-top: 1em;
    display: flex;
    justify-content: space-between;
}

/* ── Typography ───────────────────────────────── */
h1 {
    font-size: 22pt;
    color: #0b3d2e;
    border-bottom: 3px solid #166534;
    padding-bottom: 0.25em;
    margin-top: 1.5em;
    margin-bottom: 0.6em;
    page-break-after: avoid;
    page-break-before: always;
}
h1:first-of-type { page-break-before: auto; }

h2 {
    font-size: 16pt;
    color: #14532d;
    border-bottom: 1.5px solid #bbf7d0;
    padding-bottom: 0.2em;
    margin-top: 1.4em;
    margin-bottom: 0.5em;
    page-break-after: avoid;
}
h3 {
    font-size: 13pt;
    color: #166534;
    margin-top: 1.2em;
    margin-bottom: 0.4em;
    page-break-after: avoid;
}
h4 {
    font-size: 11.5pt;
    color: #374151;
    margin-top: 1em;
    margin-bottom: 0.3em;
    page-break-after: avoid;
}

p { margin: 0.5em 0; }

strong { color: #0b3d2e; }

/* ── Links ────────────────────────────────────── */
a {
    color: #166534;
    text-decoration: none;
    border-bottom: 1px dotted #86efac;
}
a:hover { color: #064e3b; }

/* ── Lists ────────────────────────────────────── */
ul, ol {
    margin: 0.5em 0 0.5em 0;
    padding-left: 1.6em;
}
li { margin: 0.2em 0; }
li p { margin: 0.2em 0; }

/* ── Code ─────────────────────────────────────── */
code {
    font-family: 'Courier New', 'Courier', monospace;
    font-size: 9.5pt;
    background: #f3f4f6;
    color: #be185d;
    padding: 1px 5px;
    border-radius: 3px;
    border: 1px solid #e5e7eb;
}
pre {
    background: #1f2937;
    color: #f3f4f6;
    padding: 12px 16px;
    border-radius: 5px;
    border-left: 4px solid #166534;
    overflow-x: auto;
    font-size: 9pt;
    line-height: 1.5;
    margin: 0.8em 0;
    page-break-inside: avoid;
}
pre code {
    background: transparent;
    color: inherit;
    padding: 0;
    border: none;
    font-size: inherit;
}

/* pygments highlights */
.highlight .k, .highlight .kd { color: #c084fc; font-weight: bold; }
.highlight .n { color: #f3f4f6; }
.highlight .s, .highlight .s1, .highlight .s2 { color: #86efac; }
.highlight .c, .highlight .c1 { color: #9ca3af; font-style: italic; }
.highlight .mi, .highlight .mf { color: #fbbf24; }

/* ── Tables ───────────────────────────────────── */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 0.8em 0;
    font-size: 9.5pt;
    page-break-inside: auto;
}
thead {
    background: #166534;
    color: #fff;
}
th {
    padding: 8px 10px;
    text-align: left;
    font-weight: 700;
    border: 1px solid #14532d;
}
td {
    padding: 7px 10px;
    border: 1px solid #e5e7eb;
    vertical-align: top;
}
tbody tr:nth-child(even) { background: #f9fafb; }
tbody tr:hover { background: #f0fdf4; }

/* ── Blockquotes ──────────────────────────────── */
blockquote {
    border-left: 4px solid #166534;
    background: #f0fdf4;
    margin: 0.8em 0;
    padding: 0.6em 1em;
    color: #14532d;
    font-style: italic;
    page-break-inside: avoid;
}

/* ── Horizontal rules ─────────────────────────── */
hr {
    border: none;
    border-top: 1.5px dashed #86efac;
    margin: 1.5em 0;
}

/* ── Table of contents ────────────────────────── */
.toc {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 6px;
    padding: 1em 1.5em;
    margin: 1em 0 2em 0;
    page-break-after: always;
}
.toc > .toctitle {
    font-size: 15pt;
    font-weight: 700;
    color: #0b3d2e;
    margin-bottom: 0.6em;
    display: block;
}
.toc ul {
    list-style: none;
    padding-left: 1em;
    margin: 0.2em 0;
}
.toc > ul { padding-left: 0; }
.toc li { margin: 0.2em 0; font-size: 10pt; }
.toc a {
    color: #166534;
    border: none;
}

/* Avoid breaking headings from their first paragraph */
h1 + p, h2 + p, h3 + p, h4 + p { page-break-before: avoid; }
"""
)

HTML(string=html_doc, base_url=str(ROOT)).write_pdf(str(PDF_PATH), stylesheets=[css])
print(f"Generated: {PDF_PATH}")
print(f"Size: {PDF_PATH.stat().st_size / 1024:.1f} KB")
