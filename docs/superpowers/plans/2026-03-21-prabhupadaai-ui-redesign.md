# PrabhupadaAI UI Redesign + Railway Deployment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the PrabhupadaAI web app with a "Temple at Dusk" spiritual aesthetic, add share/subscribe features, harden answer quality & cost controls, and deploy as a single Railway service.

**Architecture:** Next.js 15 static export served by FastAPI on same origin. FAISS index baked into Docker image. Google Sign-In required (auth-first), 5 text + 2 voice lifetime quota, SubscribeGate collects email when exhausted.

**Tech Stack:** Next.js 15 (static export), React 19, Tailwind CSS, FastAPI, FAISS, Claude Sonnet 4.5, ElevenLabs v3, SQLite (WAL), Docker multi-stage, Railway

**Spec:** `docs/superpowers/specs/2026-03-21-prabhupadaai-ui-redesign-design.md`

---

## File Map

### Modified
| File | Responsibility | Task |
|------|----------------|------|
| `web/app/globals.css` | CSS variables, animations, noise overlay | 1 |
| `web/tailwind.config.ts` | Color scales, font families | 1 |
| `web/app/layout.tsx` | Google Fonts `<link>`, metadata | 1 |
| `web/next.config.ts` | `output: 'export'`, remove rewrites | 7 |
| `web/app/auth/page.tsx` | Auth screen redesign | 3 |
| `web/app/page.tsx` | Quota display, SubscribeGate on 402, styling | 4 |
| `web/app/history/page.tsx` | Color updates | 6 |
| `web/components/RichAnswer.tsx` | Color/font CSS updates only | 5 |
| `web/components/AIAnswer.tsx` | Color updates | 5 |
| `web/components/AudioPlayer.tsx` | Bar layout, double-ring, colors | 5 |
| `web/components/QuestionInput.tsx` | Styling, pill updates | 4 |
| `web/components/AnswerTabs.tsx` | Tab styling | 5 |
| `web/components/ScriptureResults.tsx` | Relevance color-coding, header format | 5 |
| `web/components/QuotaBar.tsx` | Color updates, show x of y format | 4 |
| `web/components/AuthProvider.tsx` | Cleanup (remove any anon refs) | 3 |
| `web/lib/api.ts` | Add `no_match` SSE handler | 8 |
| `api/main.py` | Static serving, relevance floor, audio cache path, CORS, dead code | 8, 9 |
| `api/database.py` | Quota defaults 5/2, SQL defaults | 8 |
| `Dockerfile` | Multi-stage build | 10 |
| `railway.toml` | Updated config | 10 |

### New
| File | Responsibility | Task |
|------|----------------|------|
| `web/components/AratiDivider.tsx` | Reusable CSS flame divider | 2 |
| `web/components/ShareBar.tsx` | Copy/share/tweet actions | 2 |
| `web/components/SubscribeGate.tsx` | Quota-exhausted email gate | 2 |
| `.dockerignore` | Exclude large files from image | 10 |
| `.env.example` | Document all required keys | 10 |

### Deleted
| File | Reason | Task |
|------|--------|------|
| `web/components/QuotaWall.tsx` | Replaced by SubscribeGate | 2 |

---

## Task 0: Pre-flight — Static Export Validation

Per spec section 4.9, validate static export works on the current codebase **before** making any visual changes.

- [ ] **Step 1: Test static export on current code**

```bash
cd web
# Temporarily add output: 'export' to next.config.ts
echo 'import type { NextConfig } from "next"; const c: NextConfig = { output: "export", images: { unoptimized: true } }; export default c;' > next.config.tmp.ts
cp next.config.ts next.config.ts.bak
cp next.config.tmp.ts next.config.ts
npm run build
```

If build fails, note the errors (missing `'use client'`, `useSearchParams` without `<Suspense>`, `headers()`/`cookies()` calls). These must be fixed during Tasks 1-6.

- [ ] **Step 2: Restore original config**

```bash
cp next.config.ts.bak next.config.ts
rm next.config.tmp.ts next.config.ts.bak web/out -rf 2>/dev/null
```

Document any failures found — they'll be addressed inline during later tasks.

---

## Task 1: Visual Foundation

**Files:**
- Modify: `web/app/globals.css`
- Modify: `web/tailwind.config.ts`
- Modify: `web/app/layout.tsx`

- [ ] **Step 1: Replace CSS variables in globals.css**

Replace the existing `:root` block and add new animations. The full color system is in spec section 2.1. Key changes:

```css
:root {
  /* Backgrounds — The Sanctum */
  --sanctum: #060403;
  --temple-dark: #0c0908;
  --altar: #161009;
  --card: #1c150e;
  --card-hover: #231a12;

  /* Sacred Accents — Arati Flame */
  --gold: #c9a84c;
  --gold-bright: #dbb85a;
  --gold-dim: #a08940;
  --vermillion: #c24d2c;
  --vermillion-bright: #e07050;
  --tulsi: #4a8c3f;

  /* Text — Deity Darshan Glow */
  --text-primary: #f7f0e3;
  --text-body: rgba(247,240,227,0.88);
  --text-secondary: rgba(247,240,227,0.6);
  --text-muted: rgba(247,240,227,0.4);
  --text-ghost: rgba(247,240,227,0.25);

  /* Glass & Borders */
  --glass: rgba(22,16,9,0.6);
  --glass-border: rgba(201,168,76,0.08);
  --glass-border-hover: rgba(201,168,76,0.15);
}
```

Add noise texture overlay, arati flame keyframes, pulse-ring keyframes, glass card utility, and updated scrollbar/cursor colors. See spec section 2.3-2.4 and 3.8 for full list.

Add `body::before` noise overlay:
```css
body::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
  opacity: 0.03;
  background-image: url("data:image/svg+xml,..."); /* inline SVG feTurbulence */
}
```

Add arati flame animation:
```css
@keyframes arati-flicker {
  0%, 100% { transform: scaleY(1) scaleX(1); }
  25% { transform: scaleY(1.15) scaleX(0.95); }
  50% { transform: scaleY(0.9) scaleX(1.05); }
  75% { transform: scaleY(1.1) scaleX(0.97); }
}

@keyframes pulse-ring {
  0% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.15); opacity: 0.2; }
  100% { transform: scale(1); opacity: 0.6; }
}
```

- [ ] **Step 2: Update tailwind.config.ts**

Replace `saffron` scale with `gold`, add `vermillion` and `tulsi`, update fonts:

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        gold: {
          50: '#fdf8e8', 100: '#f9edd0', 200: '#f0d89a',
          300: '#e4c064', 400: '#dbb85a', 500: '#c9a84c',
          600: '#a08940', 700: '#7a6a32', 800: '#544a24',
          900: '#2e2916', DEFAULT: '#c9a84c',
        },
        vermillion: {
          50: '#fef0ec', 300: '#e07050', 500: '#c24d2c',
          700: '#8a3620', DEFAULT: '#c24d2c',
        },
        tulsi: {
          50: '#edf5eb', 500: '#4a8c3f', 700: '#356b2d',
          DEFAULT: '#4a8c3f',
        },
        sanctum: '#060403',
        altar: '#161009',
        card: { DEFAULT: '#1c150e', hover: '#231a12' },
      },
      fontFamily: {
        serif: ['Cormorant Garamond', 'Georgia', 'Cambria', 'Times New Roman', 'serif'],
        display: ['Cinzel', 'serif'],
      },
    },
  },
  plugins: [],
};
export default config;
```

- [ ] **Step 3: Add Google Fonts to layout.tsx**

Add `<link>` tags in the `<head>` (NOT CSS `@import`). Also update metadata theme-color and description:

```tsx
// In <head>:
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
<link
  href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,500&display=swap"
  rel="stylesheet"
/>
```

Update `themeColor` to `#060403` (sanctum), update description.

- [ ] **Step 4: Verify fonts render**

Run: `cd web && npm run dev`

Open browser, inspect page — confirm Cormorant Garamond and Cinzel are loading. Check "Hare Kṛṣṇa" renders correctly (no broken diacriticals).

- [ ] **Step 5: Commit**

```bash
git add web/app/globals.css web/tailwind.config.ts web/app/layout.tsx
git commit -m "feat: Temple at Dusk visual foundation — colors, fonts, animations"
```

---

## Task 2: Reusable Components

**Files:**
- Create: `web/components/AratiDivider.tsx`
- Create: `web/components/ShareBar.tsx`
- Create: `web/components/SubscribeGate.tsx`
- Delete: `web/components/QuotaWall.tsx`

- [ ] **Step 1: Create AratiDivider.tsx**

CSS-only animated flame divider. 5 pill-shaped `<div>`s with `linear-gradient` fills and the `arati-flicker` keyframe (already in globals.css from Task 1):

```tsx
'use client';

export default function AratiDivider() {
  return (
    <div className="flex items-end justify-center gap-1 py-4" aria-hidden="true">
      {[0.7, 0.85, 1, 0.85, 0.7].map((scale, i) => (
        <div
          key={i}
          className="rounded-full"
          style={{
            width: `${4 * scale}px`,
            height: `${20 * scale}px`,
            background: 'linear-gradient(to top, #c24d2c, #c9a84c, #f7f0e3)',
            animation: `arati-flicker 2s ease-in-out infinite alternate`,
            animationDelay: `${i * 0.15}s`,
          }}
        />
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create ShareBar.tsx**

Copy/Share/Tweet actions with glass backdrop. Uses `navigator.clipboard`, `navigator.share` (Web Share API), and `x.com/intent/tweet`:

```tsx
'use client';
import { useState } from 'react';

interface ShareBarProps {
  answerText: string;
  question: string;
}

function formatForShare(question: string, answer: string): string {
  const clean = answer
    .replace(/#{1,3}\s/g, '')
    .replace(/\*\*/g, '')
    .replace(/^\s*[-•]\s/gm, '• ')
    .trim();
  return `Q: ${question}\n\n${clean.slice(0, 500)}...\n\n— Prabhupada AI`;
}

export default function ShareBar({ answerText, question }: ShareBarProps) {
  const [copied, setCopied] = useState(false);
  const formatted = formatForShare(question, answerText);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(formatted);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = async () => {
    if (navigator.share) {
      await navigator.share({ title: 'Prabhupada AI', text: formatted });
    } else {
      handleCopy(); // Desktop fallback
    }
  };

  const handleTweet = () => {
    const text = encodeURIComponent(formatted.slice(0, 250) + '...');
    window.open(`https://x.com/intent/tweet?text=${text}`, '_blank');
  };

  return (
    <div className="flex gap-3 py-3 px-4 border-t"
         style={{ borderColor: 'var(--glass-border)', background: 'var(--glass)', backdropFilter: 'blur(12px)' }}>
      <button onClick={handleCopy} className="font-display text-xs tracking-wider px-4 py-2 rounded-full border transition-colors"
              style={{ borderColor: 'var(--glass-border-hover)', color: copied ? 'var(--tulsi)' : 'var(--text-secondary)' }}>
        {copied ? 'Copied ✓' : 'Copy'}
      </button>
      <button onClick={handleShare} className="font-display text-xs tracking-wider px-4 py-2 rounded-full border transition-colors"
              style={{ borderColor: 'var(--glass-border-hover)', color: 'var(--text-secondary)' }}>
        Share
      </button>
      <button onClick={handleTweet} className="font-display text-xs tracking-wider px-4 py-2 rounded-full border transition-colors"
              style={{ borderColor: 'var(--glass-border-hover)', color: 'var(--text-secondary)' }}>
        Tweet
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Create SubscribeGate.tsx**

Replaces QuotaWall. Collects email via existing `/api/waitlist` endpoint:

```tsx
'use client';
import { useState } from 'react';
import { submitWaitlist } from '@/lib/api';
import AratiDivider from './AratiDivider';

interface SubscribeGateProps {
  quotaType: 'text' | 'voice';
  userEmail: string;
  textUsed: number;
  voiceUsed: number;
  onSubmit: (email: string) => void;
  onDismiss: () => void;
}

export default function SubscribeGate({ quotaType, userEmail, textUsed, voiceUsed, onSubmit, onDismiss }: SubscribeGateProps) {
  const [email, setEmail] = useState(userEmail);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email');
      return;
    }
    try {
      await submitWaitlist(email);
      setSubmitted(true);
      onSubmit(email);
    } catch {
      setError('Something went wrong. Please try again.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(6,4,3,0.85)' }}>
      <div className="max-w-md w-full rounded-2xl p-8 text-center" style={{ background: 'var(--card)' }}>
        <AratiDivider />
        <h2 className="font-serif text-2xl font-semibold mt-4" style={{ color: 'var(--text-primary)' }}>
          You've tasted the nectar
        </h2>
        <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
          You've asked {textUsed} question{textUsed !== 1 ? 's' : ''} and received {voiceUsed} voice answer{voiceUsed !== 1 ? 's' : ''}.
        </p>
        <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
          Unlock unlimited access to Prabhupada's wisdom
        </p>

        {submitted ? (
          <p className="mt-6 text-sm" style={{ color: 'var(--tulsi)' }}>
            We'll notify you when unlimited access is available.
          </p>
        ) : (
          <div className="mt-6 space-y-3">
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              className="w-full px-4 py-3 rounded-lg text-sm bg-transparent border outline-none focus:ring-2"
              style={{ borderColor: 'var(--glass-border-hover)', color: 'var(--text-body)', outlineColor: 'var(--gold)' }}
            />
            {error && <p className="text-xs" style={{ color: '#e07050' }}>{error}</p>}
            <button onClick={handleSubmit}
                    className="w-full py-3 rounded-lg font-display text-sm tracking-wider transition-colors"
                    style={{ background: 'var(--gold)', color: 'var(--sanctum)' }}>
              Join Waitlist ✦
            </button>
          </div>
        )}

        <button onClick={onDismiss} className="mt-4 text-xs" style={{ color: 'var(--text-ghost)' }}>
          Dismiss
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Delete QuotaWall.tsx**

```bash
rm web/components/QuotaWall.tsx
```

Update any imports that reference QuotaWall → SubscribeGate (check `web/app/page.tsx`).

- [ ] **Step 5: Commit**

```bash
git add web/components/AratiDivider.tsx web/components/ShareBar.tsx web/components/SubscribeGate.tsx
git add -u  # stages the QuotaWall deletion
git commit -m "feat: add AratiDivider, ShareBar, SubscribeGate; delete QuotaWall"
```

---

## Task 3: Auth Screen Redesign

**Files:**
- Modify: `web/app/auth/page.tsx`
- Modify: `web/components/AuthProvider.tsx`

- [ ] **Step 1: Redesign auth/page.tsx**

Apply Temple at Dusk styling. Key changes per spec section 3.1:
- Title: "Hare Kṛṣṇa" in Cormorant Garamond 600
- Pulsing ring animations around avatar/icon
- AratiDivider component
- Scripture count badge: "161,724 sacred passages indexed"
- Subtitle: "5 questions free · Voice answers included"
- Google Sign-In as sole gold CTA: "Sign In to Ask Prabhupada ✦"
- Sanctum aura gradient background

- [ ] **Step 2: Clean up AuthProvider.tsx**

Remove any anonymous mode references if present. The provider should only track authenticated state.

- [ ] **Step 3: Visual test**

Run dev server, navigate to `/auth`. Verify:
- Title renders with diacriticals
- Pulsing rings animate
- Arati flames flicker
- Sign-In button is gold, prominent, 44px+ touch target
- Mobile viewport (375px) looks good

- [ ] **Step 4: Commit**

```bash
git add web/app/auth/page.tsx web/components/AuthProvider.tsx
git commit -m "feat: redesign auth screen with Temple at Dusk aesthetic"
```

---

## Task 4: Main Page Styling + Quota

**Files:**
- Modify: `web/app/page.tsx`
- Modify: `web/components/QuestionInput.tsx`
- Modify: `web/components/QuotaBar.tsx`

- [ ] **Step 1: Update page.tsx**

Per spec section 3.2:
- Glass header with `backdrop-filter: blur(12px)`
- Show remaining quota via QuotaBar: "3 of 5 questions left"
- Replace `QuotaWall` import → `SubscribeGate` import
- When API returns 402, show SubscribeGate with `userEmail` from auth context
- Apply Temple at Dusk colors to greeting, background
- Greeting in Cormorant Garamond 600

- [ ] **Step 2: Update QuotaBar.tsx**

Change from compact `{n}T {n}V` to readable: "3 of 5 questions · 1 of 2 voice"
- Green (tulsi) when quota > 0
- Vermillion when exhausted
- Use `font-display` for labels

- [ ] **Step 3: Update QuestionInput.tsx**

- Example question pills: gold border, glass background
- Input: dark background, gold focus ring glow
- Submit button: gold background, sanctum text
- 44px minimum touch targets
- Voice toggle: vermillion accent when enabled, disabled with tooltip when voice quota = 0

- [ ] **Step 4: Wire `onNoMatch` callback in page.tsx**

In the `queryStream` call inside `page.tsx`, add the `onNoMatch` callback to display the message in the answer area and hide the Sources tab:

```typescript
onNoMatch: (message) => {
  setAnswer(message);
  setPassages([]);  // hide sources
  setIsStreaming(false);
},
```

This ensures that when the backend sends a `no_match` SSE event (relevance floor not met), the user sees a helpful message instead of silence.

- [ ] **Step 5: Visual test**

Test on dev server at `/`. Verify quota display, pill styling, input focus glow, voice toggle states.

- [ ] **Step 6: Commit**

```bash
git add web/app/page.tsx web/components/QuestionInput.tsx web/components/QuotaBar.tsx
git commit -m "feat: main page Temple at Dusk styling, quota display, SubscribeGate, no_match UI"
```

---

## Task 5: Answer Display Components

**Files:**
- Modify: `web/components/RichAnswer.tsx` (CSS only)
- Modify: `web/components/AIAnswer.tsx`
- Modify: `web/components/AudioPlayer.tsx`
- Modify: `web/components/AnswerTabs.tsx`
- Modify: `web/components/ScriptureResults.tsx`

- [ ] **Step 1: Update RichAnswer.tsx — CSS only**

Per spec section 3.3 — NO logic changes:
- Verse text color: `#c75b39` → `#e07050`
- Body line-height: 1.9 → 2.0
- Font handled by Tailwind config (serif → Cormorant Garamond)
- Verse block background: enhanced gradient wash
- Translation block: font-weight 600
- All hardcoded colors → CSS variables

- [ ] **Step 2: Update AudioPlayer.tsx — CSS only**

Per spec section 3.4 — NO logic changes:
- Persistent bar below tabs (not floating)
- Double-ring play button: `::before` pseudo-element with gold glow
- Progress gradient: vermillion → gold
- `font-variant-numeric: tabular-nums` on time display
- 44px play button

- [ ] **Step 3: Update AnswerTabs.tsx**

- Tab active indicator: gold `linear-gradient` underline
- Inactive tabs: `--text-muted`
- Font: `font-display` for tab labels

- [ ] **Step 4: Update ScriptureResults.tsx — relevance color coding**

Per spec section 10.3:
- Show relevance percentage next to each source
- Color-code: ≥70% tulsi (green), 50-70% gold, <50% muted
- Header: "Sources (5) — Top relevance: 78.4%"

- [ ] **Step 5: Update AIAnswer.tsx**

- Update any hardcoded colors to CSS variables
- Ensure streaming cursor uses `--gold` color

- [ ] **Step 6: Add ShareBar to answer area**

In `page.tsx`, render `<ShareBar>` below the answer when an answer is present. Position it with glass backdrop.

- [ ] **Step 7: Commit**

```bash
git add web/components/RichAnswer.tsx web/components/AIAnswer.tsx web/components/AudioPlayer.tsx web/components/AnswerTabs.tsx web/components/ScriptureResults.tsx web/app/page.tsx
git commit -m "feat: Temple at Dusk answer display, audio bar, relevance scores, ShareBar"
```

---

## Task 6: History Page

**Files:**
- Modify: `web/app/history/page.tsx`

- [ ] **Step 1: Update colors**

Apply Temple at Dusk palette:
- Card backgrounds: `--card` / `--card-hover`
- Text colors: `--text-primary`, `--text-body`, `--text-secondary`
- Timestamps: `--text-muted`
- Border: `--glass-border`

- [ ] **Step 2: Commit**

```bash
git add web/app/history/page.tsx
git commit -m "feat: history page Temple at Dusk colors"
```

---

## Task 7: Static Export Configuration

**Files:**
- Modify: `web/next.config.ts`

- [ ] **Step 1: Update next.config.ts**

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  images: { unoptimized: true },
  // Remove rewrites — same origin on Railway, dev uses proxy separately
};

export default nextConfig;
```

- [ ] **Step 2: Update .gitignore before build**

Add `web/out/` and `.superpowers/` to `.gitignore` to prevent committing build output:

```bash
echo -e '\n# Build output\nweb/out/\n.superpowers/' >> .gitignore
```

- [ ] **Step 3: Test static export build**

Run: `cd web && npm run build`

Expected: Build succeeds, outputs to `web/out/`. If it fails:
- Add `'use client'` to any page using hooks
- Wrap `useSearchParams()` in `<Suspense>`
- Remove any `headers()` or `cookies()` calls

This is a **gate** — do not proceed until build passes.

- [ ] **Step 4: Verify output**

```bash
ls web/out/
```

Expected: `index.html`, `auth.html`, `history.html`, `_next/` directory.

- [ ] **Step 5: Commit**

```bash
git add web/next.config.ts .gitignore
git commit -m "feat: configure Next.js static export for Railway"
```

---

## Task 8: Backend Hardening

**Files:**
- Modify: `api/main.py`
- Modify: `api/database.py`
- Modify: `web/lib/api.ts`

- [ ] **Step 1: Update quota defaults in database.py**

```python
# Change constants (line 26-27):
DEFAULT_TEXT_QUOTA = 5
DEFAULT_VOICE_QUOTA = 2

# Also update SQL CREATE TABLE defaults (lines 51-52):
# text_quota INTEGER NOT NULL DEFAULT 5,
# voice_quota INTEGER NOT NULL DEFAULT 2,
```

- [ ] **Step 2: Add relevance floor to api/main.py**

Add env-configurable constant near the top:

```python
MIN_RELEVANCE_SCORE = float(os.getenv("MIN_RELEVANCE_SCORE", "0.50"))
```

In both `query_stream()` event generator and `query()` handler, after FAISS search and before Claude call, filter results:

```python
relevant_results = [r for r in raw_results if r.get("similarity", 0) >= MIN_RELEVANCE_SCORE]
if not relevant_results:
    # For streaming:
    yield f"data: {json_module.dumps({'type': 'no_match', 'message': 'I could not find a direct teaching on this topic. Try rephrasing with specific scripture terms.'})}\n\n"
    yield f"data: {json_module.dumps({'type': 'done'})}\n\n"
    return
    # For POST: return QueryResponse with ai_answer=None and a message field
```

Important: Do NOT decrement quota for no-match responses.

- [ ] **Step 3: Move audio cache to persistent volume**

In `api/main.py`, change line 64:

```python
# From:
AUDIO_CACHE_DIR = PROJECT_ROOT / "api" / "audio_cache"
# To:
AUDIO_CACHE_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data_local"))) / "audio_cache"
```

Keep the `mkdir` on the next line — it handles directory creation.

- [ ] **Step 4: Remove dead code**

Remove `optional_auth` from the import on line 47:

```python
# From:
from api.middleware import get_current_user, optional_auth
# To:
from api.middleware import get_current_user
```

- [ ] **Step 5: Update CORS defaults**

Add `localhost:8000` to the default origins (line 90):

```python
_default_origins = "http://localhost:3000,http://localhost:3001,http://localhost:8000"
```

- [ ] **Step 6: Add no_match handler to web/lib/api.ts**

In the `queryStream` function's SSE event parser, add a new case:

```typescript
case 'no_match':
  callbacks.onNoMatch?.(parsed.message);
  break;
```

Update the `QueryStreamCallbacks` interface to include `onNoMatch?: (message: string) => void`.

- [ ] **Step 7: Lock top_k to 5 in web/lib/api.ts**

Remove the `topK` parameter from `queryStream()` and hard-code it to `5`:

```typescript
// From:
export function queryStream(question: string, topK: number = 5, ...)
// To:
export function queryStream(question: string, callbacks: ...)
```

And in the URLSearchParams:
```typescript
const params = new URLSearchParams({
  question: question.trim(),
  top_k: '5',  // locked — do not expose to callers
});
```

Update all callsites to remove the `topK` argument.

- [ ] **Step 8: Commit**

```bash
git add api/main.py api/database.py web/lib/api.ts
git commit -m "feat: relevance floor, audio persistence, quota 5+2, no_match handler"
```

---

## Task 9: FastAPI Static Serving

**Files:**
- Modify: `api/main.py`

- [ ] **Step 1: Add static file mount**

Add at the VERY END of `api/main.py`, after all route definitions:

```python
from fastapi.staticfiles import StaticFiles

# Serve frontend static files (must be LAST — catches all non-API routes)
_frontend_dir = PROJECT_ROOT / "web" / "out"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
    logger.info("Serving frontend from %s", _frontend_dir)
```

- [ ] **Step 2: Test locally**

Build frontend and serve from FastAPI:

```bash
cd web && npm run build && cd ..
uvicorn api.main:app --port 8000
```

Open `http://localhost:8000` — should see the auth page.
Open `http://localhost:8000/auth` — should serve `auth.html`.
Open `http://localhost:8000/api/health` — should return JSON (API still works).

- [ ] **Step 3: Commit**

```bash
git add api/main.py
git commit -m "feat: FastAPI serves static frontend from web/out/"
```

---

## Task 10: Docker + Railway Config

**Files:**
- Modify: `Dockerfile`
- Create: `.dockerignore`
- Modify: `railway.toml`
- Create: `.env.example`

- [ ] **Step 1: Write .dockerignore**

```
embeddings/
embeddings_optimized/
logs/
.env
.env.*
web/node_modules/
web/.next/
web/out/
.superpowers/
*.log
*.md
!README.md
tests/
__pycache__/
.git/
```

- [ ] **Step 2: Write multi-stage Dockerfile**

See spec section 4.3 for the complete Dockerfile. Key points:
- Stage 1: `node:20-slim` builds frontend (`npm ci` + `npm run build`)
- Stage 2: `python:3.11-slim` runs everything
- COPY faiss_indexes/ (baked in, ~1.1GB)
- COPY --from=frontend the built `web/out/`
- Single worker: `--workers 1`

- [ ] **Step 3: Update railway.toml**

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

- [ ] **Step 4: Create .env.example**

```
# Required
VOYAGE_API_KEY=
ANTHROPIC_API_KEY=
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=NkwRXQbcKij4CMmXWWt5
JWT_SECRET=
GOOGLE_CLIENT_ID=

# Railway
DATA_DIR=/data
ALLOWED_ORIGINS=https://your-app.up.railway.app

# Optional
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW_SECS=60
MIN_RELEVANCE_SCORE=0.50
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

- [ ] **Step 5: Test Docker build locally (optional)**

```bash
docker build -t prabhupada-ai .
```

Expected: Build completes (may take 5-10 min due to FAISS index COPY).

- [ ] **Step 6: Commit**

```bash
git add Dockerfile .dockerignore railway.toml .env.example
git commit -m "feat: Docker multi-stage build + Railway config + env example"
```

---

## Task 11: Railway Deployment

**Files:** None (Railway dashboard + CLI)

- [ ] **Step 1: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 2: Create Railway service**

On Railway dashboard:
1. New project → Deploy from GitHub repo
2. Select `ai-prabhupada-rag` repo
3. Railway auto-detects Dockerfile

- [ ] **Step 3: Set environment variables**

Set all variables from `.env.example` on the Railway dashboard. Generate a random 64-char `JWT_SECRET`:

```bash
openssl rand -hex 32
```

- [ ] **Step 4: Create persistent volume**

On Railway service settings:
1. Add volume → Mount path: `/data`
2. Verify `DATA_DIR=/data` is set in env vars

- [ ] **Step 5: Deploy and verify**

Wait for build + deploy. Then check:
- `https://<app>.up.railway.app/api/health` → 200, `faiss_loaded: true`
- `https://<app>.up.railway.app/` → Auth page renders
- `https://<app>.up.railway.app/auth` → Sign-in works

---

## Task 12: Post-Deploy Verification

- [ ] **Step 1: Mobile viewport test**

Open on phone (or Chrome DevTools 375px):
- Auth screen: readable, 44px buttons
- Main page: input usable, pills tappable
- Answer: text readable, audio player bar
- History: cards display correctly

- [ ] **Step 2: Full flow test**

1. Sign in with Google
2. Ask a question → verify streaming answer
3. Check Sources tab → relevance scores displayed
4. Try voice toggle → audio plays
5. Use ShareBar → copy works, tweet opens x.com
6. Ask 5 text questions → verify SubscribeGate appears on 6th
7. Submit email on SubscribeGate → verify "We'll notify you"

- [ ] **Step 3: Edge case test**

- Low-relevance query (e.g., "What is the weather in Tokyo?") → should show "no match" message
- Refresh page → quota persists (server-side, not localStorage)
- Check `railway logs` for any errors or OOM warnings

- [ ] **Step 4: Verify audio persistence**

Ask a voice question, note the audio_id. Then trigger a Railway redeploy. After redeploy, check if the audio file still exists at the same URL.

---

## Task 13: Code Review

- [ ] **Step 1: Dispatch code review agent**

Use `superpowers:requesting-code-review` with the review context from spec section 8.3. Include all critical checks (auth, quota, XSS, CORS, static serving, Docker, memory), answer quality checks (relevance floor, voice quota, audio persistence, semantic cache), and informational checks (dead code, console.logs, touch targets).

- [ ] **Step 2: Fix any issues found**

Address critical and important findings. Informational items at discretion.

- [ ] **Step 3: Final commit + push**

```bash
git push origin main
```

Railway auto-redeploys on push.
