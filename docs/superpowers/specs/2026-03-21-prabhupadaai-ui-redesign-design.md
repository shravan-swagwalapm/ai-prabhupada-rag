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

**Required code change:** Replace `Depends(get_current_user)` with `Depends(optional_auth)` on BOTH `/api/query` and `/api/query/stream` endpoints. Current code at `api/main.py:528` uses `get_current_user` which returns 401 for unauthenticated requests — this blocks anonymous users.

```python
# CHANGE FROM (current):
user_id: str = Depends(get_current_user)

# CHANGE TO:
@app.get("/api/query/stream")
async def query_stream(
    request: Request,
    question: str = Query(..., min_length=1, max_length=500),
    top_k: int = Query(default=5, ge=1, le=20),
    include_voice: bool = Query(default=False),
    anon: bool = Query(default=False),
    user_id: Optional[str] = Depends(optional_auth),  # Returns None for anon
):
```

- If `anon=True` and `user_id is None`: allow query but skip quota/history
- Rate limiting still applies (per-IP) — **stricter for anonymous**: 3 req/IP/hour (vs 10 req/60s for authenticated)
- Voice disabled for anonymous users (`include_voice` forced to False)
- Anonymous rate limit: refactor `_is_rate_limited()` to accept a `window_secs` and `max_requests` param, then call with `(ip, 3600, 3)` for anonymous vs `(ip, 60, 10)` for authenticated

```python
def _is_rate_limited(client_ip: str, window_secs: int = None, max_requests: int = None) -> bool:
    """Rate limit with configurable window. Defaults to env var settings."""
    window_secs = window_secs or _RATE_LIMIT_WINDOW_SECS
    max_requests = max_requests or _RATE_LIMIT_REQUESTS
    # ... existing sliding window logic with parameterized values
```

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

**Answer quality checks:**
1. **Relevance floor** — Low-relevance queries (<50%) show graceful "no match" message, not hallucinated answers
2. **Voice quota** — Daily reset working, not lifetime depletion
3. **Audio persistence** — Audio files stored in `DATA_DIR` (persistent volume), not ephemeral `api/audio_cache/`
4. **Semantic cache** — Cache hits return correct mode (voice cached answer shouldn't serve as text answer)
5. **Cost ceiling** — ElevenLabs usage trackable via dashboard, voice disabled for anonymous

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
- `api/main.py` — static file serving, optional auth for anon, relevance floor, audio cache in DATA_DIR, anon rate limit
- `api/middleware.py` — optional_auth dependency
- `api/database.py` — voice daily reset fields (voice_uses_today, voice_reset_date)
- `Dockerfile` — multi-stage build
- `.dockerignore` — new file
- `railway.toml` — updated config
- `.env.example` — updated with all keys

### New
- `web/components/ShareBar.tsx` — copy/share/tweet
- `web/components/SoftGate.tsx` — anonymous trial exhausted modal
- `web/components/AratiDivider.tsx` — reusable flame divider
- `.dockerignore` — exclude large files from image

### Not Changed (logic preserved)
- `web/components/RichAnswer.tsx` — CSS only, two-tier Sanskrit detection untouched
- `web/components/ScriptureResults.tsx` — styling updates, logic preserved
- `web/lib/scriptures.ts` — no changes
- `scripts/*` — no changes to RAG pipeline or generate_answer.py prompts
- `faiss_indexes/*` — no changes
- `rag_query.py` — no changes
- `api/answer_cache.py` — no changes (SIMILARITY_THRESHOLD=0.92 stays)

---

## 10. Answer Quality Guardrails

### 10.1 Relevance Floor

FAISS returns results even when nothing is relevant. Without a floor, Claude fabricates answers grounded in irrelevant passages.

**Implementation** (in streaming and POST query handlers):

```python
MIN_RELEVANCE_SCORE = 0.50  # Below this, passages are noise — start strict, loosen if needed

# After FAISS search, filter results
relevant_results = [r for r in raw_results if r.get("similarity", 0) >= MIN_RELEVANCE_SCORE]

if not relevant_results:
    # Return passages for transparency but skip AI answer
    yield {"type": "no_match", "message": "I could not find a direct teaching on this topic in Prabhupada's books. Try rephrasing with specific scripture terms."}
    return
```

**Why 0.50?** Measured from 7 cached recordings: lowest useful hit was 63.7% (material failure). A floor of 0.50 provides generous headroom below that while filtering genuine noise. Start strict — it's easier to loosen (users won't notice a floor decrease) than to tighten (users will notice worse answers). Make this an env var (`MIN_RELEVANCE_SCORE`) so it can be tuned in production without redeploying.

### 10.2 Top-k Tuning

Current default: `top_k=5`. This is correct for the corpus size (161K chunks). Do NOT increase above 10 — more passages dilute relevance and increase Claude token costs.

**Frontend:** Lock `top_k` to 5 for all users. Remove it from the API client params. The `ge=1, le=20` backend validation stays as a safety net, but frontend should never send >5.

### 10.3 Answer Quality Signals (Frontend)

Display relevance scores on the Sources tab to build trust:

```
Sources (5) — Top relevance: 78.4%
├── BG 2.20 (78.4%) — na jāyate mriyate vā kadācin...
├── BG 2.13 (72.1%) — dehino 'smin yathā dehe...
└── SB 3.25.33 (65.2%) — ...
```

Color-code: ≥70% green (tulsi), 50-70% gold, <50% muted.

### 10.4 Streaming Prompt Selection

The spec currently uses `mode="full"` for text and `mode="concise"` for voice. This is correct and must not change. The "full" prompt produces 800-1200 word answers with markdown formatting (headers, bold, verse blocks) — exactly what `RichAnswer.tsx` renders. The "concise" prompt produces 360-450 word flowing prose — exactly what ElevenLabs can synthesize naturally.

**Critical:** Never use the concise prompt for text-only answers. Users paying with quota expect comprehensive scripture-grounded responses, not abbreviated voice scripts.

---

## 11. Cost Control

### 11.1 Cost Per Query (Current)

| Component | Cost | Calculation |
|-----------|------|-------------|
| FAISS search | ~$0.00001 | Voyage API embedding, 80% cached |
| Claude Sonnet (full mode) | **~$0.022** | ~1500 input × $3/1M = $0.0045 + ~1200 output × $15/1M = $0.018 |
| Claude Sonnet (concise) | **~$0.012** | ~1500 input × $3/1M = $0.0045 + ~500 output × $15/1M = $0.0075 |
| ElevenLabs v3 (~1 min) | ~$0.15-0.30 | Voice answers only |
| **Total (text only)** | **~$0.022** | |
| **Total (with voice)** | **~$0.17-0.33** | |
| **Cached (semantic hit)** | **~$0.00** | 92% similarity threshold |

*Pricing: Claude Sonnet 4.5 at $3/1M input, $15/1M output. Verify at deploy time — model pricing may change.*

### 11.2 Cost Guardrails (Implement These)

**A. Semantic cache (already exists, verify threshold):**
- `SIMILARITY_THRESHOLD = 0.92` in `answer_cache.py` — this is aggressive enough. At 0.92, "What is the soul?" and "What is the atma?" will cache-hit. Identical rephrases are caught.
- **Action:** No change needed. Verify cache is working post-deploy via `/api/health` response (`cache_entries` field).

**B. Audio file caching (NEW — add to backend):**
When a semantic cache hit has an `audio_id`, check if the MP3 file still exists on disk. If yes, serve it directly (zero ElevenLabs cost). If the file was evicted, regenerate.

```python
# In audio endpoint — check persistent volume first
audio_path = AUDIO_CACHE_DIR / f"{audio_id}.mp3"
if audio_path.exists():
    return FileResponse(audio_path, media_type="audio/mpeg")
# else: trigger regeneration
```

**Current code has the serve-from-disk logic** (`api/main.py:708` checks `audio_path.exists()` and returns `FileResponse`). However, `AUDIO_CACHE_DIR` is hardcoded to `PROJECT_ROOT / "api" / "audio_cache"` (ephemeral on Railway). Audio files are lost on every redeploy. **Required change:** Move `AUDIO_CACHE_DIR` to `DATA_DIR` (persistent volume):

```python
# Change from:
AUDIO_CACHE_DIR = PROJECT_ROOT / "api" / "audio_cache"
# To:
AUDIO_CACHE_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data_local"))) / "audio_cache"
```

This single-line change means cached voice responses survive redeploys. At $0.15-0.30 per generation, this saves significant money.

**C. Per-user voice daily cap (NEW):**
Default `voice_quota=3` in database is a lifetime cap — once exhausted, user can never use voice again. This is a product bug.

**Fix in implementation:** Change voice quota to a daily reset model:
- Add two columns to users table: `voice_uses_today INTEGER DEFAULT 0` and `voice_reset_date TEXT`
- Reset counter when `voice_reset_date != today` (check at query time, not via cron)
- Default: 3 voice queries per day per user
- Keep existing `voice_quota` column as-is (unused but harmless — avoids migration risk)

**Migration SQL** (add to `init_db()` after table creation):
```sql
-- Idempotent: ALTER TABLE fails silently if columns exist
ALTER TABLE users ADD COLUMN voice_uses_today INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN voice_reset_date TEXT;
```

**Note:** SQLite's `ALTER TABLE ADD COLUMN` is safe — existing rows get the default value. Wrap each statement in try/except to handle the "duplicate column name" error on subsequent startups. Existing users with `voice_quota=0` are NOT affected — the new daily system is independent of the old lifetime quota.

**D. Anonymous users: text-only (already in spec):**
Section 5.2 already disables voice for anonymous users. This is the most important cost control — unauthenticated users get zero ElevenLabs costs.

**E. Monthly cost ceiling:**
At full capacity (100 users × 3 voice/day × 30 days):
- Voice: 9,000 × $0.20 = **$1,800/month** ← dangerous
- Text: 9,000 × $0.022 = **$198/month** ← manageable
- With 30% semantic cache hit rate: voice drops to **$1,260/month**, text to **$139/month**

**Mitigation:** Keep initial voice quota at 3/day, monitor via ElevenLabs dashboard. At 10 active users (realistic MVP), monthly voice cost is ~$180. Cache popular questions' audio permanently on the persistent volume.

### 11.3 Model Fallback

If `ANTHROPIC_MODEL` env var is not set, the system defaults to `claude-sonnet-4-5-20250929`. Check for a newer Sonnet version at deploy time and update the env var if available. Do NOT fall back to Haiku for cost savings — answer quality is the product's core value proposition.

**Exception:** If Anthropic API returns 529 (overloaded), the current code raises an exception. Consider adding a single retry with 2s backoff before failing.

---

## 12. Scalability Guardrails

### 12.1 What Works at MVP Scale (1-100 concurrent users)

- **SQLite + WAL mode** — WAL allows concurrent reads during writes. Writes are still serialized, but at MVP scale (~10-100 writes/min for quota + history), this is well within SQLite's capabilities. Read throughput is thousands/sec.
- **In-memory semantic cache** — `np.ndarray` with 1000 entries max. Matrix multiply for lookup is <1ms even at 1000 entries.
- **Single uvicorn worker** — Railway Hobby plan has 1 vCPU. Multiple workers would fight over FAISS index memory. Keep `--workers 1`.
- **Thread-per-voice-request** — ElevenLabs synthesis is I/O bound. Threading is correct here. Max concurrent threads bounded by audio job registry (500).

### 12.2 What to Watch

| Signal | Threshold | Action |
|--------|-----------|--------|
| Memory usage | >4GB | Investigate metadata.json lazy loading |
| SQLite lock contention | >100ms write latency | Add connection pooling or switch to Postgres |
| Rate limit store size | >10K IPs | Already has cleanup at 5000, but verify in logs |
| Audio cache disk | >5GB | Add LRU eviction for audio files in `DATA_DIR` |
| FAISS cold start | >5s | Pre-warm in lifespan (already done) |
| Semantic cache | >500 entries | Already has LRU at 1000, but monitor RAM |

### 12.3 NOT Doing Now (Future Scale)

These are explicitly out of scope for this deployment. Document them so we don't over-engineer:

- **Postgres migration** — Only needed if SQLite write contention becomes a bottleneck (unlikely under 1000 daily users)
- **Redis caching** — Only needed if semantic cache needs to be shared across multiple workers
- **CDN for audio** — Only needed if audio bandwidth exceeds Railway's included bandwidth
- **FAISS sharding** — Only needed if index exceeds 1M vectors (currently 161K)
- **Horizontal scaling** — Only needed if single Railway instance can't handle traffic (8GB RAM, 1 vCPU is generous for MVP)

---

## 13. Implementation Order

1. **Visual foundation** — globals.css, tailwind.config.ts, layout.tsx (fonts)
2. **Reusable components** — AratiDivider, ShareBar, SoftGate
3. **Auth flow** — auth page redesign, AuthProvider anonymous mode
4. **Main page** — query screen styling, anonymous trial logic
5. **Answer display** — RichAnswer colors, AudioPlayer bar, AnswerTabs, relevance score display on Sources tab
6. **History page** — color updates
7. **Static export** — next.config.ts, test build
8. **Backend hardening** — Relevance floor (MIN_RELEVANCE_SCORE=0.50, env-configurable), audio cache in DATA_DIR, anonymous rate limit (3 req/IP/hour via dual-window rate limiter), voice daily reset quota (migration SQL), streaming endpoint → `optional_auth`
9. **Backend integration** — FastAPI static serving, optional auth, CORS, localhost:8000 in ALLOWED_ORIGINS default
10. **Docker** — multi-stage Dockerfile, .dockerignore
11. **Railway deploy** — push, set env vars, persistent volume at /data, verify health check
12. **Post-deploy verification** — all screens on mobile, voice works, share works, semantic cache populated, audio persists across simulated redeploy
13. **Code review agent** — dispatch superpowers:requesting-code-review with answer quality + cost + scalability review context
