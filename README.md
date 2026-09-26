# InsightBoard

A full-stack CSV data exploration tool built with **Django REST Framework** (backend) and **Vue 3** (frontend).

Upload any CSV file, then explore it with an interactive data table (filter, sort, paginate) and Chart.js visualisations (Bar, Line, Doughnut).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Django 6 + Django REST Framework |
| CSV Processing | pandas |
| Frontend | Vue 3 (Composition API) + Vite |
| Charts | Chart.js + vue-chartjs |
| HTTP Client | Axios |
| Routing | Vue Router 4 |
| Backend Tests | Django TestCase + DRF APIClient (47 tests) |
| Frontend Tests | Vitest + @vue/test-utils (19 tests) |
| Linting | Ruff (backend) · ESLint + eslint-plugin-vue (frontend) |

---

## Project Structure

```
insightboard/
├── backend/                    # Django project
│   ├── datasets/
│   │   ├── models.py           # Dataset, DatasetColumn, DataRow
│   │   ├── serializers.py      # DRF serializers (list + detail)
│   │   ├── views.py            # API views (CRUD, upload, row filter)
│   │   ├── urls.py             # URL patterns
│   │   └── tests.py            # 47 unit + API tests
│   ├── insightboard/
│   │   ├── settings.py
│   │   └── urls.py
│   ├── requirements.txt
│   └── ruff.toml               # Linter config
│
└── frontend/                   # Vue 3 + Vite project
    └── src/
        ├── assets/main.css     # Dark theme design system (CSS vars)
        ├── axios.js            # Axios instance (base URL /api)
        ├── router/index.js     # Routes: /, /upload, /datasets/:id
        ├── components/
        │   ├── NavBar.vue
        │   ├── DataTable.vue   # Filter · Sort · Paginate
        │   ├── ChartPanel.vue  # Bar · Line · Doughnut
        │   └── ToastNotification.vue
        ├── composables/
        │   └── useToast.js     # Global toast state
        ├── views/
        │   ├── HomeView.vue    # Dataset card grid
        │   ├── UploadView.vue  # Drag-and-drop CSV upload
        │   └── DatasetView.vue # Detail page (table + charts)
        └── tests/              # 19 Vitest component tests
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- pip

---

## Local Development Setup

### 1 — Clone the repo

```bash
git clone https://github.com/hardikhg1/insightboard.git
cd insightboard
```

### 2 — Backend

```powershell
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1          # Windows PowerShell
# source venv/bin/activate           # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Apply database migrations (creates db.sqlite3)
python manage.py migrate

# Run the development server (port 8000)
python manage.py runserver
```

### 3 — Frontend

```powershell
cd frontend

# Install npm packages
npm install

# Start Vite dev server (port 5173)
npm run dev
```

### 4 — Open the app

Navigate to **http://localhost:5173** in your browser.

> The Vite dev server proxies all `/api/` requests to Django on port 8000 — no CORS issues.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/datasets/` | List all datasets (id, name, row/col count) |
| `POST` | `/api/datasets/upload/` | Upload a CSV file (`multipart/form-data`, key: `file`) |
| `GET` | `/api/datasets/<id>/` | Dataset detail (nested columns + rows) |
| `DELETE` | `/api/datasets/<id>/` | Delete dataset and all its data |
| `GET` | `/api/datasets/<id>/rows/` | All rows (optionally filter: `?column=X&value=Y`) |

### Upload example (curl)

```bash
curl -X POST http://localhost:8000/api/datasets/upload/ \
     -F "file=@my_data.csv"
```

---

## Data Models

```
Dataset
  ├── name             (CharField)
  ├── original_filename(CharField)
  ├── uploaded_at      (DateTimeField, auto)
  ├── row_count        (PositiveIntegerField)
  └── column_count     (PositiveIntegerField)

DatasetColumn  (ForeignKey → Dataset)
  ├── name             (CharField)
  ├── position         (PositiveIntegerField)
  └── data_type        ('text' | 'number' | 'date')

DataRow  (ForeignKey → Dataset)
  ├── row_index        (PositiveIntegerField)
  └── data             (JSONField — one key per CSV column)
```

---

## Running Tests

### Backend (47 tests)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py test datasets --verbosity=2
```

### Frontend (19 tests)

```powershell
cd frontend
npm run test:run
```

---

## Linting

### Backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
ruff check .        # check
ruff check . --fix  # auto-fix
```

### Frontend

```powershell
cd frontend
npm run lint
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **JSONField for row data** | Allows arbitrary CSV schemas without schema migrations per upload |
| **Pandas for CSV parsing** | Robust type inference (`parse_dates`, `keep_default_na`) in one call |
| **Vite proxy for `/api`** | Eliminates CORS during development; no extra browser config needed |
| **Module-level `useToast`** | Shared toast state across components without Vuex/Pinia complexity |
| **Separate list + detail serializers** | List endpoint stays fast (no nested rows); detail loads full data |
| **Vue `<TransitionGroup>`** | Built-in animation primitive — zero extra libraries |

---

## Git Commit History

Each step is a separate commit for a clean review history:

| Commit | Step |
|--------|------|
| `Step 1-4` | Django project setup, models, migrations |
| `Step 5` | DRF serializers + API views |
| `Step 6` | CSV upload endpoint + row filter API |
| `Step 7` | Vue 3 frontend scaffold |
| `Step 8` | Data table with filter, sort, pagination |
| `Step 9` | Chart.js visualisations |
| `Step 10` | Integration polish (toasts, auto-redirect, responsive) |
| `Step 11` | 66 unit tests (47 backend + 19 frontend) |
| `Step 12` | Final cleanup, linting, README |
