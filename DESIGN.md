# DESIGN.md — Modern Dark Developer UI Design System
### Design Guidelines for Sub-Second Voice Concierge & Atelier Ops

> **Aesthetic Profile:** Ultra-modern Developer-Centric Dark Mode, Hairline Precision Grid, Flame/Heat Accents (`#fa5d19`), Monospace Status Headers, and Interactive Terminal Playgrounds.

---

## 1. Color Palette Tokens

```css
:root {
  /* Firecrawl Signature Accent: Flame / Heat */
  --heat-100: #fa5d19;          /* Primary CTA, flame orange */
  --heat-90:  #fa5d19e6;        /* High-emphasis hover */
  --heat-48:  #fa5d197a;        /* Active border glow */
  --heat-20:  #fa5d1933;        /* Subtle badge background */
  --heat-8:   #fa5d1914;        /* Card tint / hover wash */

  /* Dark Canvas Surfaces */
  --bg-base:        #0a0a0a;    /* Primary background */
  --bg-lighter:     #121212;    /* Secondary section background */
  --surface:        #171717;    /* Primary card & console background */
  --surface-raised: #1e1e1e;    /* Hover card & elevated elements */
  --surface-active: #242424;    /* Active tab / input field */

  /* Precision Hairline Borders */
  --border-faint:   #222222;    /* Subtle dividers & outer grid */
  --border-muted:   #2e2e2e;    /* Card borders */
  --border-loud:    #3e3e3e;    /* Focused inputs, active borders */

  /* Status Colors */
  --status-emerald: #10b981;    /* Online, completed, 200 OK */
  --status-sky:     #38bdf8;    /* Shipped, active streams */
  --status-purple:  #a855f7;    /* Measurements, bespoke configs */
  --status-amber:   #f59e0b;    /* In production, processing */
  --status-rose:    #f43f5e;    /* Alteration, cancelled, barge-in */

  /* Typography Colors */
  --text-primary:   #ededed;    /* High contrast text */
  --text-secondary: #a1a1aa;    /* Labels, descriptions */
  --text-tertiary:  #71717a;    /* Dim metadata, icons */
  --text-mono:      #d4d4d8;    /* Code, JSON, millisecond counters */
}
```

---

## 2. Typography & Fonts

* **Primary Sans:** `Geist Sans` / `Inter` (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`)
  * Used for: Titles, body copy, marketing copy, buttons.
  * Weights: `400` (Regular), `500` (Medium), `600` (Semi-bold), `700` (Bold).
* **Technical Monospace:** `Geist Mono` / `JetBrains Mono` (`ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`)
  * Used for:
    * Frame labels (e.g., `[ 200 OK ]`, `[ LIVEKIT ]`, `[ 467ms ]`).
    * Order IDs (`ORD-101`), latency waterfall meters, JSON payload viewer.
    * Terminal logs & tool execution traces.

---

## 3. Structural & Architectural Motifs (Precision Developer UI)

### A. The Hairline Grid & Corner Connectors
* Containers feature subtle **1px borders** (`border border-[#262626]`).
* Background has a subtle grid pattern:
  ```css
  background-image: linear-gradient(to right, #1f1f1f 1px, transparent 1px),
                    linear-gradient(to bottom, #1f1f1f 1px, transparent 1px);
  background-size: 32px 32px;
  ```
* Corner crosses (`+` or four-point star icons) mark grid intersections, giving it a blueprint / precision-engineered aesthetic.

### B. Header & Announcement Banner
* Sticky top bar with a 1px bottom border (`border-b border-[#222222]`) and backdrop blur (`backdrop-blur-md bg-[#0a0a0a]/80`).
* Flame orange announcement pill at the top:
  `[ NEW ] Sub-Second Full-Duplex Voice Engine Released →`

### C. The Interactive Console / Terminal Playground
* Replaces standard web forms with a **developer console layout**:
  * Top bar with terminal tabs: `[ Live Voice ]`, `[ Tool Trace ]`, `[ API Docs ]`, `[ ERP DB ]`.
  * Right side shows live millisecond waterfall cards with color-coded tokens:
    * 🟢 `Deepgram STT`: 120ms
    * 🔥 `Groq LPU (GPT-OSS)`: 467ms
    * ⚡ `Edge-TTS`: 290ms
    * 🏆 `Total TTFA`: 877ms

### D. The Flame Orange CTA Button
* Primary interactive trigger has a distinctive warm glow:
  ```css
  background: #fa5d19;
  color: #ffffff;
  font-weight: 500;
  box-shadow: 0 0 28px -4px rgba(250, 93, 25, 0.45), 0 0 0 1px rgba(250, 93, 25, 0.8);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  ```
  On hover: expands shadow, scales `1.02`.
  On active: scales `0.98`.

### E. Live Atelier ERP Cards
* Styled like code inspection panels:
  * Top bar shows `ORDER_ID` in monospace.
  * Status tag has a hairline border with matching semi-transparent background.
  * Subtle hover state: border brightens to `--border-loud` and card lifts slightly.

---

## 4. UI Components Specification

| Component | Inactive State | Active / Hover State |
| :--- | :--- | :--- |
| **Voice Microphone Orb** | `#171717` card, border `#2a2a2a`, orange icon | Glowing `#fa5d19` ring pulse, soundwave audio bars |
| **Barge-in Indicator** | Hidden | `#fa5d1920` pill with flashing flame dot: `⚡ Barge-in Triggered` |
| **Prompt Pill Chips** | `#171717` bg, `#2a2a2a` border, `#a1a1aa` text | `#222222` bg, `#fa5d19` border glow, `#ededed` text |
| **Live Tool Traces** | Collapsible JSON drawer in dark console | Monospace syntax-highlighted tool arguments & results |
