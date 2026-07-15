# save_storage.py (project root)
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

START_URL = sys.argv[1] if len(sys.argv) > 1 else "https://<your-internal-start-page>"
OUT = Path("auth") / "storage_state.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

print(f"[INFO] Launching Edge to {START_URL}")
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(START_URL)

    print("\n[ACTION] Complete your normal SSO login in the Edge window.")
    print("         Once you reach your internal home page, return here and press ENTER.")
    input()

    context.storage_state(path=str(OUT))
    print(f"[OK] Saved storage state to {OUT.resolve()}")
    browser.close()
