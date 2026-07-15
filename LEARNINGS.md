# Learnings — UI Change Monitor & Evidence Reporter (CUA)

## What Is a Computer-Using Agent?

A CUA is an agent that interacts with software through its graphical interface — the same way a human user would. Instead of calling APIs or reading databases, it *sees* the screen, *clicks* buttons, and *reads* text from rendered pages.

This is fundamentally different from traditional test automation:

| Traditional Automation | CUA Approach |
|----------------------|-------------|
| Checks DOM elements by selector | Sees the rendered visual output |
| Validates API responses | Validates what the user actually sees |
| Misses CSS/layout regressions | Catches anything visible on screen |
| Tightly coupled to page structure | Works even if DOM changes but UI looks the same |

**My takeaway:** CUAs are especially powerful for catching the class of bugs that "pass all tests but look wrong." A button that shifted 50px left, a font that changed, a chart that renders blank — these are invisible to API tests but obvious to a CUA.

---

## Technical Learnings

### Playwright

- `channel="msedge"` lets you control the enterprise-installed Edge — no need to download a separate browser binary. This is a big deal in corporate environments where IT controls what's installed.
- `full_page=True` on screenshots captures the entire scrollable page, not just the viewport. Essential for dashboards.
- `storage_state` is the cleanest way to handle SSO — capture once, reuse until session expires. No credential storage.
- `wait_until` options matter: `commit` is fastest (first response bytes), `domcontentloaded` waits for HTML parse, `load` waits for everything including images. For screenshots, you usually want `domcontentloaded` plus a settle delay.

### Image Processing (Pillow)

- `ImageChops.difference()` gives you a per-pixel delta between two images. Converting to grayscale then thresholding creates a clean binary mask of "changed" vs "unchanged."
- **Threshold tuning is the hardest part.** Too low (< 5) and you get noise from anti-aliasing, font hinting, and sub-pixel rendering. Too high (> 20) and you miss real but subtle changes. I settled on 10 as a good default.
- `Image.alpha_composite()` lets you overlay a translucent color on the changed regions while keeping the original content visible underneath. The alpha value (90/255 ≈ 35%) was chosen so changes are obvious but the underlying content is still readable.

### Configuration Design

- YAML is a good middle ground between JSON (no comments, strict syntax) and INI (no nesting). QA or ops people can edit targets.yaml without Python knowledge.
- Per-target overrides with global fallbacks keeps the config DRY while allowing flexibility.
- The `actions` list (wait, scroll, click) makes the agent's pre-capture behavior declarative rather than hardcoded.

---

## Enterprise / Lilly Context Learnings

### Evidence-First Design

In regulated environments, the *output format* matters as much as the *detection accuracy*. A log file that says "5.2% change detected" is useful for developers but useless for compliance. A visual HTML report with baseline/current/diff panels that anyone can open in a browser — that's evidence.

**My takeaway:** When building tools for enterprise, always ask "who else needs to understand this output?" The answer is usually wider than just the dev team.

### SSO and Authentication

Enterprise apps are protected by SSO (Single Sign-On). You can't just `requests.get()` an internal page. Playwright's `storage_state` approach captures the browser's session cookies and localStorage after a manual SSO login, then reuses them in subsequent automated runs.

**Important:** This doesn't store passwords. It stores session tokens that expire naturally. This is a cleaner pattern than trying to automate the SSO flow itself (which is fragile and may violate security policies).

### Why Edge Matters

At Lilly, Edge is the standard browser. It has pre-configured proxy settings, certificate stores, and SSO integrations. Using Playwright with `channel="msedge"` means the agent inherits all of this automatically. If I'd used a downloaded Chromium binary, I'd need to reconfigure all of that — or it simply wouldn't work behind the corporate proxy.

---

## What Went Well

1. **The pipeline is clean.** Capture → Diff → Report is simple to understand and debug.
2. **Self-contained HTML reports** turned out to be the most impactful design choice. Everyone can open and understand the output.
3. **YAML configuration** makes it easy to add new targets without changing code.
4. **The demo on time.is** provided a clear, visual proof that the system works — the clock digits change between runs, and the red overlay highlights exactly where.

## What I'd Do Differently

1. **Start with bounding-box targeting earlier.** Siva's question about graphs highlighted that full-page diff is noisy for pages with lots of dynamic content. Isolating specific regions would give cleaner results.
2. **Add structured logging from day one.** Currently the agent just prints to stdout. A proper logging setup with timestamps and run IDs would make debugging easier.
3. **Build the multi-target loop sooner.** The current script handles one URL. The targets.yaml already supports a list, but the main script doesn't iterate yet.

---

## Skills Developed

- **Browser automation** — Playwright, Edge integration, storage state management
- **Image processing** — Pixel-level comparison, thresholding, overlay composition
- **Configuration design** — YAML-based declarative config with inheritance
- **Evidence engineering** — Building outputs for non-technical stakeholders
- **Enterprise thinking** — Designing for SSO, corporate browsers, compliance requirements
- **CUA paradigm** — Understanding how agents can interact through GUIs rather than APIs
