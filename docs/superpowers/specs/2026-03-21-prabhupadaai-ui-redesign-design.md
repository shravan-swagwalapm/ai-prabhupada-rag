# PrabhupadaAI — UI Redesign + Railway Deployment

**Date:** 2026-03-21
**Status:** Design approved, pending implementation
**Scope:** Visual refinement, anonymous trial, share feature, static export, Railway deploy

---

## 1. Decisions Made (Brainstorming Summary)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Audience | Both devotees and seekers | Maximize reach without alienating either |
| Deployment model | Static export + Railway single service | Zero Node.js overhead, one service, cheapest |
| Visual direction | Traditional Temple ("Temple at Dusk") | Aligns with existing codebase palette, ISKCON devotees feel at home |
| FAISS index shipping | Baked into Docker image | Instant cold start, no volume config |
| Auth flow | 2 free questions without login | Let users experience the magic before sign-in friction |
| Scope | Core polish + sharing + deploy | Ship today, landing page is a future session |
| Architecture approach | Refine in-place | Preserve working SSE/RichAnswer/AudioPlayer, only change visual layer |
| Title font | Cormorant Garamond 600 | Full Unicode for Sanskrit diacriticals (ṛ ṣ ṇ ā ī ū) |
| Code review | Superpowers code-reviewer agent post-implementation | Catches auth bypass, XSS, data loss, dead code |

---

## 2. Visual Identity — "Temple at Dusk"

### 2.1 Color System

```css
:root {
  /* Backgrounds — The Sanctum */
  --sanctum: #060403;        /* deepest background */
  --temple-dark: #0c0908;    /* page sections */
  --altar: #161009;          /* elevated surfaces */
  --card: #1c150e;           /* card backgrounds */
  --card-hover: #231a12;     /* interactive hover */

  /* Sacred Accents — Arati Flame */
  --gold: #c9a84c;           /* primary accent */
  --gold-bright: #dbb85a;    /* buttons, active states */
  --gold-dim: #a08940;       /* labels, metadata */
  --vermillion: #c24d2c;     /* Sanskrit, voice, sacred */
  --vermillion-bright: #e07050; /* verse text (WCAG AA on dark) */
  --tulsi: #4a8c3f;          /* success, ready states */

  /* Text — Deity Darshan Glow */
  --text-primary: #f7f0e3;          /* headings, titles (near-white warm) */
  --text-body: rgba(247,240,227,0.88); /* body paragraphs */
  --text-secondary: rgba(247,240,227,0.6); /* subtitles, labels */
  --text-muted: rgba(247,240,227,0.4);    /* metadata, hints */
  --text-ghost: rgba(247,240,227,0.25);   /* footers only */

  /* Glass & Borders */
  --glass: rgba(22,16,9,0.6);
  --glass-border: rgba(201,168,76,0.08);
  --glass-border-hover: rgba(201,168,76,0.15);
}
```

### 2.2 Typography

| Role | Font | Weight | Size | Usage |
|------|------|--------|------|-------|
| App title, greetings | Cormorant Garamond | 600 | 26-34px | "Hare Kṛṣṇa", screen titles — full diacritical support |
| Buttons, nav labels | Cinzel | 400 | 12-15px | "Ask Prabhupada ✦", tab labels — ASCII only, stone-carved authority |
| Body, scripture | Cormorant Garamond | 300-400 | 16-17px | Answer text, descriptions — liturgical warmth |
| Verse (Sanskrit) | Cormorant Garamond | 400 italic | 15-16px | Transliterated Sanskrit — #e07050 vermillion |
| Translation | Cormorant Garamond | 600 | 15-16px | English verse translations — #f7f0e3 |

**Google Fonts loading:** Use `<link rel="preconnect">` + `<link rel="stylesheet">` tags in `layout.tsx` `<head>` (NOT CSS `@import`, which blocks rendering):
```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,500&display=swap" rel="stylesheet" />
```
(~30KB total, `display=swap` prevents FOIT)

### 2.3 Ornamental Elements (CSS-only, zero image assets)

1. **Arati Flame Dividers** — 5 CSS divs with `border-radius` pill shapes, `linear-gradient` fills (vermillion→gold→cream), `scaleY/scaleX` keyframe animation for flickering effect
2. **Pulsing Avatar Rings** — Concentric `border-radius: 50%` elements with `scale` + `opacity` animation at 4s interval
3. **Temple Arch Card Frames** — Corner ornaments (border-top + border-left on absolute-positioned pseudo-elements), top-edge gold glow via `linear-gradient`
4. **Noise Texture Overlay** — Inline SVG `feTurbulence` at 3% opacity, `position: fixed` over entire viewport. Adds analog warmth.
5. **Sanctum Aura** — `radial-gradient` from gold→vermillion→transparent, positioned at top of each screen
6. **Backdrop-blur Glass** — `backdrop-filter: blur(12px)` on header and share bar

### 2.4 Micro-interactions & Animation

| Element | Animation | Duration | Purpose |
|---------|-----------|----------|---------|
| Arati flames | `scaleY` flicker | 2s alternate | Living dividers |
| Avatar rings | `scale` + `opacity` pulse | 4s ease-in-out | Breathing sanctum |
| Streaming cursor | `opacity` blink | 1.2s step-end | "Still receiving" signal |
| Input focus | `box-shadow` glow expand | 0.3s ease | Gold focus ring |
| Share buttons | `background` + `border-color` | 0.3s ease | Hover feedback |
| Tab indicator | `linear-gradient` underline | instant | Active state |
| Audio progress | `width` transition | 0.3s linear | Smooth playback bar |

All animations use CSS only — no JS animation libraries needed.

---

## 3. Component Changes

### 3.1 Auth Screen (`app/auth/page.tsx`)

**Current:** Google Sign-In gate, redirects to `/` if logged in.

**Changes:**
- Add "Ask 2 Free Questions ✦" as primary CTA (gold, prominent) above Google Sign-In
- Clicking it sets `localStorage.setItem('prabhupada_anon_mode', 'true')` and navigates to `/`
- Update avatar container with pulsing ring animations
- Replace static divider with arati flame component
- Title font → Cormorant Garamond 600 for "Hare Kṛṣṇa"
- Add scripture count badge: "161,724 sacred passages indexed"
- Update all colors to Temple at Dusk palette

### 3.2 Main Page (`app/page.tsx`)

**Current:** Auth-gated, redirects to `/auth` if not logged in.

**Changes:**
- Allow access when `prabhupada_anon_mode` is set in localStorage
- Track anonymous query count: `prabhupada_anon_count` in localStorage
- When count >= 2 and not authenticated → show soft gate modal (new component)
- For anonymous users: skip auth header in API calls, pass `?anon=true` (backend serves without quota check, limited to 2)
- Update greeting to use Cormorant Garamond 600
- Apply Temple at Dusk colors throughout
- Glass header with `backdrop-filter: blur(12px)`
- Example question pills with updated styling

### 3.3 RichAnswer.tsx — Styling Only

**NO logic changes.** The two-tier Sanskrit detection, verse/translation/paragraph block system, and inline highlighting all stay intact.

**Style changes:**
- Verse text color: `#c75b39` → `#e07050` (brighter vermillion, WCAG AA)
- Body line-height: 1.9 → 2.0
- Font: Georgia → Cormorant Garamond (via Tailwind config)
- Verse block background: enhanced gradient wash
- Translation block: font-weight 600 for more distinction
- All color vars updated to Temple at Dusk

### 3.4 AudioPlayer.tsx — Style Refresh

**Logic preserved.** Polling, timeout, play/pause, progress tracking all stay.

**Style changes:**
- Redesigned as a persistent bar below tabs (not floating)
- Double-ring play button (outer glow ring via `::before` pseudo-element)
- Progress gradient: vermillion → gold
- Time display: `font-variant-numeric: tabular-nums` (prevents jitter)
- 44px play button touch target

### 3.5 New Component: ShareBar.tsx

```tsx
interface ShareBarProps {
  answerText: string;
  question: string;
}
```

**Buttons:**
- **Copy:** `navigator.clipboard.writeText()` — formats answer with verse references
- **Share:** `navigator.share({ title, text, url })` on mobile, fallback to copy URL on desktop
- **Tweet:** `window.open()` with Twitter intent URL, pre-filled with truncated answer

**Position:** Fixed at bottom of answer screen, glass backdrop-blur background.

### 3.6 New Component: SoftGate.tsx

Replaces `QuotaWall.tsx` behavior for anonymous users.

```tsx
interface SoftGateProps {
  onSignIn: () => void;
}
```

**Content:** "You've tasted the nectar" heading, devotional subtitle, animated arati flames, Google Sign-In CTA, footer note about saved answers.

### 3.7 New Component: AratiDivider.tsx

Reusable CSS-only animated flame divider. Used in auth screen, soft gate, and optionally in answer display between sections.

### 3.8 globals.css Updates

- Replace all CSS custom properties with Temple at Dusk values
- Add noise texture overlay (`body::before`)
- Add Cormorant Garamond + Cinzel font-family declarations (fonts loaded via `<link>` in layout.tsx, see section 2.2)
- Update scrollbar colors
- Update streaming cursor color (saffron → gold)
- Add glass card utility class
- Add arati flame animation keyframes
- Add pulse-ring animation keyframes

### 3.9 tailwind.config.ts Updates

- Replace `saffron` color scale with `gold` scale based on `#c9a84c`
- Add `vermillion` color scale based on `#c24d2c`
- Add `tulsi` color scale based on `#4a8c3f`
- Update font families: `serif` → `['Cormorant Garamond', 'Georgia', 'serif']`
- Add `display` font family: `['Cinzel', 'serif']`

---

## 4. Deployment Architecture

### 4.1 Static Export

```
next.config.ts changes:
  - Add: output: 'export'
  - Remove: rewrites (no proxy needed — same origin)
  - Add: images: { unoptimized: true } (required for static export)
```

**Build command:** `cd web && npm run build` → outputs to `web/out/`

### 4.2 FastAPI Static File Serving

Add to `api/main.py` AFTER all API route definitions:

```python
from fastapi.staticfiles import StaticFiles

# Serve frontend (must be LAST — catches all non-API routes)
frontend_dir = PROJECT_ROOT / "web" / "out"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
```

`html=True` enables SPA-style routing: `/history` serves `history.html`, `/auth` serves `auth.html`.

### 4.3 Docker Multi-Stage Build

```dockerfile
# Stage 1: Build frontend
FROM node:20-slim AS frontend
WORKDIR /web
COPY web/package*.json ./
RUN npm ci --production=false
COPY web/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim
WORKDIR /app

# Install dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./api/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY rag_query.py .
COPY data_local/ ./data_local/

# Copy FAISS index (baked in — ~1.1GB)
COPY faiss_indexes/ ./faiss_indexes/

# Copy embeddings cache (for query embedding lookups)
COPY embeddings_cache.db .

# Copy built frontend
COPY --from=frontend /web/out ./web/out

# Do NOT copy: embeddings/, embeddings_optimized/, logs/, .env, node_modules/
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### 4.4 .dockerignore

```
embeddings/
embeddings_optimized/
logs/
.env
.env.*
web/node_modules/
web/.next/
.superpowers/
*.log
*.md
!README.md
tests/
__pycache__/
.git/
```

### 4.5 Railway Configuration

**railway.toml:**
```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/api/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
numReplicas = 1
```

**Environment variables to set on Railway dashboard:**

| Variable | Value | Required |
|----------|-------|----------|
| `VOYAGE_API_KEY` | (from .env) | Yes — embedding queries |
| `ANTHROPIC_API_KEY` | (from .env) | Yes — Claude answers |
| `ELEVENLABS_API_KEY` | (from .env) | Yes — voice synthesis |
| `ELEVENLABS_VOICE_ID` | `NkwRXQbcKij4CMmXWWt5` | Yes — Prabhupada clone |
| `JWT_SECRET` | (generate random 64-char) | Yes — auth tokens |
| `GOOGLE_CLIENT_ID` | (from Google Cloud Console) | Yes — OAuth |
| `ALLOWED_ORIGINS` | `https://<railway-app>.up.railway.app` | Yes — CORS |
| `DATA_DIR` | `/data` | **Yes — persistent volume mount** |
| `RATE_LIMIT_REQUESTS` | `10` | Optional (default 10) |

### 4.6 Database Persistence (REQUIRED)

SQLite (`api/database.py`) uses `DATA_DIR` env var (defaults to `data_local/`). On Railway, the filesystem is ephemeral — **without a persistent volume, all user accounts, history, and quota data are lost on every redeploy.**

**Required setup on Railway:**
1. Create a persistent volume mounted at `/data`
2. Set env var `DATA_DIR=/data`
3. Database auto-creates at `/data/prabhupada.db`

This is a zero-code change — `database.py` already reads `DATA_DIR` from env (line 22).

**Why this is not optional:** Without persistence, (a) user history vanishes, (b) quota resets let users get unlimited free questions, (c) the anonymous trial system becomes pointless since users can just wait for redeploy.

### 4.7 Resource Budget (Railway Hobby Plan — 8GB RAM)

| Component | RAM Usage | Notes |
|-----------|-----------|-------|
| Python runtime + FastAPI | ~150MB | Base overhead |
| FAISS IVF100 index | ~700MB | Index loaded into memory at startup |
| metadata.json (161K chunks) | ~540MB | Loaded by search function |
| Semantic answer cache | ~50MB | Grows with cached answers |
| Embedding cache (SQLite) | ~5MB | Query embedding lookups |
| OS + buffers | ~200MB | Linux overhead |
| **Total baseline** | **~1.65GB** | |
| **Headroom** | **~6.35GB** | Comfortable for spikes |

**Verification step:** After first Railway deploy, run `railway logs` and check for OOM kills. If memory exceeds 4GB, investigate metadata.json lazy loading.

### 4.8 CORS Update

Update `api/main.py` ALLOWED_ORIGINS default to include `localhost:8000` (for static-served frontend in dev):

```python
_default_origins = "http://localhost:3000,http://localhost:3001,http://localhost:8000"
```

The Railway production URL will be set via `ALLOWED_ORIGINS` env var. Since frontend and backend are same-origin on Railway, CORS won't apply for the static-served frontend — but it's needed for local development. **Verified:** `web/lib/api.ts` uses relative URLs (`/api/query/stream`) so same-origin works correctly.

### 4.9 Static Export Pre-Validation (Gate)

**Before making any visual changes**, run a test static export on the current codebase:

```bash
cd web && npm run build
```

With `output: 'export'` in next.config.ts, Next.js 15 requires:
- All pages must be client components or statically deterministic
- `useSearchParams()` requires `<Suspense>` boundary
- No `headers()` or `cookies()` calls in components
- Any future dynamic routes (e.g., `[id]`) will need `generateStaticParams` — current app has none, so this is a note for later

If the build fails, document which components need `'use client'` or Suspense wrapping. This is a **gate** — fix build errors before proceeding with visual changes.

---

## 5. Anonymous Trial System

### 5.1 Frontend (localStorage)

```typescript
const ANON_COUNT_KEY = 'prabhupada_anon_count';
const ANON_MODE_KEY = 'prabhupada_anon_mode';
const MAX_ANON_QUERIES = 2;

function getAnonCount(): number {
  return parseInt(localStorage.getItem(ANON_COUNT_KEY) || '0', 10);
}

function incrementAnonCount(): void {
  const count = getAnonCount() + 1;
  localStorage.setItem(ANON_COUNT_KEY, count.toString());
}

function isAnonExhausted(): boolean {
  return getAnonCount() >= MAX_ANON_QUERIES;
}
```

### 5.2 Backend (api/main.py)

Add `optional_auth` dependency for query endpoints when `anon=true`:

```python
@app.get("/api/query/stream")
async def query_stream(
    request: Request,
    question: str = Query(..., min_length=1, max_length=500),
    top_k: int = Query(default=5, ge=1, le=20),
    include_voice: bool = Query(default=False),
    anon: bool = Query(default=False),
    user_id: str = Depends(optional_auth),  # Returns None for anon
):
```

- If `anon=True` and no auth token: allow query but skip quota/history
- Rate limiting still applies (per-IP) — **stricter for anonymous**: 3 req/IP/hour (vs 10 req/60s for authenticated)
- Voice disabled for anonymous users (`include_voice` forced to False)
- Anonymous rate limit implemented as a separate sliding window keyed by IP + `anon` flag

### 5.3 Edge Cases

- User clears localStorage → gets 2 more free questions (acceptable for MVP)
- User signs in after anonymous questions → anonymous answers NOT transferred (too complex for MVP)
- User in private/incognito → gets 2 questions per session (acceptable)

---

## 6. Share Feature

### 6.1 ShareBar Component

```typescript
function formatAnswerForShare(question: string, answer: string): string {
  // Strip markdown, keep verse references
  const clean = answer
    .replace(/#{1,3}\s/g, '')      // Remove headers
    .replace(/\*\*/g, '')          // Remove bold
    .replace(/^\s*[-•]\s/gm, '• ') // Normalize bullets
    .trim();

  return `Q: ${question}\n\n${clean.slice(0, 500)}...\n\n— Prabhupada AI`;
}
```

### 6.2 Actions

- **Copy:** `navigator.clipboard.writeText(formatted)` → show toast "Copied to clipboard" for 2s
- **Share (mobile):** `navigator.share({ title: 'Prabhupada AI', text: formatted })` → native share sheet
- **Share (desktop fallback):** Copy URL to clipboard
- **Tweet:** Open `https://x.com/intent/tweet?text=` with URL-encoded truncated text (280 char limit)

---

## 7. Performance Budget

| Metric | Target | How |
|--------|--------|-----|
| First Contentful Paint | < 1.5s | Static HTML, inline critical CSS |
| Largest Contentful Paint | < 2.5s | Fonts load async via `display=swap` |
| Total JS bundle | < 200KB gzipped | Next.js static export, no SSR runtime |
| Font payload | < 30KB | Only 2 Google Fonts, subset latin + latin-ext |
| FAISS search | < 0.5s | Pre-loaded index in memory |
| Time to first answer chunk | < 3s | SSE streaming starts after FAISS search |
| Animation performance | 60fps | CSS-only animations, no JS animation libraries |
| Mobile touch targets | ≥ 44px | All buttons, pills, toggles |

---

## 8. Quality Gates

### 8.1 Pre-Implementation Checks

- [ ] `.env.example` updated with all required keys
- [ ] `.dockerignore` excludes embeddings, logs, .env
- [ ] `web/out/` added to `.gitignore`
- [ ] `.superpowers/` added to `.gitignore`

### 8.2 Post-Implementation — Automated

- [ ] `npm run build` succeeds (static export)
- [ ] `python -m pytest tests/` passes
- [ ] Docker build completes
- [ ] `/api/health` returns 200 with `faiss_loaded: true`
- [ ] All 4 screens render correctly on mobile (375px viewport)

### 8.3 Post-Implementation — Code Review Agent

Dispatch `superpowers:requesting-code-review` agent with review context:

**Critical checks:**
1. **Auth bypass** — Can anonymous users access more than 2 queries? Is rate limiting still active?
2. **XSS** — Is user input sanitized in ShareBar (clipboard, tweet intent)?
3. **CORS** — Is `ALLOWED_ORIGINS` properly configured for Railway?
4. **Static serving** — Does `StaticFiles(html=True)` correctly serve SPA routes without breaking API routes?
5. **Font loading** — Are Google Fonts loaded with `display=swap` to prevent FOIT?
6. **localStorage** — Is anonymous count tamper-resistant enough for MVP? (Answer: yes — it's just a friction gate, not a security boundary)
7. **Docker** — Are secrets excluded from image? Is `.env` in `.dockerignore`?
8. **Memory** — Does FAISS index fit in Railway Hobby plan's 8GB RAM?

**Informational checks:**
1. Dead code removed (old color variables, unused components)
2. Consistent use of new CSS variables throughout
3. No console.log statements
4. All loading/empty/error states handled
5. Touch targets ≥ 44px on all interactive elements

---

## 9. Files Changed (Expected)

### Modified
- `web/app/page.tsx` — anonymous trial logic, Temple at Dusk styling
- `web/app/auth/page.tsx` — "Try 2 Free" CTA, pulsing rings, arati flames
- `web/app/history/page.tsx` — updated colors
- `web/app/layout.tsx` — Google Fonts link, updated metadata
- `web/app/globals.css` — complete color/animation overhaul
- `web/tailwind.config.ts` — new color scales, font families
- `web/next.config.ts` — `output: 'export'`, remove rewrites
- `web/components/RichAnswer.tsx` — color updates only
- `web/components/AIAnswer.tsx` — color updates
- `web/components/AudioPlayer.tsx` — bar layout, double-ring, colors
- `web/components/QuestionInput.tsx` — styling, pill updates
- `web/components/AnswerTabs.tsx` — tab styling
- `web/components/QuotaBar.tsx` — color updates
- `web/components/QuotaWall.tsx` — replaced by SoftGate for anon users
- `web/components/AuthProvider.tsx` — support anonymous mode
- `web/lib/api.ts` — add `anon` param to query functions
- `web/lib/auth.ts` — add anonymous mode helpers
- `api/main.py` — static file serving, optional auth for anon
- `api/middleware.py` — optional_auth dependency
- `Dockerfile` — multi-stage build
- `.dockerignore` — new file
- `railway.toml` — updated config
- `.env.example` — updated with all keys

### New
- `web/components/ShareBar.tsx` — copy/share/tweet
- `web/components/SoftGate.tsx` — anonymous trial exhausted modal
- `web/components/AratiDivider.tsx` — reusable flame divider
- `.dockerignore` — exclude large files from image

### Not Changed
- `web/components/RichAnswer.tsx` — logic untouched (only CSS)
- `web/components/ScriptureResults.tsx` — styling updates, logic preserved
- `web/lib/scriptures.ts` — no changes
- `api/main.py` — core query/streaming/audio logic untouched
- `scripts/*` — no changes to RAG pipeline
- `faiss_indexes/*` — no changes
- `rag_query.py` — no changes

---

## 10. Implementation Order

1. **Visual foundation** — globals.css, tailwind.config.ts, layout.tsx (fonts)
2. **Reusable components** — AratiDivider, ShareBar, SoftGate
3. **Auth flow** — auth page redesign, AuthProvider anonymous mode
4. **Main page** — query screen styling, anonymous trial logic
5. **Answer display** — RichAnswer colors, AudioPlayer bar, AnswerTabs
6. **History page** — color updates
7. **Static export** — next.config.ts, test build
8. **Backend integration** — FastAPI static serving, optional auth, CORS
9. **Docker** — multi-stage Dockerfile, .dockerignore
10. **Railway deploy** — push, set env vars, verify health check
11. **Post-deploy verification** — all screens on mobile, voice works, share works
12. **Code review agent** — dispatch superpowers:requesting-code-review
