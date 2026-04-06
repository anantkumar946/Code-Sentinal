"""
report.py — Terminal (colored) and HTML output for CodeSentinel findings.
"""

import os, html as _html
from datetime import datetime

try:
    from rich.console import Console
    from rich.rule import Rule
    from rich.panel import Panel
    console = Console()
    USE_RICH = True
except ImportError:
    USE_RICH = False

SEVERITY_COLOR = {
    "ERROR":   "bold red",
    "HIGH":    "red",
    "MEDIUM":  "yellow",
    "WARNING": "yellow",
    "INFO":    "cyan",
}

SEVERITY_BADGE = {
    "ERROR":   "#ef4444",
    "HIGH":    "#f97316",
    "MEDIUM":  "#eab308",
    "WARNING": "#eab308",
    "INFO":    "#38bdf8",
}


def print_terminal(findings):
    issues   = findings["issues"]
    score    = findings["score"]
    filepath = findings["file"]

    categories = ["Syntax", "Semantic", "Complexity", "Style", "Security"]

    if USE_RICH:
        console.print(Rule(f"[bold cyan]CodeSentinel — {os.path.basename(filepath)}[/bold cyan]"))
    else:
        print(f"\n=== CodeSentinel — {os.path.basename(filepath)} ===")

    for cat in categories:
        cat_issues = [i for i in issues if i["category"] == cat]
        if USE_RICH:
            console.print(f"\n[bold white]▸ {cat}[/bold white]")
        else:
            print(f"\n▸ {cat}")

        if not cat_issues:
            _print("  ✓ No issues", "INFO")
            continue
        for i in sorted(cat_issues, key=lambda x: x["line"] or 0):
            line_tag = f"[L{i['line']}] " if i["line"] else ""
            _print(f"  {line_tag}{i['message']}", i["severity"])

    # Score panel
    grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "F"
    color = "green" if score >= 80 else "yellow" if score >= 60 else "orange3" if score >= 40 else "red"
    if USE_RICH:
        console.print()
        console.print(Panel(f"[bold {color}]Health Score: {score}/100   Grade: {grade}[/bold {color}]",
                            title="Score", border_style=color))
    else:
        print(f"\n  Health Score: {score}/100  (Grade: {grade})\n")


def _print(msg, severity="INFO"):
    if USE_RICH:
        color = SEVERITY_COLOR.get(severity, "white")
        prefix = f"[{color}][{severity}][/{color}] " if severity != "INFO" else ""
        console.print(prefix + msg)
    else:
        print(f"[{severity}] {msg}")


def generate_html(findings, out="report.html"):
    issues   = findings["issues"]
    score    = findings["score"]
    filepath = findings["file"]

    grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "F"
    sc    = "#22c55e" if score >= 80 else "#eab308" if score >= 60 else "#f97316" if score >= 40 else "#ef4444"

    counts = {cat: len([i for i in issues if i["category"] == cat])
              for cat in ["Syntax", "Semantic", "Complexity", "Style", "Security"]}

    def rows(cat):
        items = [i for i in issues if i["category"] == cat]
        if not items:
            return '<p class="ok">✓ No issues found</p>'
        return "".join(
            f'<div class="row">'
            f'<span class="badge" style="background:{SEVERITY_BADGE.get(i["severity"],"#64748b")}">'
            f'{i["severity"]}</span>'
            f'<span class="ln">L{i["line"]}</span>'
            f'<span>{_html.escape(i["message"])}</span></div>'
            for i in sorted(items, key=lambda x: x["line"] or 0)
        )

    stats = "".join(
        f'<div class="stat"><div class="num">{counts[c]}</div><div class="lbl">{c}</div></div>'
        for c in counts
    )
    sections = "".join(
        f'<div class="card"><h2>{cat}</h2>{rows(cat)}</div>'
        for cat in ["Syntax", "Semantic", "Complexity", "Style", "Security"]
    )

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>CodeSentinel — {_html.escape(os.path.basename(filepath))}</title>
<style>
  :root{{--bg:#0f172a;--s:#1e293b;--b:#334155;--t:#e2e8f0;--m:#94a3b8;--a:#38bdf8}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--t);font-family:'Segoe UI',sans-serif;padding:2rem}}
  header{{display:flex;justify-content:space-between;align-items:center;
          border-bottom:1px solid var(--b);padding-bottom:1.5rem;margin-bottom:1.5rem}}
  h1{{font-size:1.5rem;color:var(--a)}}
  header p{{color:var(--m);font-size:.8rem;margin-top:.25rem}}
  .ring{{width:80px;height:80px;border-radius:50%;
         background:conic-gradient({sc} {score}%,var(--b) 0);
         display:flex;align-items:center;justify-content:center}}
  .inner{{width:62px;height:62px;border-radius:50%;background:var(--bg);
          display:flex;flex-direction:column;align-items:center;justify-content:center}}
  .snum{{font-size:1.1rem;font-weight:700;color:{sc}}}
  .sgrd{{font-size:.65rem;color:var(--m)}}
  .stats{{display:grid;grid-template-columns:repeat(5,1fr);gap:.75rem;margin-bottom:1.5rem}}
  .stat{{background:var(--s);border:1px solid var(--b);border-radius:8px;
         padding:.75rem;text-align:center}}
  .num{{font-size:1.6rem;font-weight:700;color:var(--a)}}
  .lbl{{font-size:.7rem;color:var(--m);margin-top:.2rem}}
  .card{{background:var(--s);border:1px solid var(--b);border-radius:8px;
         margin-bottom:1rem;overflow:hidden}}
  .card h2{{padding:.6rem 1rem;background:var(--b);font-size:.85rem;
            letter-spacing:.05em;color:var(--a)}}
  .row{{display:flex;align-items:center;gap:.6rem;padding:.5rem 1rem;
        border-bottom:1px solid var(--b);font-size:.82rem}}
  .row:last-child{{border-bottom:none}}
  .badge{{font-size:.65rem;font-weight:700;padding:2px 5px;border-radius:3px;
          color:#fff;white-space:nowrap}}
  .ln{{color:var(--m);font-size:.75rem;min-width:2.5rem}}
  .ok{{padding:.6rem 1rem;color:#22c55e;font-size:.82rem}}
  footer{{margin-top:1.5rem;text-align:center;color:var(--m);font-size:.72rem}}
</style></head><body>
<header>
  <div><h1>🛡 CodeSentinel</h1>
  <p>{_html.escape(filepath)} &nbsp;|&nbsp; {datetime.now().strftime("%Y-%m-%d %H:%M")}</p></div>
  <div class="ring"><div class="inner">
    <span class="snum">{score}</span><span class="sgrd">Grade {grade}</span>
  </div></div>
</header>
<div class="stats">{stats}</div>
{sections}
<footer>CodeSentinel — Python Static Analyzer &nbsp;|&nbsp; Compiler Design Project</footer>
</body></html>"""

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    return out
