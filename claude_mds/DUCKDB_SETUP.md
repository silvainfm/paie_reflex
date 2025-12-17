# DuckDB Database Setup - Complete

## ✅ Database Configuration

### Primary Database: DuckDB
- **Location:** `data/payroll.duckdb`
- **Size:** 780 KB (initialized)
- **Tables:** `payroll_data`, `companies`
- **Status:** ✓ Verified working
- **Schema:** See README.md for complete database schema from original app

### Reflex Internal State: SQLite (Optional)
- **Location:** `reflex_state.db`
- **Purpose:** Reflex framework internals only
- **Note:** Payroll data does NOT use this

---

## 🔧 Key Changes Made

### 1. **rxconfig.py** - Updated Configuration
```python
config = rx.Config(
    app_name="paie_monaco",  # cspell: disable-line
    # Note: Payroll data uses DuckDB (data/payroll.duckdb)
    # This db_url is for Reflex internal state only
    db_url="sqlite:///reflex_state.db",
    timeout=600,  # 10 min for file uploads
    telemetry_enabled=False,
)
```

### 2. **paie_monaco/__init__.py** - Auto-Initialize DB
```python
from paie_monaco.services.data_mgt import DataManager

# Initialize DuckDB database on startup
try:
    DataManager.init_database()
    print("✓ DuckDB database initialized at data/payroll.duckdb")
except Exception as e:
    print(f"Warning: Could not initialize database: {e}")
```

### 3. **Import Path Fixes** - Consistent Imports
Changed all service imports from:
```python
from services.data_mgt import DataManager  # ❌ Old
```

To:
```python
from paie_monaco.services.data_mgt import DataManager  # ✅ New
```

---

## 🚀 Usage

### Starting the App
```bash
cd /Users/brych/Documents/Cab_Brych/paie_reflex
reflex run
```

**On first run:**
- DuckDB database auto-creates at `data/payroll.duckdb`
- Tables auto-initialize
- Ready for data import

### Testing Database
```bash
# Direct DuckDB test
uv run python test_duckdb.py

# Expected output:
# ✓ DuckDB test successful!
# - 2 tables created
# - Database: 780 KB
```

---

## 📊 Database Operations

### Load Companies
```python
from paie_monaco.services.data_mgt import DataManager

companies = DataManager.get_companies()
# Returns: ['COMPANY_A', 'COMPANY_B', ...]
```

### Load Period Data
```python
df = DataManager.load_period_data("COMPANY_A", month=12, year=2025)
# Returns: Polars DataFrame with employee payroll data
```

### Save Period Data
```python
DataManager.save_period_data(df, "COMPANY_A", month=12, year=2025)
# Saves payroll data to DuckDB
```

---

## ✅ Verification Checklist

- [x] DuckDB database file created (`data/payroll.duckdb`)
- [x] Tables initialized (schema from original app)
- [x] DataManager methods working
- [x] Import paths fixed throughout app
- [x] Auto-initialization on app startup
- [x] rxconfig.py updated and optimized
- [x] Spelling issues fixed
- [x] Test script created and verified

---

## 🔍 Database Location

**Full Path:**
```
/Users/brych/Documents/Cab_Brych/paie_reflex/data/payroll.duckdb
```

**Backup Command:**
```bash
cp data/payroll.duckdb data/payroll_backup_$(date +%Y%m%d).duckdb
```

**View with DuckDB CLI:**
```bash
duckdb data/payroll.duckdb
.tables
SELECT * FROM companies;
SELECT COUNT(*) FROM payroll_data;
```

---

## 📝 Next Steps

1. **Start app:** `reflex run`
2. **Import Excel data** - Populates payroll_data table
3. **Verify companies dropdown** - Should load from DB
4. **Test payroll processing** - Data saves to DuckDB
5. **Test validation page** - Loads employee data from DB
6. **Test PDF generation** - Reads from DuckDB
7. **Monitor performance** - DuckDB optimized for analytics

---

## ⚠️ Important Notes

1. **Two Separate Databases:**
   - `data/payroll.duckdb` = Payroll data (DuckDB) ← **This is what matters**
   - `reflex_state.db` = Reflex internals (SQLite, optional)

2. **Data Persistence:**
   - All payroll data persists in DuckDB
   - No data lost between app restarts
   - Compatible with original Streamlit app database

3. **Performance:**
   - DuckDB optimized for OLAP queries
   - Fast aggregations on large datasets
   - Direct Polars integration (.pl() method)
   - No need to load full dataset into memory

4. **Schema:**
   - See README.md for complete database schema
   - Matches original monaco_paie Streamlit app
   - Primary key: (company_id, period_year, period_month, matricule)

---

**✓ DuckDB setup complete and verified!**
**✓ Database initialized: 780 KB, 2 tables**
**✓ App ready for testing**
