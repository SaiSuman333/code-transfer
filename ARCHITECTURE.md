# Architecture — UI Change Monitor & Evidence Reporter

## System Overview

The agent follows a linear pipeline architecture: **Configure → Launch → Capture → Compare → Report**.

There is no persistent server or daemon. Each execution is a standalone run that produces a snapshot of the current UI state and compares it against the last known baseline.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXECUTION PIPELINE                          │
│                                                                     │
│  targets.yaml ──► Playwright (Edge) ──► Screenshot ──► Pillow Diff │
│                         │                                   │       │
│                    save_storage.py                     report.html   │
│                   (SSO auth state)                  (evidence output)│
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Configuration Layer (`targets.yaml`)

Declarative YAML file that defines *what* to monitor and *how* to capture it.

**Design rationale:** Separating config from code means QA or ops teams can add new targets without modifying Python. The YAML structure supports per-target overrides (viewport, wait times, masking) while inheriting global defaults.

**Key structures:**
- `run` — Global defaults (viewport, user agent, timeouts)
- `auth` — Path to stored browser state for SSO
- `targets[]` — List of URLs with per-target actions, readiness gates, and masking rules

### 2. Browser Automation (`Playwright + Edge`)

Playwright controls a real Microsoft Edge instance (via the `channel="msedge"` parameter).

**Why Edge, not Chromium?** In enterprise environments like Lilly, Edge is the standard browser with SSO integration, certificate stores, and proxy configs already set up. Using the installed Edge avoids:
- Downloading a separate Chromium binary
- Reconfiguring auth/proxy/certs
- IT policy conflicts

**Why not headless?** The current implementation runs headed (`headless=False`) for development/demo visibility. Production runs can switch to `headless=True` in targets.yaml.

### 3. Screenshot Capture

```python
page.screenshot(path=str(current_path), full_page=True)
```

Playwright captures the full scrollable page, not just the viewport. This ensures the agent sees everything a user would see by scrolling — important for dashboards and long pages.

**Readiness strategy:**
1. `wait_until="domcontentloaded"` — Wait for initial HTML parse
2. `settle_ms` — Additional wait for JS-rendered content to stabilize
3. `ready.selector` — Optional CSS selector gate (page not captured until element exists)
4. `actions` — Optional pre-capture actions (scroll, wait, click)

### 4. Diff Engine (`Pillow`)

The comparison pipeline:

```
Baseline Image ─┐
                 ├──► Normalize (crop to common size)
Current Image ──┘         │
                          ▼
                   ImageChops.difference()
                          │
                          ▼
                   Grayscale conversion
                          │
                          ▼
                   Threshold mask (pixel > 10 → changed)
                          │
                    ┌─────┴─────┐
                    ▼           ▼
             Changed pixel   Red overlay
              count / %      composite
                    │           │
                    ▼           ▼
               Quantified   diff image
                change       (visual)
```

**Threshold = 10:** This value was tuned empirically. Below 10, anti-aliasing and sub-pixel rendering differences create noise. Above 15, subtle but real changes (color shifts, font weight changes) get missed.

**Red overlay (RGBA 255,0,0,90):** The 90/255 alpha means the original content is still visible beneath the highlight, making it easy to see both *what changed* and *what it changed to*.

### 5. Evidence Report (`HTML`)

The report is a single self-contained HTML file with:
- Run metadata (timestamp, URL)
- Change percentage
- Three-panel grid: Baseline | Current | Diff
- All images embedded as base64 data URIs

**Why base64 embedding?** The report has zero external dependencies. It can be:
- Emailed as an attachment
- Stored in SharePoint or Teams
- Opened offline in any browser
- Attached to a Jira/ServiceNow ticket

### 6. Auth Helper (`save_storage.py`)

For SSO-protected internal pages:
1. Opens Edge to the target login page
2. User completes SSO login manually (one time)
3. Browser storage state (cookies, localStorage) saved to `auth/storage_state.json`
4. Subsequent agent runs load this state to bypass login

**Security:** No passwords are stored. Only the session state is captured, and it expires naturally based on the IdP's session policy.

---

## Data Flow

```
Run N (first time):
  targets.yaml → launch Edge → navigate URL → capture screenshot
                                                      │
                                              save as baseline
                                                      │
                                              generate "baseline created" report

Run N+1 (subsequent):
  targets.yaml → launch Edge → navigate URL → capture screenshot
                                                      │
                                              load baseline from disk
                                                      │
                                              pixel diff (Pillow)
                                                      │
                                              generate diff report
                                              with change % + overlay
```

---

## Directory Layout (Runtime)

```
project-root/
├── baselines/
│   └── demo_page_baseline.png        # Stored baseline (persists across runs)
├── runs/
│   └── edge_run_20260215_103045/     # One folder per execution
│       ├── demo_page_current.png
│       ├── demo_page_diff.png
│       └── report.html
├── auth/
│   └── storage_state.json            # SSO session state (gitignored)
├── edge_screenshot_diff_report.py
├── save_storage.py
├── targets.yaml
├── requirements.txt
└── pyproject.toml
```

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.11+ | Orchestration, diff logic, reporting |
| Browser automation | Playwright | 1.45+ | Edge control, screenshot capture |
| Image processing | Pillow (PIL) | 10.0+ | Pixel diff, overlay composite |
| Configuration | PyYAML | 6.0+ | Target definitions, settings |
| HTML parsing | BeautifulSoup4 | 4.12+ | DOM analysis (future extension) |
| Browser | Microsoft Edge | Enterprise | Real browser with SSO/proxy support |

---

## Extension Points

1. **Multi-target runs** — Loop through `targets[]` in YAML, generate per-target reports
2. **DOM capture** — BeautifulSoup already in requirements; add structural diff alongside visual
3. **Scheduled execution** — Wrap in cron/Task Scheduler/CI trigger
4. **Alerting** — POST to Teams webhook or send email when change % exceeds threshold
5. **Bounding-box targeting** — Crop specific page regions (charts, headers) for focused comparison
6. **History/trending** — Store change % over time, chart regression trends
