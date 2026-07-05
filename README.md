# AI Career Navigator System

> Final Year Project — Bachelor of Computer Science (Artificial Intelligence)
> Universiti Teknikal Malaysia Melaka (UTeM) | BAXI Programme | 2025/2026

An AI-powered career guidance platform that analyses resumes, identifies skill gaps, predicts career paths, and generates personalised learning roadmaps backed by real YouTube resources.

---

## Overview

The AI Career Navigator System helps IT professionals and students understand their career readiness by comparing their skills against 29,254 real LinkedIn job postings across 11 IT role categories.

### Core Modules

| Module | Description |
|--------|-------------|
| **Resume Skill Extraction** | 4-layer hybrid NLP pipeline (Dictionary + spaCy NER + TF-IDF + Pattern Detection) |
| **Skill Gap Analysis** | Hybrid scoring (60% weighted coverage + 40% cosine similarity) against 11 IT roles |
| **Career Prediction** | Random Forest classifier — 86.48% accuracy across 11 role categories |
| **Roadmap Generator** | Content-based filtering with YouTube API integration and MongoDB caching |
| **Progress Dashboard** | JWT authentication, skill evolution tracking, and persistent analysis history |

---

## Tech Stack

### Backend
- **Framework:** Flask (Python)
- **Database:** MongoDB (PyMongo)
- **ML:** scikit-learn (Random Forest, KNN, TF-IDF), spaCy
- **Auth:** Flask-JWT-Extended, bcrypt
- **APIs:** YouTube Data API v3

### Frontend
- **Framework:** React + Vite
- **Styling:** Tailwind CSS v4
- **HTTP Client:** Axios

### ML Models
- TF-IDF Vectorizer (5,000 features, bigrams)
- Random Forest Classifier (100 trees, balanced class weights)
- K-Nearest Neighbors (k=5, euclidean distance)
- Cosine Similarity (via scikit-learn)

### Dataset
- 29,254 LinkedIn IT job postings
- 11 clean role categories (QA Engineer removed — data contamination)
- Domain blocklist applied (100+ non-skills filtered)

---

## Project Structure

```
ai-career-navigator/
├── backend/
│   ├── app/
│   │   ├── models/          # User, dashboard, resume models
│   │   ├── routes/          # Flask blueprints (auth, gap, predict, roadmap, dashboard)
│   │   ├── services/        # Core ML services
│   │   └── utils/           # DB helper, response helper
│   ├── ml/
│   │   ├── training/        # Preprocessing + training scripts
│   │   └── saved_models/    # Trained .pkl files (gitignored)
│   ├── data/
│   │   ├── raw/             # Raw LinkedIn dataset (gitignored)
│   │   └── processed/       # Cleaned data + skill corpus (gitignored)
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── src/
    │   ├── components/      # UI components + layout
    │   ├── context/         # AuthContext, FlowContext
    │   ├── lib/             # Central API client
    │   └── pages/           # 8 application pages
    ├── package.json
    └── vite.config.js
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Sign in, get JWT |
| GET | `/api/auth/me` | Current user (protected) |
| POST | `/api/resume/upload` | Upload PDF/DOCX resume |
| POST | `/api/gap/analyze` | Top 5 role matches |
| POST | `/api/gap/analyze/<role>` | Deep dive for one role |
| GET | `/api/gap/roles` | List 11 available roles |
| POST | `/api/predict/career` | Career role prediction |
| POST | `/api/roadmap/generate` | Generate learning roadmap |
| POST | `/api/dashboard/analyses` | Save analysis snapshot |
| GET | `/api/dashboard/stats` | Dashboard overview |
| POST | `/api/dashboard/progress` | Mark skill learned/learning |

---

## Local Setup

### Prerequisites

- Python 3.10+
- Node.js v20+
- MongoDB Community Server (running on port 27017)
- YouTube Data API v3 key (Google Cloud Console)

---

### 1. Clone the Repository

```bash
git clone https://github.com/ZayedDevs/ai-career-navigator.git
cd ai-career-navigator
```

---

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm
```

#### Configure Environment Variables

Create `backend/.env`:

```env
FLASK_DEBUG=true
MONGO_URI=mongodb://localhost:27017/career_navigator_db
YOUTUBE_API_KEY=your_youtube_api_key_here
YOUTUBE_RESULTS_PER_SKILL=3
YOUTUBE_CACHE_DAYS=7
JWT_SECRET_KEY=your_long_random_secret_here
JWT_ACCESS_TOKEN_HOURS=24
```

---

### 3. Prepare the ML Models

The trained model files are not included in this repository (too large). You have two options:

#### Option A — Train from Scratch (requires the LinkedIn dataset)

Place the raw data files in `backend/data/raw/`:
- `linkedin_job_postings.csv`
- `job_skills.csv`

Then run in order:

```bash
cd backend
python ml/training/preprocess_data.py
python ml/training/build_skill_db.py
python ml/training/train_models.py
```

This takes approximately 2–3 minutes.

#### Option B — Use Pre-trained Models

Contact the author to obtain the pre-trained `.pkl` files and place them in `backend/ml/saved_models/`.

---

### 4. Start the Backend

```bash
cd backend
python run.py
```

Backend runs at: `http://localhost:5000`

---

### 5. Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:5000
```

Start the development server:

```bash
npm run dev
```

Frontend runs at: `http://localhost:5173`

---

### 6. Verify Everything Works

With both servers running, open `http://localhost:5173` in your browser. The health indicator on the homepage should show **"API connected"** in green.

---

## User Flow

```
Register / Login
      ↓
Upload Resume (PDF or DOCX)
      ↓
Review Extracted Skills (editable)
      ↓
Skill Gap Analysis → Top 5 role matches
      ↓
Click a Role → Deep dive with missing skills
      ↓
Generate Roadmap → 3-phase learning plan + YouTube resources
      ↓
Mark skills as Learned → Skill profile evolves
      ↓
Dashboard → Track progress across sessions
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Removed QA Engineer category | LinkedIn data contaminated with manufacturing test engineers |
| Hybrid scoring (60/40) | Pure cosine penalises diverse profiles; coverage adds interpretability |
| KNN as readiness score (not classifier) | Dataset skewed Senior/Mid; reframed as similarity percentage |
| Domain blocklist (100+ terms) | "Data science" and "computer science" are fields, not learnable skills |
| MySQL → SQL alias | SQL dialects indicate SQL competency; avoids false negatives in gap analysis |
| YouTube API + MongoDB cache | 7-day TTL cache gives 350× speedup on repeat queries |
| JWT (24h, no refresh) | Appropriate scope for academic project; refresh tokens out of scope |

---

## Known Limitations

- ML models trained on 2023–2024 LinkedIn data — industry skill demands evolve
- Roadmap progress percentage may exceed 100% in edge cases (known bug, backlog)
- YouTube resources are general tutorials, not curated course paths
- No password reset or email verification (out of scope for FYP)

---

## Future Work

- Integrate Kaggle Udemy/Coursera datasets for paid course recommendations
- Add multi-language resume support
- Re-train models periodically with fresh LinkedIn data
- Implement password reset flow
- Deploy to cloud (AWS / Railway / Render)

---

## Author

**Zayed Khaled Habeb Alkhulaqi**
Bachelor of Computer Science (Artificial Intelligence) — BAXI Programme
Universiti Teknikal Malaysia Melaka (UTeM)
Matric: B032310764

Supervisor: Puan Nur Diana Izzani Binti Masdzarif

---

## Acknowledgements

- LinkedIn job postings dataset (via Kaggle)
- YouTube Data API v3 (Google)
- scikit-learn, spaCy, Flask, React open-source communities
