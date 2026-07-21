# 🚗 AutoWorth AI

> **AI-Powered Vehicle Valuation Platform for India**
>
> Accurate, transparent, and explainable used car pricing — powered by Machine Learning, Computer Vision, and Explainable AI.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-000000?style=flat&logo=next.js)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1?style=flat&logo=postgresql)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-Strict-3178C6?style=flat&logo=typescript)](https://www.typescriptlang.org/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Database](#database)
- [Development](#development)

---

## Overview

AutoWorth AI provides:

- **ML-powered price prediction** (XGBoost, Random Forest, Linear Regression, Decision Tree)
- **Computer Vision analysis** (YOLO-based damage detection, severity estimation, heatmaps)
- **Explainable AI** (SHAP feature contributions per prediction)
- **Professional PDF valuation reports** (WeasyPrint, QR codes)
- **Role-based access** (Guest / Registered User / Admin)
- **Admin portal** (dataset management, model training, versioning, analytics)

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, React Hook Form, Zod, Framer Motion |
| **Backend** | FastAPI, SQLAlchemy (Async), Alembic, Pydantic v2, pydantic-settings |
| **Auth** | JWT (python-jose), bcrypt, Google OAuth |
| **ML** | Scikit-learn, XGBoost, SHAP, Optuna, Joblib |
| **CV** | YOLO (Ultralytics), OpenCV, PyTorch |
| **Database** | PostgreSQL (asyncpg driver) |
| **Storage** | Cloudinary (images + heatmaps) |
| **PDF** | WeasyPrint |
| **Deployment** | Vercel (Frontend), Railway (Backend + DB) |
| **CI/CD** | GitHub Actions |

---

## Architecture

```
Users
  │
  ▼
Next.js Frontend (Vercel)
  │ HTTPS REST API
  ▼
FastAPI Backend (Railway)
  │
  ├── API Layer          (/api/v1/*)
  ├── Business Logic     (services/)
  ├── ML/CV Pipelines    (ml/)
  ├── Repository Layer   (repositories/)
  └── Database           (PostgreSQL via SQLAlchemy)
        │
        └── Cloudinary (image/heatmap storage)
```

**Layered Backend:**
```
Presentation → API Layer → Business Logic → ML Layer → Repository → Database
```

---

## Project Structure

```
autoworth-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # Route handlers (thin controllers)
│   │   ├── core/               # Config, DB session, security utils
│   │   ├── models/             # SQLAlchemy ORM entities
│   │   ├── schemas/            # Pydantic v2 validation schemas
│   │   ├── repositories/       # Data access layer
│   │   ├── services/           # Business logic layer
│   │   └── ml/                 # ML training, inference & CV pipelines
│   ├── alembic/                # Database migrations
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js App Router pages
│   │   ├── components/         # Reusable UI components
│   │   ├── lib/                # API client, utilities
│   │   ├── providers/          # React context providers
│   │   └── types/              # TypeScript type definitions
│   └── package.json
│
└── Docs/                       # PRD, TRD, DB Schema, SOT
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials and secrets

# Run database migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local with your API URL

# Start development server
npm run dev
```

Frontend available at: `http://localhost:3000`

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL async connection string |
| `SECRET_KEY` | JWT signing secret (32+ chars) |
| `ALGORITHM` | JWT algorithm (`HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `SMTP_HOST` | Email server host |
| `SMTP_PORT` | Email server port |
| `SMTP_USER` | Email username |
| `SMTP_PASSWORD` | Email password |
| `FRONTEND_URL` | Frontend base URL (CORS) |
| `ENVIRONMENT` | `development` / `production` |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth client ID |

---

## Database

AutoWorth AI uses **PostgreSQL** exclusively. The schema includes 20+ tables:

**Core:** `roles`, `users`, `user_sessions`

**Vehicle Catalog:** `brands`, `car_models`, `variants`, `cities`, `vehicles`

**Predictions:** `predictions`, `prediction_images`, `shap_results`, `recommendations`

**ML:** `ml_models`, `model_versions`, `datasets`

**User Activity:** `favorites`, `feedback`, `activity_logs`, `error_logs`, `notification_logs`

Run migrations:
```bash
alembic upgrade head
```

---

## Development

### Run Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Type Checking
```bash
# Backend
mypy app/

# Frontend
npx tsc --noEmit
```

### Linting
```bash
# Backend
ruff check app/

# Frontend
npm run lint
```

---

## Deployment

- **Frontend**: Deploy `frontend/` to Vercel
- **Backend**: Deploy `backend/` to Railway
- **Database**: Railway PostgreSQL plugin
- **CI/CD**: GitHub Actions (`.github/workflows/deploy.yml`)

---

## License

This project is built for academic and portfolio purposes.
