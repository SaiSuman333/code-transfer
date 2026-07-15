
# src/uimon/collector.py
from playwright.sync_api import sync_playwright
from pathlib import Path
from .utils import slugify, now_iso
from .masker import apply_masks
import json, time


def _visible_text(page):
    return page.evaluate("document.body.innerText || ''")


def _safe_path(p):
    """Return a string path if input is Path-like, else return as-is."""
    if p is None:
        return None
    try:
        return str(Path(p))
    except Exception:
        return p


def _apply_actions(page, actions, timeout_ms):
    """
    Supported action types:
      - wait: {type: "wait", ms: 4000}
      - scroll_bottom: {type: "scroll_bottom"}
      - scroll_top: {type: "scroll_top"}
      - click: {type: "click", selector: "..."}
      - fill: {type: "fill", selector: "...", value: "..."}
      - press: {type: "press", key: "Enter"}  (global keypress)
      - eval: {type: "eval", script: "..."}   (JS expression / statement)
      - wait_selector: {type: "wait_selector", selector: "..."}
    """
    if not actions:
        return

    for a in actions:
        a_type = (a.get("type") or "").strip().lower()

        try:
            if a_type == "wait":
                page.wait_for_timeout(int(a.get("ms", 1000)))

            elif a_type == "scroll_bottom":
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                # give layout a moment to reflow
                page.wait_for_timeout(750)

            elif a_type == "scroll_top":
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(300)

            elif a_type == "click":
                sel = a.get("selector")
                if sel:
                    page.click(sel, timeout=timeout_ms)

            elif a_type == "fill":
                sel = a.get("selector")
                val = a.get("value", "")
                if sel:
                    page.fill(sel, str(val), timeout=timeout_ms)

            elif a_type == "press":
                key = a.get("key")
                if key:
                    page.keyboard.press(key)

            elif a_type == "eval":
                script = a.get("script")
                if script:
                    page.evaluate(script)

            elif a_type == "wait_selector":
                sel = a.get("selector")
                if sel:
                    page.wait_for_selector(sel, timeout=timeout_ms)

            else:
                # Unknown action type — ignore (keeps it multi-site friendly)
                continue

        except Exception:
            # Do not crash entire run for one action; continue to next action/target
            continue


def _wait_ready(page, ready, timeout_ms):
    """
    ready supports:
      - selector: CSS/text selector
      - text: substring required in visible text
    """
    if not ready:
        return

    try:
        sel = ready.get("selector")
        if sel:
            page.wait_for_selector(sel, timeout=timeout_ms)
            return
    except Exception:
        pass

    try:
        required_text = ready.get("text")
        if required_text:
            # simple polling
            deadline = time.time() + (timeout_ms / 1000.0)
            while time.time() < deadline:
                body_text = _visible_text(page)
                if required_text in body_text:
                    return
                time.sleep(0.25)
    except Exception:
        pass


def capture_targets(cfg, baseline=False, run_dir=None):
    artifacts = []

    # default directories
    base_dir = Path("baselines")
    base_dir.mkdir(exist_ok=True)

    run_dir = Path(run_dir or "runs/_tmp")  # caller should pass actual run folder
    run_dir.mkdir(parents=True, exist_ok=True)

    # runtime config
    run_cfg = cfg.get("run", {})
    timeout_ms = int(run_cfg.get("timeout_ms", 60000))
    settle_ms_default = int(run_cfg.get("settle_ms", 8000))
    wait_until = run_cfg.get("wait_until", "commit")
    viewport = run_cfg.get("viewport", {"width": 1366, "height": 768})
    user_agent = run_cfg.get("user_agent", "UI-EvidenceBot/1.0 (read-only)")
    rate_limit_ms = int(run_cfg.get("rate_limit_ms", 0))
    headless = bool(run_cfg.get("headless", True))  # add run.headless in YAML if you want

    storage_state = cfg.get("auth", {}).get("storage_state")
    storage_state = _safe_path(storage_state)

    with sync_playwright() as p:
        # Edge chromium
        browser = p.chromium.launch(channel="msedge", headless=headless)

        context = browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            storage_state=storage_state if storage_state else None
        )

        page = context.new_page()
        page.set_default_timeout(timeout_ms)

        for t in cfg.get("targets", []):
            name = t.get("name", "unnamed")
            slug = t.get("slug") or slugify(name)
            url = t.get("url")

            if not url:
                # skip invalid target
                continue

            # Navigate
            page.goto(url, wait_until=wait_until)

            # Global/per-target settle wait (helps SPAs)
            settle_ms = int(t.get("settle_ms", settle_ms_default))
            if settle_ms > 0:
                page.wait_for_timeout(settle_ms)

            # Optional per-target actions (scroll, search, click etc.)
            _apply_actions(page, t.get("actions", []), timeout_ms)

            # Optional readiness gate (selector/text)
            _wait_ready(page, t.get("ready", {}), timeout_ms)

            # Capture HTML after readiness/actions
            latest_html = page.content()

            # Mask volatile UI regions before screenshot/text
            apply_masks(page, t.get("masking", {}).get("selectors"))

            # Capture options
            cap = t.get("capture", {})
            full_page = bool(cap.get("full_page", False))
            clip_selector = cap.get("clip_selector")
            clip = None
            if clip_selector:
                try:
                    box = page.locator(clip_selector).bounding_box()
                    if box:
                        clip = {k: float(v) for k, v in box.items()}
                except Exception:
                    clip = None

            # Screenshot + visible text
            png_bytes = page.screenshot(full_page=full_page, clip=clip, type="png")
            text = _visible_text(page)

            meta = {
                "name": name,
                "slug": slug,
                "url": url,
                "final_url": page.url,
                "title": page.title(),
                "timestamp": now_iso(),
                "headless": headless,
                "wait_until": wait_until,
                "settle_ms": settle_ms
            }

            # Write baseline or run artifacts
            out_root = base_dir if baseline else run_dir / "artifacts"
            out = out_root / slug
            out.mkdir(parents=True, exist_ok=True)

            (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
            (out / "text.txt").write_text(text, encoding="utf-8")
            (out / "screenshot.png").write_bytes(png_bytes)

            artifacts.append({
                "name": name,
                "url": url,
                "slug": slug,
                "rules": t.get("rules", {}),
                "paths": {
                    "meta": str(out / "meta.json"),
                    "text": str(out / "text.txt"),
                    "screenshot": str(out / "screenshot.png"),
                    "diff": str(out / "diff.png")
                },
                "meta": meta,
                "latest_html": latest_html
            })

            # courteous pacing between targets
            if rate_limit_ms > 0:
                time.sleep(rate_limit_ms / 1000.0)

        context.close()
        browser.close()

    return artifacts
