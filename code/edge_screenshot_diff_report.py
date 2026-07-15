from __future__ import annotations
from datetime import datetime
from pathlib import Path
import base64
from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import sync_playwright

# Demo URL (change if needed)
URL = " https://time.is/"

BASELINES_DIR = Path("baselines")
RUNS_DIR = Path("runs")
BASELINES_DIR.mkdir(exist_ok=True)
RUNS_DIR.mkdir(exist_ok=True)

SAFE_NAME = "demo_page"
baseline_path = BASELINES_DIR / f"{SAFE_NAME}_baseline.png"

run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
run_dir = RUNS_DIR / f"edge_run_{run_stamp}"
run_dir.mkdir(parents=True, exist_ok=True)

current_path = run_dir / f"{SAFE_NAME}_current.png"
diff_path = run_dir / f"{SAFE_NAME}_diff.png"
report_path = run_dir / "report.html"


def to_data_uri(img_path: Path) -> str:
    b = img_path.read_bytes()
    return "data:image/png;base64," + base64.b64encode(b).decode("utf-8")


def make_diff(baseline_img: Image.Image, current_img: Image.Image):
    # normalize sizes
    w = min(baseline_img.width, current_img.width)
    h = min(baseline_img.height, current_img.height)
    baseline = baseline_img.crop((0, 0, w, h)).convert("RGBA")
    current = current_img.crop((0, 0, w, h)).convert("RGBA")

    diff = ImageChops.difference(baseline, current)
    gray = diff.convert("L")

    # threshold mask (adjust 10->20 if too sensitive)
    threshold = 10
    mask = gray.point(lambda p: 255 if p > threshold else 0)

    changed_pixels = sum(1 for v in mask.getdata() if v != 0)
    total_pixels = w * h
    pct = (changed_pixels / total_pixels) * 100 if total_pixels else 0.0

    # overlay red where changed
    red = Image.new("RGBA", (w, h), (255, 0, 0, 90))
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    overlay = Image.composite(red, overlay, mask)

    highlighted = Image.alpha_composite(current, overlay)
    return highlighted, changed_pixels, total_pixels, pct


def write_html(title: str, url: str, started: str, body_html: str):
    html = """<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    .meta {{ background: #f5f5f5; padding: 12px; border-radius: 8px; margin-bottom: 16px; }}
    .grid {{ display: grid; grid-template-columns: 1fr; gap: 16px; }}
    @media (min-width: 1100px) {{ .grid {{ grid-template-columns: 1fr 1fr 1fr; }} }}
    .card {{ border: 1px solid #ddd; border-radius: 10px; padding: 10px; }}
    img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 8px; }}
    code {{ background:#eee; padding:2px 6px; border-radius:4px; }}
    small {{ color:#666; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="meta">
    <p><b>Run time:</b> {started}</p>
    <p><b>URL:</b> <a href="{url}">{url}</a></p>
  </div>
  {body}
</body>
</html>
""".format(title=title, url=url, started=started, body=body_html)

    report_path.write_text(html, encoding="utf-8")


def main():
    started = datetime.now().isoformat(timespec="seconds")

    with sync_playwright() as p:
        # Launch installed Microsoft Edge via branded channel (no Playwright Chromium download) [1](https://teams.microsoft.com/l/message/19:576a877a403942f5944557f6fd7592f8@thread.v2/1769141111395?context=%7B%22contextType%22:%22chat%22%7D)[2](https://teams.microsoft.com/l/message/19:576a877a403942f5944557f6fd7592f8@thread.v2/1769089235529?context=%7B%22contextType%22:%22chat%22%7D)
        browser = p.chromium.launch(channel="msedge", headless=False)
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1500)

        page_title = page.title()
        page.screenshot(path=str(current_path), full_page=True)

        browser.close()

    # If baseline missing -> create baseline and report
    if not baseline_path.exists():
        baseline_path.write_bytes(current_path.read_bytes())

        body = """
        <p><b>Page title:</b> {}</p>
        <p><b>Status:</b> Baseline did not exist — created baseline from this run.</p>
        <p><b>Next:</b> Run the script again to generate a diff report.</p>
        <div class="card">
          <h2>Baseline (created)</h2>
          <img src="{}" />
        </div>
        """.format(page_title, to_data_uri(baseline_path))

        write_html("UI Evidence Report (Baseline Created)", URL, started, body)
        print(f"✅ Baseline created: {baseline_path}")
        print(f"✅ Report generated: {report_path}")
        return

    # Otherwise compute diff and report
    baseline_img = Image.open(baseline_path)
    current_img = Image.open(current_path)

    diff_img, changed_pixels, total_pixels, pct = make_diff(baseline_img, current_img)
    diff_img.save(diff_path)

    body = """
    <p><b>Page title:</b> {title}</p>
    <p><b>Diff:</b> Changed pixels: <code>{cp}</code> / <code>{tp}</code> → <code>{pct:.2f}%</code></p>
    <p><small>Diff image highlights changes in translucent red on top of CURRENT screenshot.</small></p>

    <div class="grid">
      <div class="card">
        <h2>Baseline</h2>
        <img src="{b64_base}" />
      </div>
      <div class="card">
        <h2>Current</h2>
        <img src="{b64_curr}" />
      </div>
      <div class="card">
        <h2>Diff (Red highlights)</h2>
        <img src="{b64_diff}" />
      </div>
    </div>
    """.format(
        title=page_title,
        cp=changed_pixels,
        tp=total_pixels,
        pct=pct,
        b64_base=to_data_uri(baseline_path),
        b64_curr=to_data_uri(current_path),
        b64_diff=to_data_uri(diff_path),
    )

    write_html("UI Evidence Report (Diff)", URL, started, body)
    print(f"✅ Current screenshot: {current_path}")
    print(f"✅ Diff screenshot: {diff_path}")
    print(f"✅ Report generated: {report_path}")


if __name__ == "__main__":
    main()