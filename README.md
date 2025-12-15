# Monaco Payroll Management System - Reflex Version

Reflex-based web application for Monaco payroll management.

## Architecture

**Framework:** Reflex (Python fullstack framework)
**Database:** DuckDB
**Data Processing:** Polars
**Auth:** Reflex built-in + custom AuthManager
**Storage:** Local filesystem (cloud-ready)

## Setup

### 1. Prerequisites

```bash
python 3.11+
pip
```

### 2. Copy Services

Copy the entire `services/` directory from the original Streamlit app:

```bash
cp -r /path/to/streamlit-app/services /path/to/reflex-paie-monaco/
```

Required service files:
- auth.py
- data_mgt.py
- shared_utils.py
- payroll_system.py
- excel_import_export.py
- pdf_generation.py
- edge_case_agent.py
- dsm_xml_generator.py
- payroll_calculations.py
- email_archive.py
- payslip_helpers.py

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

Create required directories:

```bash
mkdir -p data/config
mkdir -p data/db
mkdir -p data/consolidated
```

Create initial config files:

**data/config/company_info.json:**
```json
{
  "name": "Your Company",
  "siret": "12345678901234",
  "address": "Monaco Address",
  "phone": "+377...",
  "email": "contact@company.mc",
  "employer_number_monaco": "12345"
}
```

### 5. Run Application

```bash
reflex run
```

Access at `http://localhost:3000`

## Default Admin Login

First time setup - create admin user via Config page or:

```python
from services.auth import AuthManager
AuthManager.add_or_update_user("admin", "changeme", "admin", "Admin User")
```

## Key Differences from Streamlit

**State Management:**
- Class-based State instead of session_state
- Reactive updates via Reflex State

**File Uploads:**
- rx.upload() instead of st.file_uploader()
- Async file handling

**Forms:**
- rx.form() with on_submit
- No st.form context manager

**Navigation:**
- Route-based with rx.redirect()
- No st.rerun()

**Downloads:**
- rx.download() instead of st.download_button()
- Generated on-demand

**Charts:**
- rx.recharts instead of st.line_chart
- More configuration required

## Simplified Features (MVP)

**Validation Page:**
- Basic editing (full editing to be implemented)
- Focus on validation workflow

**PDF Page:**
- Core generation functions
- Simplified multi-document handling

**Dashboard:**
- Essential metrics
- Basic trend visualization

## Features Preserved

✅ All 7 pages
✅ DuckDB backend
✅ Polars data processing
✅ Authentication & roles
✅ Company/period selection
✅ Import/export workflows
✅ PDF generation
✅ DSM XML export
✅ Edge case agent
✅ Processing pipeline

## Production Deployment

**Reflex Cloud:**
```bash
reflex deploy
```

**Self-hosted:**
```bash
reflex export
# Deploy static files + API server
```

## Development

**Hot reload:**
```bash
reflex run --loglevel debug
```

**Database inspection:**
```python
import duckdb
conn = duckdb.connect('data/db/payroll.duckdb')
conn.execute("SELECT * FROM payroll_data LIMIT 5").fetchdf()
```

## Troubleshooting

**Services not found:**
- Ensure services/ directory is copied
- Check sys.path in page files

**Upload issues:**
- Verify rx.upload accepts correct MIME types
- Check async file handling

**State not updating:**
- Use State methods, not direct assignment
- Ensure on_change callbacks set correctly

**Download not working:**
- Return rx.download() from State method
- Don't use yield, use return

## Cost Comparison

**Self-hosted:** Free (server costs only)
**Reflex Cloud:** ~$20-50/month (depends on usage)

Start self-hosted, migrate to cloud as needed.
