# src/uimon/rules.py
from bs4 import BeautifulSoup

def run_rules(rules, html):
    out = {"must_exist": [], "must_contain": [], "passed": True}
    if not rules: return out
    soup = BeautifulSoup(html, "html.parser")

    for sel in rules.get("must_exist", []):
        ok = bool(soup.select_one(sel))
        out["must_exist"].append({"selector": sel, "ok": ok})

    for item in rules.get("must_contain", []):
        el = soup.select_one(item["selector"])
        ok = bool(el and item["text"] in (el.get_text() or ""))
        out["must_contain"].append({"selector": item["selector"], "text": item["text"], "ok": ok})

    out["passed"] = all(x["ok"] for x in out["must_exist"] + out["must_contain"])
    return out
