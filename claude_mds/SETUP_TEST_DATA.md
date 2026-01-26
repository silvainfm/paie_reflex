# Setting Up Test Data

## Adding a Test Company

### Option 1: Using Python Script (Recommended)

Create a Python script to add a test company:

```bash
cat > add_test_company.py << 'EOF'
#!/usr/bin/env python3
import duckdb
from pathlib import Path

# Connect to database
db_path = Path("data/payroll.duckdb")
conn = duckdb.connect(str(db_path))

# Add test company
conn.execute("""
    INSERT INTO companies (
        company_id,
        nom_societe,
        siret,
        adresse,
        email,
        point_contact,
        planning_jour_paie
    )
    VALUES (
        'TEST001',
        'Société Test Monaco',
        '12345678901234',
        '1 Avenue des Spélugues, 98000 Monaco',
        'contact@test-monaco.mc',
        'Jean Dupont',
        25
    )
    ON CONFLICT (company_id) DO NOTHING
""")

print("✓ Company added successfully!")
print("\nCompany details:")
print("  ID: TEST001")
print("  Name: Société Test Monaco")
print("  SIRET: 12345678901234")
print("  Contact: Jean Dupont")
print("  Payday: 25th of month")

conn.close()
EOF

# Run the script
uv run python add_test_company.py
```

### Option 2: Using DuckDB CLI

```bash
# Install DuckDB CLI if needed
brew install duckdb  # macOS
# or download from https://duckdb.org/

# Open database
duckdb data/payroll.duckdb

# Add test company
INSERT INTO companies (
    company_id,
    nom_societe,
    siret,
    adresse,
    email,
    point_contact,
    planning_jour_paie
)
VALUES (
    'TEST001',
    'Société Test Monaco',
    '12345678901234',
    '1 Avenue des Spélugues, 98000 Monaco',
    'contact@test-monaco.mc',
    'Jean Dupont',
    25
);

# Verify
SELECT * FROM companies;

# Exit
.quit
```

### Option 3: From the App (Future Enhancement)

Currently, there's no UI to add companies directly. The Config page allows editing existing company info but not creating new ones. You'll need to add companies via database commands first.

## Adding Test Employee Data

After adding a company, you can import employee data via the **Import** page in the app:

1. Start the app: `reflex run`
2. Navigate to **Import** page
3. Download the Excel template
4. Fill in employee data:
   - company_id: `TEST001`
   - period_year: `2024`
   - period_month: `12`
   - Employee details (matricule, nom, prenom, etc.)
5. Upload the Excel file

## Verifying Data

Check companies in database:

```bash
uv run python -c "
import duckdb
conn = duckdb.connect('data/payroll.duckdb')
companies = conn.execute('SELECT * FROM companies').fetchall()
print(f'Companies: {len(companies)}')
for c in companies:
    print(f'  - {c[0]}: {c[1]}')
conn.close()
"
```

## Database Schema Reference

### Companies Table
- `company_id` (VARCHAR, PRIMARY KEY)
- `nom_societe` (VARCHAR)
- `siret` (VARCHAR)
- `adresse` (VARCHAR)
- `email` (VARCHAR)
- `point_contact` (VARCHAR)
- `planning_jour_paie` (INTEGER) - day of month for payroll
- `created_at` (TIMESTAMP)

### Payroll Data Table
See `.claude/CLAUDE.md` for full schema.
