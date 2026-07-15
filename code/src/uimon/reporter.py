# src/uimon/reporter.py
from pathlib import Path
from html import escape

def build_report(run_dir: Path, rows):
    # report lives at runs/<run_id>/report.html
    # baseline screenshots live at ../../baselines/<slug>/screenshot.png
    def row_html(i, r):
        slug = r["slug"]
        base_rel = f"../../baselines/{slug}/screenshot.png"
        curr_rel = f"artifacts/{slug}/screenshot.png"
        diff_rel = r["diff_preview"]["image_diff_path"].replace(str(run_dir) + "\\", "").replace(str(run_dir) + "/", "")
        return f"""
<tr>
  <td><strong>{escape(r['name'])}</strong><br><small>{escape(r['url'])}</small></td>
  <td><span class="badge {r['scores']['severity']}">{r['scores']['severity']}</span> {r['scores']['combined']:.2f}</td>
  <td>{r['scores']['text_similarity']:.2f}</td>
  <td>{r['scores']['image_distance']:.2f}</td>
  <td>{'✅' if r['rules']['passed'] else '⚠️'}</td>
  <td><button onclick="toggle('d{i}')">Open</button></td>
</tr>
<tr><td colspan="6">
  <div id="d{i}" class="details" style="display:none">
    <div class="card"><strong>Meta:</strong> {escape(str(r['meta']))}</div>
    <div class="diff">
      <div><div><small>Baseline</small></div><img src="{escape(base_rel)}"/></div>
      <div><div><small>Current</small></div><img src="{escape(curr_rel)}"/></div>
      <div><div><small>Diff</small></div><img src="{escape(diff_rel)}"/></div>
    </div>
    <div class="card">
      <strong>Unified text diff</strong>
      <pre>{escape(r['diff_preview']['text_unified'])}</pre>
    </div>
  </div>
</td></tr>
"""

    html = ["""
<!doctype html><html><head><meta charset="utf-8">
<title>UI Change Evidence Report</title>
<style>
body{font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;margin:24px}
table{border-collapse:collapse;width:100%}
th,td{padding:8px;border-bottom:1px solid #eee;vertical-align:top}
.badge{border-radius:6px;padding:2px 8px}
.LOW{background:#e8f5e9;color:#256029}.MEDIUM{background:#fff8e1;color:#7f6000}.HIGH{background:#fdecea;color:#8a0c0c}
.details{margin-top:12px}
.card{border:1px solid #e5e5e5;border-radius:8px;padding:12px;margin:12px 0}
.diff{display:flex;gap:12px;flex-wrap:wrap}
.diff img{max-width:32%;border:1px solid #ddd}
pre{white-space:pre-wrap;background:#fafafa;border:1px solid #eee;padding:8px;border-radius:6px;max-height:360px;overflow:auto}
</style>
<script>function toggle(id){const el=document.getElementById(id); el.style.display=(el.style.display==='none'?'block':'block'===el.style.display?'none':'block');}</script>
</head><body>
<h1>UI Change Evidence Report</h1>
<table>
<thead><tr><th>Page</th><th>Combined</th><th>Text sim</th><th>Img dist</th><th>Rules</th><th>Open</th></tr></thead>
<tbody>
"""]
    for i, r in enumerate(rows):
        html.append(row_html(i, r))
    html.append("</tbody></table></body></html>")
    out = run_dir / "report.html"
    out.write_text("".join(html), encoding="utf-8")
    return out
