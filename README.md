# UI Change Monitor & Evidence Reporter (CUA)

**Project Type:** Computer-Using Agent (CUA) — UI Automation & Visual Monitoring  
**Author:** Suman  
**Period:** GS Internship 2026 H1, Eli Lilly  
**Status:** Core implementation complete

---

## What This Is

A Computer-Using Agent that autonomously monitors web UIs for visual changes and generates audit-ready evidence reports. Instead of relying on DOM inspection or API checks, the agent *sees* the interface the same way a human would — through screenshots — and flags anything that changed.

**The pipeline:**

1. **Launch** → Opens Microsoft Edge via Playwright (uses enterprise-installed browser, no custom install needed)
2. **Navigate** → Goes to the target URL, waits for page readiness
3. **Capture** → Takes a full-page screenshot
4. **Compare** → Pixel-level diff against stored baseline with configurable threshold
5. **Report** → Generates a self-contained HTML report with baseline / current / diff views

---

## Quick Start

### Prerequisites

- Python 3.11+
- Microsoft Edge (installed)
- Playwright browser binaries

### Setup

```bash
pip install -r requirements.txt
playwright install msedge
```

### First Run (creates baseline)

```bash
python edge_screenshot_diff_report.py
```

This captures the first screenshot and saves it as the baseline. The report will say "Baseline created."

### Second Run (generates diff)

```bash
python edge_screenshot_diff_report.py
```

Now it compares against the baseline and produces:
- `demo_page_current.png` — current screenshot
- `demo_page_diff.png` — diff overlay (changes in red)
- `report.html` — full evidence report (open in any browser)

### For SSO-Protected Pages

```bash
python save_storage.py https://your-internal-page.lilly.com
# Complete SSO login in the Edge window, then press ENTER
# Auth state saved to auth/storage_state.json
```

---

## Folder Structure

```
CUA-Project/
├── Task_Summary.docx              # Filled-in task summary (accomplishments, learnings, next steps)
├── README.md                      # This file
├── ARCHITECTURE.md                # Technical architecture & design decisions
├── LEARNINGS.md                   # Personal reflections & what I learned
│
├── code/
│   ├── edge_screenshot_diff_report.py   # Main agent script
│   ├── save_storage.py                  # SSO auth state capture helper
│   ├── targets.yaml                     # Target URL configuration
│   ├── requirements.txt                 # Python dependencies
│   └── pyproject.toml                   # Project metadata
│
├── evidence/
│   ├── demo_page_current.png            # Captured screenshot (current run)
│   ├── demo_page_diff.png              # Diff overlay with red highlights
│   └── report.html                      # Auto-generated HTML evidence report
│
└── docs/
    └── REPORT_-_PROJECT1.pdf            # Written project report
```

---

## Configuration (targets.yaml)

The agent is driven by `targets.yaml`, which supports:

| Setting | What It Does |
|---------|-------------|
| `viewport` | Browser window size (width × height) |
| `user_agent` | Custom UA string for identification |
| `wait_until` | Page load event to wait for (`commit`, `domcontentloaded`, `load`) |
| `settle_ms` | Time to wait after load for dynamic content to stabilize |
| `retry_on_large_diff` | Auto-retry if diff exceeds threshold (catches incomplete loads) |
| `big_diff_threshold` | Max change % before triggering retry (0.65 = 65%) |
| `targets[].actions` | Per-target pre-capture actions (wait, scroll, click) |
| `targets[].ready.selector` | CSS selector that must exist before screenshot |
| `targets[].masking.selectors` | Elements to mask out (timestamps, user avatars) |

---

## How the Diff Engine Works

1. **Normalize** — Both images cropped to the minimum common dimensions
2. **Difference** — Pillow `ImageChops.difference()` computes per-pixel delta
3. **Threshold** — Pixels with delta > 10 (configurable) marked as changed
4. **Overlay** — Translucent red (RGBA 255,0,0,90) composited onto changed regions
5. **Quantify** — Changed pixels / total pixels = change percentage

This approach catches real visual changes while ignoring minor rendering noise (anti-aliasing, sub-pixel shifts).

---

## Key Design Decisions

| Decision | Why |
|----------|-----|
| Screenshot-based (not DOM) | Catches what users actually see — CSS regressions, font changes, layout shifts that DOM checks miss |
| Microsoft Edge | Enterprise-standard browser at Lilly — no custom browser install needed |
| Self-contained HTML report | Base64-embedded images, opens anywhere, no server needed, easy to attach to tickets/emails |
| YAML configuration | Non-developers can add/modify targets without touching Python code |
| Separate auth helper | SSO credentials never stored in code — only reusable browser state |

---

## Evidence Artifacts

The `evidence/` folder contains output from a demo run against `time.is`:

- **demo_page_current.png** — Screenshot showing the current state of time.is
- **demo_page_diff.png** — Same screenshot with red overlay highlighting the clock digits that changed between baseline and current capture
- **report.html** — Full HTML report with side-by-side baseline/current/diff views and change percentage

These demonstrate the agent successfully detecting real visual changes (clock digit updates) on a live website.

---

## Relevance to Eli Lilly

| Area | Value |
|------|-------|
| **Operational Efficiency** | Reduces manual UI validation during release cycles |
| **Risk Reduction** | Catches silent UI regressions before they impact users |
| **Compliance & Audit** | Generates timestamped visual evidence for regulated environments |
| **Scalability** | Configurable for any internal dashboard, portal, or regulated app |
| **CI/CD Integration** | Can be triggered as a pipeline step for pre-release visual checks |
