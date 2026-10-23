import base64
import io
from pathlib import Path
import re

import markdown
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import weasyprint

MATH_CACHE = {}


def render_latex_to_base64_png(tex: str, is_display=False) -> str:
    """Renderuje formule LaTeX do przezroczystego obrazu PNG zakodowanego w base64."""
    clean_tex = tex.strip()
    cache_key = (clean_tex, is_display)
    if cache_key in MATH_CACHE:
        return MATH_CACHE[cache_key]

    # Ujednolicenie i czyszczenie pod silnik mathtext w matplotlib
    tex_prepared = clean_tex
    tex_prepared = re.sub(r'\\text\{([^}]+)\}', r'\\mathrm{\1}', tex_prepared)
    tex_prepared = re.sub(r'\\ge\b', r'\\geq', tex_prepared)
    tex_prepared = re.sub(r'\\le\b', r'\\leq', tex_prepared)
    tex_prepared = tex_prepared.replace(r'\big(', '(').replace(r'\big)', ')')
    tex_prepared = tex_prepared.replace(r'\left\lceil', r'\lceil').replace(r'\right\rceil', r'\rceil')
    tex_prepared = tex_prepared.replace(r'\left', '').replace(r'\right', '')

    if not tex_prepared.startswith('$'):
        tex_prepared = f"${tex_prepared}$"

    try:
        fig = plt.figure(figsize=(0.1, 0.1), dpi=260)
        fig.patch.set_alpha(0)

        fontsize = 12 if is_display else 9.5
        t = fig.text(0, 0, tex_prepared, fontsize=fontsize)
        fig.canvas.draw()
        bbox = t.get_window_extent()
        width_in = bbox.width / fig.dpi
        height_in = bbox.height / fig.dpi
        fig.set_size_inches(max(width_in + 0.04, 0.1), max(height_in + 0.04, 0.1))
        t.set_position((0.02, 0.02))

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=260, transparent=True, bbox_inches="tight", pad_inches=0.01)
        plt.close(fig)

        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        MATH_CACHE[cache_key] = b64
        return b64
    except Exception as exc:
        print(f"Ostrzeżenie: Nie udało się zrenderować formuły: {clean_tex} ({exc})")
        return None


def latex_to_html(tex: str) -> str:
    """Konwertuje proste wyrażenia matematyczne LaTeX na semantyczny HTML i symbole Unicode."""
    s = tex.strip()
    if any(k in s for k in [r"\sum", r"\frac", r"\sqrt", r"\int", r"\prod"]):
        return None

    s = s.replace(r"\ge", "&ge;").replace(r"\geq", "&ge;")
    s = s.replace(r"\le", "&le;").replace(r"\leq", "&le;")
    s = s.replace(r"\in", "&isin;")
    s = s.replace(r"\times", "&times;")
    s = s.replace(r"\cdot", "&middot;")
    s = s.replace(r"\dots", "&hellip;")
    s = s.replace(r"\approx", "&asymp;")
    s = s.replace(r"\%", "%")
    s = s.replace(r"\quad", " &nbsp; ")
    s = s.replace(r"\{", "{").replace(r"\}", "}")
    s = s.replace(r"\|", "&#124;").replace("|", "&#124;")

    s = s.replace(r"\sigma", "&sigma;")
    s = s.replace(r"\delta", "&delta;")
    s = s.replace(r"\Delta", "&Delta;")
    s = s.replace(r"\lambda", "&lambda;")

    s = s.replace(r"\min", "min").replace(r"\max", "max")
    s = re.sub(r"\\(?:text|mathrm)\{([^}]+)\}", r"\1", s)
    s = re.sub(r"\\bar\{([^}]+)\}", r'<span style="text-decoration: overline;">\1</span>', s)

    s = re.sub(r"_\{([^}]+)\}", r"<sub>\1</sub>", s)
    s = re.sub(r"_([a-zA-Z0-9*+-]+)", r"<sub>\1</sub>", s)

    s = re.sub(r"\^\{([^}]+)\}", r"<sup>\1</sup>", s)
    s = re.sub(r"\^([a-zA-Z0-9*+-]+)", r"<sup>\1</sup>", s)

    # Pochylenie pojedynczych zmiennych (np. N, x, f, k, m, d) z pominięciem tagów HTML
    tokens = re.split(r"(<[^>]+>|&[a-zA-Z]+;)", s)
    out = []
    for tok in tokens:
        if tok.startswith("<") or tok.startswith("&"):
            out.append(tok)
        else:
            t = re.sub(r"\b([a-zA-Z])\b", r"<em>\1</em>", tok)
            out.append(t)
    return f'<span class="math-inline-text">{"".join(out)}</span>'


def fix_markdown_lists(text: str) -> str:
    """Upewnia się, że przed każdą listą Markdown znajduje się pusta linia oraz normalizuje wcięcia podlist."""
    lines = text.split("\n")
    fixed = []
    list_item_re = re.compile(r"^(\s*)([-*+]|\d+\.)\s+")

    for i, raw_line in enumerate(lines):
        # Normalizacja 1-3 spacji na początku podlist do standardowych 4 spacji wymaganych przez Markdown
        line = re.sub(r"^[ ]{1,3}([-*+])\s+", r"    \1 ", raw_line)

        if i > 0:
            prev = fixed[-1]
            if list_item_re.match(line):
                # Jeśli poprzednia linia to nie pusta linia i nie element listy tego samego poziomu
                if prev.strip() != "" and not list_item_re.match(prev):
                    fixed.append("")
        fixed.append(line)
    return "\n".join(fixed)


def process_math_in_markdown(md_text: str) -> str:
    """Wyszukuje bloki $$...$$ oraz $...$ i zamienia je na HTML lub obrazy."""
    # 1. Zabezpieczenie bloków kodu ```...``` oraz inline `...`
    code_blocks = []

    def save_code_block(match):
        code_blocks.append(match.group(0))
        return f"<!--CODE_BLOCK_{len(code_blocks)-1}-->"

    text = re.sub(r"```.*?```", save_code_block, md_text, flags=re.DOTALL)
    text = re.sub(r"`[^`\n]+`", save_code_block, text)

    # 2. Blokowe wzory matematyczne $$...$$
    def replace_display_math(match):
        formula = match.group(1).strip()
        b64 = render_latex_to_base64_png(formula, is_display=True)
        if b64:
            return (
                f'<div class="math-display">'
                f'<img src="data:image/png;base64,{b64}" alt="{formula}" />'
                f"</div>"
            )
        return f'<div class="math-display"><code>{formula}</code></div>'

    text = re.sub(r"\$\$(.*?)\$\$", replace_display_math, text, flags=re.DOTALL)

    # 3. Liniowe wzory matematyczne $...$
    def replace_inline_math(match):
        formula = match.group(1).strip()
        html_math = latex_to_html(formula)
        if html_math:
            return html_math
        b64 = render_latex_to_base64_png(formula, is_display=False)
        if b64:
            return f'<img class="math-inline" src="data:image/png;base64,{b64}" alt="{formula}" />'
        return f"<em>{formula}</em>"

    text = re.sub(r"(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)", replace_inline_math, text)

    # 4. Przywrócenie bloków kodu
    for idx, block in enumerate(code_blocks):
        text = text.replace(f"<!--CODE_BLOCK_{idx}-->", block)

    return text


def convert_md_to_pdf(md_path: Path, pdf_path: Path):
    with md_path.open("r", encoding="utf-8") as f:
        md_content = f.read()

    # Zamiana brakujących obrazków na czytelne ramki-placeholdery w HTML
    def replace_img(match):
        alt = match.group(1)
        src = match.group(2)
        target = (md_path.parent / src).resolve()
        if target.exists():
            return f'<div class="img-wrapper"><img src="{target.as_uri()}" alt="{alt}" style="max-width: 90%; max-height: 280px; border-radius: 4px;" /></div>'
        return (
            f'<div class="img-placeholder">'
            f"<strong>[Miejsce na rysunek / wykres]</strong><br>"
            f"Plik docelowy: <code>{src}</code><br>"
            f"Podpis: <em>{alt}</em>"
            f"</div>"
        )

    # 1. Obrazki
    content = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_img, md_content)

    # 2. Poprawka formatowania list w Markdown (zapewnienie pustej linii przed listą)
    content = fix_markdown_lists(content)

    # 3. Renderowanie wzorów matematycznych
    content = process_math_in_markdown(content)

    # 4. Konwersja Markdown na HTML
    html_body = markdown.markdown(
        content,
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
    )

    full_html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<title>Sprawozdanie - Algorytm Genetyczny</title>
<style>
    @page {{
        size: A4;
        margin: 20mm 15mm 20mm 15mm;
        @bottom-right {{
            content: "Strona " counter(page);
            font-size: 8pt;
            font-family: 'Liberation Sans', 'DejaVu Sans', sans-serif;
            color: #666;
        }}
        @bottom-left {{
            content: "Projekt 1 – Klasyczny Algorytm Genetyczny";
            font-size: 8pt;
            font-family: 'Liberation Sans', 'DejaVu Sans', sans-serif;
            color: #666;
        }}
    }}

    body {{
        font-family: 'Liberation Sans', 'DejaVu Sans', sans-serif;
        font-size: 9.5pt;
        line-height: 1.45;
        color: #222;
    }}

    h1 {{
        font-size: 17pt;
        color: #0b3c5d;
        border-bottom: 2px solid #0b3c5d;
        padding-bottom: 4px;
        margin-top: 0;
        margin-bottom: 12px;
    }}

    h2 {{
        font-size: 12.5pt;
        color: #1d2731;
        border-bottom: 1px solid #ccc;
        padding-bottom: 3px;
        margin-top: 16px;
        margin-bottom: 8px;
        page-break-after: avoid;
    }}

    h3 {{
        font-size: 11pt;
        color: #328cc1;
        margin-top: 13px;
        margin-bottom: 6px;
        page-break-after: avoid;
    }}

    h4 {{
        font-size: 10pt;
        color: #1d2731;
        margin-top: 10px;
        margin-bottom: 5px;
        page-break-after: avoid;
    }}

    p {{
        margin: 5px 0;
        text-align: justify;
    }}

    ul, ol {{
        margin: 6px 0 6px 20px;
        padding: 0;
    }}

    li {{
        margin-bottom: 6px;
        text-align: justify;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 8.5pt;
        page-break-inside: avoid;
    }}

    th, td {{
        border: 1px solid #bbb;
        padding: 4px 6px;
        text-align: left;
    }}

    th {{
        background-color: #f2f5f8;
        color: #0b3c5d;
        font-weight: bold;
    }}

    tr:nth-child(even) {{
        background-color: #fafbfc;
    }}

    code {{
        font-family: 'Liberation Mono', 'DejaVu Sans Mono', monospace;
        font-size: 8pt;
        background-color: #f0f2f5;
        padding: 1px 3px;
        border-radius: 3px;
        color: #b30000;
    }}

    pre {{
        background-color: #f7f9fa;
        border: 1px solid #e1e4e8;
        border-left: 4px solid #328cc1;
        padding: 6px 10px;
        border-radius: 3px;
        overflow-x: auto;
        font-size: 8pt;
        margin: 6px 0;
        page-break-inside: avoid;
    }}

    pre code {{
        background: none;
        padding: 0;
        color: #24292e;
    }}

    hr {{
        border: 0;
        border-top: 1px solid #ddd;
        margin: 14px 0;
    }}

    .img-wrapper {{
        text-align: center;
        margin: 10px 0;
        page-break-inside: avoid;
    }}

    .img-placeholder {{
        border: 2px dashed #999;
        background-color: #f8f9fa;
        padding: 12px;
        text-align: center;
        color: #555;
        margin: 8px 0;
        border-radius: 4px;
        font-size: 8.5pt;
        page-break-inside: avoid;
    }}

    .math-display {{
        text-align: center;
        margin: 8px 0;
        padding: 4px 0;
        page-break-inside: avoid;
    }}

    .math-display img {{
        max-height: 38px;
        vertical-align: middle;
    }}

    .math-inline {{
        vertical-align: -2.5px;
        max-height: 15px;
        margin: 0 1px;
    }}

    .math-inline-text {{
        font-family: 'Liberation Serif', 'DejaVu Serif', 'Times New Roman', serif;
        font-size: 10pt;
    }}

    .math-inline-text em {{
        font-style: italic;
    }}

    .math-inline-text sub, .math-inline-text sup {{
        font-size: 72%;
        line-height: 0;
        position: relative;
        vertical-align: baseline;
    }}

    .math-inline-text sup {{
        top: -0.45em;
    }}

    .math-inline-text sub {{
        bottom: -0.22em;
    }}

    strong {{
        color: #111;
    }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

    weasyprint.HTML(string=full_html, base_url=str(md_path.parent)).write_pdf(str(pdf_path))
    print(f"Pomyślnie wygenerowano raport PDF ze wzorami matematycznymi: {pdf_path}")


if __name__ == "__main__":
    report_dir = Path(__file__).resolve().parent
    md_file = report_dir / "sprawozdanie.md"
    pdf_file = report_dir / "sprawozdanie.pdf"
    convert_md_to_pdf(md_file, pdf_file)
