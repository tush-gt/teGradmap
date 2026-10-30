# 🎓 GradMap — AI-Powered MHT-CET Engineering Counselling Platform

> **Data-driven. ML-grounded. Gemini-powered.**  
> GradMap helps Maharashtra engineering aspirants navigate the CAP admission process with intelligent college recommendations, cutoff trend analysis, CAP round simulation, and a conversational AI counsellor.

---

## ✨ What's New in v2.0

- 🤖 **Google Gemini AI Counsellor** — Conversational admission guidance grounded in real ML data
- 🌲 **Scikit-learn Random Forest** — Genuine admission probability per college & branch  
- 📊 **Cutoff Trend Analytics** — Multi-year historical charts (2022–2025)
- 🧪 **CAP Round Simulator** — Deterministic seat allotment simulation  
- 🎯 **DnD Option Form Builder** — Drag-and-drop option form with preference ordering

---

## 🚀 Key Features

| Feature | Description |
|---|---|
| **Personalized Recommendations** | SAFE / TARGET / AMBITIOUS college suggestions based on percentile & category |
| **ML Probability Scoring** | Random Forest model predicts admission probability per seat |
| **AI Counsellor (Gemini)** | Multi-turn conversational assistant grounded in real cutoff data |
| **Cutoff Trend Charts** | Per-college, per-branch historical cutoff trends across 4 years |
| **CAP Round Simulation** | Simulate Round 1, 2, or 3 seat allotment using real historical data |
| **Option Form Builder** | Drag-and-drop interface to build & reorder your CAP preference list |
| **College Analytics** | Branch-wise cutoff comparison, volatility index, trend direction |
| **230k+ Record Dataset** | Normalized cutoff data across 300+ colleges, 50+ branches, 2022–2025 |

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| API Framework | FastAPI + Uvicorn |
| Data Processing | Pandas, NumPy |
| ML Model | Scikit-learn (Random Forest Classifier) |
| AI Integration | Google Gemini (`google-genai` SDK, Free Tier) |
| Serialization | Pydantic v2 |
| Model Persistence | Joblib |
| Environment | python-dotenv |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React 19 + Vite 8 |
| Routing | React Router v7 |
| Styling | Tailwind CSS v4 |
| State Management | Zustand |
| Data Visualization | Recharts |
| Animations | Framer Motion |
| Drag & Drop | @dnd-kit |
| HTTP Client | Axios |
| Markdown Rendering | react-markdown |

---

## 🏗️ Project Structure

```text
teGradmap/
├── frontend/                         # React + Vite SPA
│   ├── src/
│   │   ├── components/               # Reusable UI components
│   │   ├── pages/                    # Route-level page components
│   │   ├── hooks/                    # Custom React hooks
│   │   └── store/                    # Zustand state management
│   ├── package.json
│   └── vite.config.js
│
├── backend/                          # Python FastAPI backend
│   ├── api/
│   │   ├── main.py                   # FastAPI app, CORS, all HTTP routes
│   │   ├── ai_routes.py              # Gemini AI counsellor endpoints (/ai/*)
│   │   ├── ai_counsellor.py          # Gemini client, context builder, retry logic
│   │   ├── schemas.py                # Pydantic request/response models
│   │   └── test_gemini.py            # Gemini API connection tester
│   │
│   ├── scripts/
│   │   └── modeling/
│   │       ├── recommendation_engine.py  # Core recommend() orchestrator
│   │       ├── filters.py                # Category, branch, tier, window filters
│   │       ├── bucket_logic.py           # Percentile gap & SAFE/TARGET/AMBITIOUS logic
│   │       ├── scoring.py                # Recency bonus and scoring
│   │       ├── ranking.py                # Dedup, sort, format output
│   │       ├── utils.py                  # Dataset loader & input validator
│   │       └── config.py                 # Feature columns, constants
│   │
│   ├── models/
│   │   ├── trained/
│   │   │   └── admission_rfc_model.pkl   # Trained Random Forest pipeline (joblib)
│   │   └── utils/
│   │       ├── model_loader.py           # Load/cache RFC model, predict_probability()
│   │       └── probability_ranker.py     # Buckets, confidence labels, diversification
│   │
│   ├── configs/                          # Canonical college & branch maps
│   ├── .env                              # GEMINI_API_KEY & GEMINI_MODEL (gitignored)
│   └── requirements.txt
│
└── README.md
```

---

## 🧠 Recommendation & ML Pipeline

The core engine runs a **12-step deterministic + ML-hybrid pipeline**:

```
Input (percentile, category, branch_family)
     ↓
1. Validate Input
2. Load 230k-row Dataset (cached in memory)
3. Filter by Category (GOPEN, GOBC, GSC, …)
4. Filter by Branch Family (CS_FAMILY, MECH_FAMILY, …)
5. Filter by Tier Preference (optional)
6. Percentile Window Filter (±configurable margin)
7. Compute Percentile Gap = user_percentile − cutoff_percentile
8. Assign Buckets:
     Gap ≥  2.0  → SAFE
    -1.0 ≤ Gap < 2.0 → TARGET
     Gap < -1.0  → AMBITIOUS
9. Apply Year Recency Scoring
10. Deduplicate (latest/highest-scoring row per branch per college)
11. ML Inference — Random Forest predicts P(admission) per row
12. Attach probability metadata, rank, diversify (max 2 branches/college)
     ↓
Output: {SAFE: [...], TARGET: [...], AMBITIOUS: [...]}
```

### Probability Buckets (from ML)
| ML Probability | Label | Meaning |
|---|---|---|
| ≥ 70% | SAFE | Very high admission certainty |
| 45–70% | TARGET | Competitive; strong if well-sequenced |
| < 45% | AMBITIOUS | Dream college; low but possible |

### Confidence Labels
`VERY_HIGH (≥95%)` → `HIGH (≥80%)` → `MODERATE (≥60%)` → `LOW (≥40%)` → `VERY_LOW (<40%)`

---

## 🤖 AI Counsellor (Gemini)

The AI Counsellor (`/ai/chat`) uses **Google Gemini Free Tier** with:

- **Factual grounding**: Every response is anchored to live ML recommendations + historical cutoff data
- **Multi-turn context**: Last 4 conversation turns are passed as structured history  
- **Exponential backoff**: Auto-retries on HTTP 503 (High Demand) and 429 (Rate Limit)
- **Dynamic suggestions**: Context-aware follow-up question suggestions  
- **CAP strategy awareness**: Knows Freeze/Float/Slide rules and option form ordering strategy

### AI API Endpoints
| Endpoint | Method | Description |
|---|---|---|
| `/ai/chat` | POST | Multi-turn counselling chat with ML grounding |
| `/ai/status` | GET | Check Gemini + ML model readiness |
| `/ai/suggested` | GET | Get personalized suggested questions |
| `/ai/reload-env` | POST | Hot-reload `.env` without restarting server |

---

## 📡 Backend API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check + dataset status |
| `/recommend` | POST | Get SAFE/TARGET/AMBITIOUS recommendations |
| `/trends` | GET | Multi-year cutoff trends for college+branch |
| `/analytics/college` | GET | Branch-wise analytics for a college |
| `/colleges` | GET | List all colleges with metadata |
| `/simulate` | POST | CAP Round allotment simulation |

---

## 🏁 Getting Started

### Prerequisites
- Python **3.10+**
- Node.js **18+**
- A free **Gemini API key** from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Clone & Setup Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure Gemini API Key

Edit `backend/.env`:
```env
GEMINI_API_KEY=AIzaSyYourActualKeyHere
GEMINI_MODEL=gemini-2.0-flash
```

### 3. Start the Backend Server

```bash
# From the backend/ directory:
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive API docs: `http://localhost:8000/docs`

### 4. Setup & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

---

## 🗂️ Data & Feature Engineering

The system processes raw PDF cutoff lists from Maharashtra CET Cell through a production-grade ETL pipeline:

1. **Extraction**: PDF → structured CSV per year and round
2. **Normalization**: Canonical mapping of 300+ institute names and 50+ branch variations
3. **Quality Audit**: Automated quarantine of corrupted or unrecognized rows
4. **Feature Synthesis**:
   - `branch_family` — Groups CS, IT, AI&DS, Data Science → `CS_FAMILY`
   - `institute_tier` — Heuristic tier 1/2/3 for Maharashtra's engineering colleges
   - `round_type` — Early / Mid / Late admission stage classification
   - `recommendation_score` — Weighted metric: `((cutoff/100)*50) + tier_weight + branch_weight + recency_bonus`
5. **ML Training**: Random Forest Classifier trained on engineered features to predict admission probability

---

## 🗺️ Roadmap

- [x] Recommendation engine with SAFE/TARGET/AMBITIOUS bucketing  
- [x] Random Forest ML probability scoring  
- [x] Google Gemini AI Counsellor integration  
- [x] Multi-year cutoff trend charts  
- [x] CAP Round Simulator  
- [x] Drag-and-drop Option Form Builder  
- [ ] XGBoost / LightGBM upgrade for refined probability estimation  
- [ ] Time-series cutoff trend forecasting  
- [ ] Collaborative filtering hybrid recommender  
- [ ] Live CAP seat matrix integration  
- [ ] PWA support for mobile access  

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Google AI Studio API key |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model to use |

---

## ⚖️ License

Internal GradMap Development — All Rights Reserved.
