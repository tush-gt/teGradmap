# GradMap: AI-Powered Engineering Counselling Platform

GradMap is a sophisticated data intelligence platform designed to navigate the complexities of the Maharashtra Engineering (MHT-CET) admission process. By leveraging historical CAP cutoff datasets from 2022–2025, the system provides students with data-driven, explainable recommendations and admission simulations.

---

## 🚀 Key Features

- **Intelligence-Driven Recommendations**: Personalized college and branch suggestions based on user percentile and category.
- **Explainable Bucketing**: Classification of results into **SAFE**, **TARGET**, and **AMBITIOUS** segments to manage admission expectations.
- **Multi-Year Data Normalization**: Unified data pipeline processing over 230,000 records from multiple years and admission rounds.
- **Advanced Feature Engineering**: Derived metrics including `institute_tier`, `recommendation_score`, and `branch_family` groupings.
- **CAP Round Simulation**: Heuristic modelling of admission trends across CAP rounds (Early, Mid, and Late stages).
- **High-Fidelity UI**: Modern React-based interface for interactive counselling exploration.

---

## 🛠️ Tech Stack

### Backend
- **Core**: Python 3.10+
- **Data Engine**: Pandas, NumPy
- **API Layer**: FastAPI (Uvicorn)
- **Architecture**: Modular, service-oriented design

### Frontend
- **Framework**: React 18+
- **Build Tool**: Vite
- **Styling**: Vanilla CSS / Tailwind CSS
- **State Management**: React Hooks / Context API

---

## 🧠 Recommendation System Overview

The GradMap engine employs a deterministic, multi-stage pipeline to ensure high-confidence results:

### 1. The Recommendation Buckets
- **SAFE (Gap ≥ 2.0)**: Institutes where the student's percentile is comfortably above historical cutoffs.
- **TARGET (-1.0 ≤ Gap < 2.0)**: Highly realistic options where cutoffs align closely with the student's score.
- **AMBITIOUS (Gap < -1.0)**: "Dream" institutes that represent a significant reach but remain statistically possible.

### 2. Recommendation Scoring
The `recommendation_score` is a transparent, weighted metric calculated as:
`((percentile_cutoff / 100) * 50) + tier_weight + branch_family_weight + recency_bonus`
This ensures that prestigious institutes and modern branches (like AI/ML) are appropriately prioritized in the ranking logic.

---

## 🏗️ Modular Architecture

The project is structured as a monorepo to maintain strict separation between data intelligence and presentation layers.

### Folder Structure
```text
GradMap/
├── frontend/               # React + Vite application
│   ├── src/                # Component architecture and hooks
│   └── vite.config.js      # Build configuration
│
├── backend/                # Data pipeline and API
│   ├── api/                # FastAPI routers and endpoints
│   ├── scripts/            # Core ETL and normalization logic
│   ├── modeling/           # Modular recommendation engine
│   ├── configs/            # Canonical maps (colleges, branches)
│   └── requirements.txt    # Backend dependencies
│
├── README.md               # Documentation
└── .gitignore              # Version control exclusions
```

---

## 📊 Data Pipeline & Feature Engineering

The system processes raw PDF cutoff lists through a production-grade ETL (Extract, Transform, Load) pipeline:

1. **Normalization**: Canonical mapping of over 300 institutes and 50+ branch variations.
2. **Quality Audit**: Automated isolation of corrupted rows and unknown branch artifacts into quarantine zones.
3. **Feature Synthesis**:
   - **`branch_family`**: Grouping fragmented branches (e.g., CS, IT, AI&DS) into functional families.
   - **`institute_tier`**: Heuristic tiering of Maharashtra's 300+ engineering colleges.
   - **`round_type`**: Temporal classification of admission stages (Early/Mid/Late).

---

## 🏁 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend Setup
1. Navigate to `/backend`
2. Create virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Run scripts or API: `python main.py`

### Frontend Setup
1. Navigate to `/frontend`
2. Install dependencies: `npm install`
3. Start dev server: `npm run dev`

---

## 🗺️ Roadmap

- [ ] **XGBoost Integration**: Implementation of Gradient Boosted Decision Trees for refined ranking probability.
- [ ] **Trend Forecasting**: Time-series analysis to predict upcoming year cutoff fluctuations.
- [ ] **Personalized Counselling Intelligence**: LLM-powered assistant for explainable admission guidance.
- [ ] **Hybrid Recommender**: Combining collaborative filtering with current content-based logic.
- [ ] **Live CAP Simulation**: Real-time mock-allotment logic based on current year seat matrices.

---

## ⚖️ License
Internal GradMap Development — All Rights Reserved.
