# AI Career Navigator — Progress

## Status: Frontend complete, both servers stable

---

## What's built

### Backend (pre-existing, Flask + MongoDB)
All routes tested and working:
- `POST /api/auth/register` · `POST /api/auth/login` · `GET /api/auth/me`
- `POST /api/resume/upload` (PDF / DOCX, max 10 MB)
- `POST /api/gap/analyze` · `POST /api/gap/analyze/<role>` · `GET /api/gap/roles`
- `POST /api/predict/career` · `GET /api/predict/roles`
- `POST /api/roadmap/generate` (YouTube resources via Google API)
- `POST|GET /api/dashboard/analyses` · `DELETE /api/dashboard/analyses/<id>`
- `POST|GET /api/dashboard/roadmaps` · `GET /api/dashboard/roadmaps/active`
- `POST|GET /api/dashboard/progress` · `DELETE /api/dashboard/progress/<skill>`
- `GET /api/dashboard/stats`
- `GET /api/health`

### Frontend (`frontend/`) — React 19 + Vite 8 + Tailwind v4

**Foundation**
- `src/lib/api.js` — central axios client; auto-attaches JWT, redirects to `/login` on 401
- `src/context/AuthContext.jsx` — `{ user, token, login, logout, register }`; hydrates from `localStorage` on mount
- `src/context/FlowContext.jsx` — session state carrying `skills → gap → predict → roadmap` without re-uploading
- `src/components/ProtectedRoute.jsx` — redirects unauthenticated users to `/login`
- `.env` — `VITE_API_BASE_URL=http://localhost:5000`

**Shared UI components** (`src/components/ui/`)
- `Button` — variant: primary / secondary / danger / outline; `loading` prop shows inline spinner
- `Card` — consistent padded container
- `Input` — labelled with error state
- `Spinner` — sm / md / lg sizes
- `SkillTag` — pill badge; `removable` prop for editable lists
- `ProgressBar` — colour-coded (green ≥ 70 / yellow ≥ 40 / red < 40); capped at 100%

**Layout** (`src/components/layout/`)
- `Navbar` — auth-aware: name + logout when signed in; Login / Register when not
- `Layout` — wraps all pages via React Router `<Outlet />`

**Pages** (`src/pages/`)
| Route | Page | Key features |
|---|---|---|
| `/` | Home | Hero, API health dot, 4 how-it-works cards, 11 roles |
| `/login` | Login | Email + password form, error display |
| `/register` | Register | Name + email + password, client-side length check |
| `/upload` | Upload | Drag-drop + file picker, editable extracted skill list (add / remove tags) |
| `/gap` | Gap | Overall readiness %, top-5 role cards, click-to-deep-dive, frequency bars for missing skills |
| `/predict` | Predict | Primary prediction card, top-K list, all-11-role bar chart |
| `/roadmap` | Roadmap | 3-phase cards (Foundation / Intermediate / Advanced), priority colours, YouTube resource cards with thumbnails, mark-learned per skill, save to dashboard |
| `/dashboard` | Dashboard | Stats row, roadmap progress bar, latest analysis card, full analyses list with delete + resume session |

---

## Bug fixes applied during build

| File | Fix |
|---|---|
| `backend/app/services/roadmap_generator.py` line 126 | Replaced `⚠️` emoji in `print()` — was throwing `UnicodeEncodeError` on Windows cp1252, crashing the request and eventually the process |
| `backend/run.py` | Added `use_reloader=False` — Flask's stat reloader segfaults Python 3.14 on Windows |

---

## Known issues / backlog

| Issue | Detail |
|---|---|
| YouTube SSL errors (intermittent) | `ssl.SSLError: WRONG_VERSION_NUMBER` from httplib2 on Python 3.14 + Windows. YouTube fetch fails silently; roadmap renders with empty resources. Possible causes: TLS mismatch, antivirus HTTPS inspection, or httplib2 incompatibility with Python 3.14. |
| `roadmap_progress.percent_complete` can exceed 100% | Backend counts all "learned" skills globally against the roadmap's skill count — can inflate past 100%. Frontend already clamps display to 100%. Backend fix is on backlog. |
| Duplicate API calls in React StrictMode | Dev server (StrictMode) double-invokes `useEffect`, causing paired OPTIONS + GET/POST calls in backend logs. Normal in development; disappears in production build. |

---

## How to run

```bash
# Terminal 1 — backend
cd backend
python run.py
# Serves at http://localhost:5000

# Terminal 2 — frontend
cd frontend
npm run dev
# Serves at http://localhost:5173
```

> **Note:** The YouTube API key is configured in `backend/.env`. If SSL errors persist, set `include_resources: false` in roadmap requests or investigate httplib2 vs Python 3.14 TLS compatibility.
