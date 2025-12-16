# Monaco Payroll Management System - Reflex Version

Reflex-based web application for Monaco payroll management.

## Architecture

**Framework:** Reflex (Python fullstack framework)
**Database:** DuckDB
**Data Processing:** Polars
**Auth:** Reflex built-in + custom AuthManager
**Storage:** Local filesystem (cloud-ready)

## Database Schema

**`payroll_data` table** (Primary Key: company_id, period_year, period_month, matricule):
- Employee info: matricule, nom, prenom, email, date_naissance, emploi, qualification
- Hours: base_heures, heures_payees, heures_conges_payes, heures_absence, heures_sup_125/150, heures_jours_feries, heures_dimanche
- Salary: salaire_base, taux_horaire, prime, type_prime
- Benefits: tickets_restaurant, avantage_logement, avantage_transport
- Cross-border: pays_residence, ccss_number, teletravail, pays_teletravail
- Charges: total_charges_salariales, total_charges_patronales, details_charges (JSON)
- PTO: cp_acquis_n1, cp_pris_n1, cp_restants_n1, cp_acquis_n, cp_pris_n, cp_restants_n
- Totals: salaire_brut, salaire_net, cumul_brut, cumul_net_percu, cost_total_employeur
- Edge cases: edge_case_flag (BOOLEAN), edge_case_reason, statut_validation, remarques

**`companies` table**: id, name, siret, address, phone, email

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

## Monaco-Specific Context

**Regulatory Compliance**:
- DSM (Déclaration Sociale Monaco): Monthly XML submission to Caisses Sociales
- Meal tickets: 60% employer / 40% employee participation
- SMIC Monaco: 11.65€/hour (as of 2025)
- Work week: 169 hours/month standard

**Edge Case Categories** (parsed from "remarques" field):
1. `new_hire`: "embauche", "nouveau", "entrée le DD/MM"
2. `departure`: "départ", "sortie le DD/MM", "démission"
3. `salary_change`: "augmentation", "modification salaire"
4. `bonus`: "prime", "bonus", "13ème mois"
5. `unpaid_leave`: "congé sans solde", "arrêt maladie"
6. `prorate`: "prorata", "du DD au DD"

### Monaco Payroll Calculations

**Social Charges** (18 types in `ChargesSocialesMonaco`):
- **Salarial**: CAR (2.15%), CCSS (7.40% T1 + 2.00% T2), ASSEDIC (1.30%), retirement contributions, equilibrium
- **Patronal**: CAR (2.15%), CMRC TA/TB (3.34%/7.72%), ASSEDIC (1.90%), retirement, equilibrium, prevoyance

**Tranches** (income tiers):
- T1: Up to 3428€/month (1x social security ceiling)
- T2: 3428€ to 13712€/month (1x to 4x ceiling)

**Overtime**:
- 125%: First 8 hours over base (169h/month)
- 150%: Beyond 8 hours overtime

**PTO Accrual**: 2.08 days per month (25 days/year), with provision accounting

**Cross-Border Tax**:
- Monaco residents: No income tax, full social charges
- France residents: CSG/CRDS (9.70%), progressive tax (11%-45%), withholding in France
- Italy residents: IRPEF (23%-43%), 15% Monaco withholding

## Common Development Tasks

### Adding a New Salary Rubric
1. Add rubric code to `PDFGeneratorService.get_salary_rubrics()` in `services/pdf_generation.py`
2. Update calculation logic in `CalculateurPaieMonaco.process_employee_payslip()` in `services/payroll_calculations.py`
3. Add UI field in relevant Streamlit page in `app.py`
4. Update database schema if new column needed in `data_mgt.py`

### Adding a New Social Charge
1. Add charge to `ChargesSocialesMonaco` class in `services/payroll_calculations.py`
2. Add rate to `config/payroll_rates.csv` (CSV: Category=CHARGE, Type=SALARIAL/PATRONAL, Code=NEW_CODE, taux_YYYY=rate)
3. Update charge total calculations
4. Add to PDF generation in `pdf_generation.py` charge codes

### Modifying Edge Case Detection
1. Edit `RemarkParser` patterns in `services/edge_case_agent.py`
2. Add new category to `EdgeCaseCategory` enum if needed
3. Update `EdgeCaseAgent.process()` logic for auto-correction rules
4. Adjust confidence thresholds (default: >0.85 for auto-correction)

## Role-Based Access Control

**Admin Role**:
- Full system access
- User management
- Configuration changes
- All periods accessible

**Comptable (Accountant) Role**:
- Can modify last 2 months of paystubs only
- Cannot modify older data (unless new company)
- Can validate and generate PDFs
- Cannot manage users

## Important Constraints

**Data Editing Restrictions**:
- Accountants can only modify last 2 months of paystubs
- Exception: New companies (no historical data) - all periods editable
- Enforced at UI level in `app.py` validation pages

**Calculation Immutability**:
- Social charge rates loaded from `config/payroll_rates.csv` - **do not hardcode**
- Use `MonacoPayrollConstants(year=YYYY)` to get year-specific rates
- Charges recalculated on every save to ensure consistency

**PDF Requirements**:
- Must fit on single A4 page
- Blue color scheme (#1a5f9e)
- French formatting: comma decimals (1 234,56 €), DD/MM/YYYY dates
- Company info from `config/company_info.json`

**Concurrency**:
- DuckDB supports 10-15 concurrent users (configured in `data_mgt.py`)
- File locking used for `users.parquet` (5s timeout)

# Run Application

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
