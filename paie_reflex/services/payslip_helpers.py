"""
Payslip Editing Helpers
======================
Helper functions for payslip validation, editing, and data cleaning
Framework-agnostic utility functions
"""

import json
import polars as pl
import numpy as np
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache
from .payroll_calculations import MonacoPayrollConstants, ChargesSocialesMonaco, CalculateurPaieMonaco
from .pdf_generation import PaystubPDFGenerator
from .data_mgt import DataManager

# ============================================================================
# RUBRICS AND CODES
# ============================================================================

@lru_cache(maxsize=1)
def load_rubrics_from_excel() -> List[Dict]:
    """
    Load salary rubrics from config/acc_rem.xlsx

    Returns list of rubrics with filtering:
    - Excludes rubrics with 'X' in 'Ajout automatique' (auto-added by system)
    - Excludes rubrics with 'X' in 'Presence obligatoire' (mandatory presence)
    - Returns rubrics available for manual addition
    """
    excel_path = Path("data/config") / "acc_rem.xlsx"

    if not excel_path.exists():
        return []

    try:
        df = pl.read_excel(excel_path)

        rubrics = []
        for row in df.iter_rows(named=True):
            # Filter logic: exclude auto and mandatory rubrics
            ajout_auto = str(row.get('Ajout automatique') or '').strip().upper() == 'X'
            presence_oblig = str(row.get('Presence obligatoire') or '').strip().upper() == 'X'

            # Skip if auto-added or mandatory
            if ajout_auto or presence_oblig:
                continue

            rubric = {
                'code': int(row['Rémunération']),
                'label': str(row['Libellé']),
                'field_name': str(row['field_name']),
                'calcul': str(row.get('Calcul') or ''),
                'cotisable_mc': str(row.get('Cotisable MC  ?') or '').strip().upper() == 'X',
                'cotisable_autres': str(row.get('Cotisable autres cot ?') or '').strip().upper() == 'X',
                'base_cp': str(row.get('Base CP') or '').strip().upper() == 'X',
                'imposable': str(row.get('Imposable ?') or '').strip().upper() == 'X',
            }
            rubrics.append(rubric)

        return rubrics
    except Exception as e:
        print(f"Error loading rubrics: {e}")
        return []

def get_salary_rubrics() -> List[Dict]:
    """Get salary element rubrics from pdf_generation"""
    codes = PaystubPDFGenerator.RUBRIC_CODES

    return [
        {'code': codes['salaire_base'], 'label': 'Salaire Mensuel', 'field': 'salaire_base'},
        {'code': codes['prime_anciennete'], 'label': "Prime d'ancienneté", 'field': 'prime_anciennete'},
        {'code': codes['heures_sup_125'], 'label': 'Heures sup. 125%', 'field': 'heures_sup_125'},
        {'code': codes['heures_sup_150'], 'label': 'Heures sup. 150%', 'field': 'heures_sup_150'},
        {'code': codes['prime_performance'], 'label': 'Prime performance', 'field': 'prime'},
        {'code': codes['prime_autre'], 'label': 'Autre prime', 'field': 'prime_autre'},
        {'code': codes['prime_non_cotisable'], 'label': 'Prime non cotisable', 'field': 'prime_non_cotisable'},
        {'code': codes['jours_feries'], 'label': 'Jours fériés 100%', 'field': 'heures_jours_feries'},
        {'code': codes['absence_maladie'], 'label': 'Absence maladie', 'field': 'heures_absence'},
        {'code': codes['absence_cp'], 'label': 'Absence congés payés', 'field': 'heures_conges_payes'},
        {'code': codes['indemnite_cp'], 'label': 'Indemnité congés payés', 'field': 'jours_conges_pris'},
        {'code': codes['tickets_resto'], 'label': 'Tickets restaurant', 'field': 'tickets_restaurant'},
    ]

def get_all_available_salary_rubrics(year: int = None) -> List[Dict]:
    """Get all available salary rubrics including constants"""
    all_rubrics = []

    # Add standard salary rubrics
    codes = PaystubPDFGenerator.RUBRIC_CODES
    all_rubrics.extend([
        {'code': codes['salaire_base'], 'label': 'Salaire Mensuel', 'field': 'salaire_base'},
        {'code': codes['prime_anciennete'], 'label': "Prime d'ancienneté", 'field': 'prime_anciennete'},
        {'code': codes['heures_sup_125'], 'label': 'Heures sup. 125%', 'field': 'heures_sup_125'},
        {'code': codes['heures_sup_150'], 'label': 'Heures sup. 150%', 'field': 'heures_sup_150'},
        {'code': codes['prime_performance'], 'label': 'Prime performance', 'field': 'prime'},
        {'code': codes['prime_autre'], 'label': 'Autre prime', 'field': 'prime_autre'},
        {'code': codes['prime_non_cotisable'], 'label': 'Prime non cotisable', 'field': 'prime_non_cotisable'},
        {'code': codes['jours_feries'], 'label': 'Jours fériés 100%', 'field': 'heures_jours_feries'},
        {'code': codes['absence_maladie'], 'label': 'Absence maladie', 'field': 'heures_absence'},
        {'code': codes['absence_cp'], 'label': 'Absence congés payés', 'field': 'heures_conges_payes'},
        {'code': codes['indemnite_cp'], 'label': 'Indemnité congés payés', 'field': 'jours_conges_pris'},
        {'code': codes['tickets_resto'], 'label': 'Tickets restaurant', 'field': 'tickets_restaurant'},
        {'code': codes['maintien_salaire'], 'label': 'Maintien de salaire', 'field': 'maintien_salaire'},
    ])

    # Add constants from CSV
    csv_path = Path("data/config") / "payroll_rates.csv"
    if csv_path.exists():
        try:
            df = pl.read_csv(csv_path)
            constants_df = df.filter(pl.col("category") == "CONSTANT")
            for row in constants_df.iter_rows(named=True):
                const_code = row["code"]
                const_desc = row.get("description", const_code)
                all_rubrics.append({
                    'code': const_code,
                    'label': const_desc,
                    'field': const_code.lower()
                })
        except Exception as e:
            print(f"Error loading constants: {e}")

    return all_rubrics

def get_available_rubrics_for_employee(employee_data: Dict, year: int = None) -> List[Dict]:
    """Get rubrics not currently displayed for this employee"""
    all_rubrics = load_rubrics_from_excel()

    displayed_fields = set()
    for rubric in all_rubrics:
        field = rubric['field_name']
        if safe_get_numeric(employee_data, field, 0) != 0:
            displayed_fields.add(field)

    available = [r for r in all_rubrics if r['field_name'] not in displayed_fields]
    return available

def get_charge_rubrics() -> Dict[str, List[Dict]]:
    """Get social charge rubrics"""
    charges_calc = ChargesSocialesMonaco()
    
    salariales = []
    for key, params in charges_calc.COTISATIONS_SALARIALES.items():
        salariales.append({
            'code': key,
            'label': params['description'],
            'taux': params['taux'],
            'plafond': params['plafond']
        })

    patronales = []
    for key, params in charges_calc.COTISATIONS_PATRONALES.items():
        patronales.append({
            'code': key,
            'label': params['description'],
            'taux': params['taux'],
            'plafond': params['plafond']
        })

    return {
        'salariales': salariales,
        'patronales': patronales
    }

def get_available_charges_for_employee(employee_data: Dict, year: int = None, month: int = None) -> List[Dict]:
    """Get charge codes not currently displayed for this employee"""
    charges_calc = ChargesSocialesMonaco(year, month)

    all_charges = {}
    for code, params in charges_calc.COTISATIONS_SALARIALES.items():
        all_charges[code] = {
            'code': code,
            'label': params['description'],
            'taux_sal': params['taux'],
            'taux_pat': 0,
            'plafond': params['plafond'],
            'has_salarial': True,
            'has_patronal': False
        }

    for code, params in charges_calc.COTISATIONS_PATRONALES.items():
        if code in all_charges:
            all_charges[code]['taux_pat'] = params['taux']
            all_charges[code]['has_patronal'] = True
        else:
            all_charges[code] = {
                'code': code,
                'label': params['description'],
                'taux_sal': 0,
                'taux_pat': params['taux'],
                'plafond': params['plafond'],
                'has_salarial': False,
                'has_patronal': True
            }

    details_charges = employee_data.get('details_charges', {})
    charges_sal = details_charges.get('charges_salariales', {})
    charges_pat = details_charges.get('charges_patronales', {})

    displayed_codes = set()
    for code in charges_sal.keys():
        if charges_sal.get(code, 0) != 0:
            displayed_codes.add(code)
    for code in charges_pat.keys():
        if charges_pat.get(code, 0) != 0:
            displayed_codes.add(code)

    available = [charge for code, charge in all_charges.items() if code not in displayed_codes]
    return available

# ============================================================================
# PAYSLIP RECALCULATION
# ============================================================================

def recalculate_employee_payslip(employee_data: Dict, modifications: Dict,
                                 company_id: str = None, year: int = None, month: int = None) -> Dict:
    """Recalculate payslip after modifications"""
    updated_data = {}

    # Copy and clean all fields
    for key, value in employee_data.items():
        if key in ['salaire_brut', 'salaire_base', 'salaire_net', 'total_charges_salariales',
                   'total_charges_patronales', 'heures_sup_125', 'heures_sup_150', 'prime',
                   'montant_hs_125', 'montant_hs_150', 'cout_total_employeur', 'taux_horaire',
                   'base_heures', 'heures_payees', 'retenue_absence', 'heures_absence',
                   'indemnite_cp', 'heures_jours_feries', 'montant_jours_feries',
                   'prime_anciennete', 'prime_autre', 'tickets_restaurant']:
            if isinstance(value, dict):
                updated_data[key] = 0.0
            elif value is None:
                updated_data[key] = 0.0
            else:
                try:
                    updated_data[key] = float(value)
                except (TypeError, ValueError):
                    updated_data[key] = 0.0
        else:
            updated_data[key] = value

    # Handle nested charges updates
    if 'charges_salariales' in modifications or 'charges_patronales' in modifications:
        if 'details_charges' not in updated_data:
            updated_data['details_charges'] = {'charges_salariales': {}, 'charges_patronales': {}}
        if not isinstance(updated_data['details_charges'], dict):
            updated_data['details_charges'] = {'charges_salariales': {}, 'charges_patronales': {}}

        if 'charges_salariales' in modifications:
            if 'charges_salariales' not in updated_data['details_charges']:
                updated_data['details_charges']['charges_salariales'] = {}
            updated_data['details_charges']['charges_salariales'].update(modifications['charges_salariales'])

        if 'charges_patronales' in modifications:
            if 'charges_patronales' not in updated_data['details_charges']:
                updated_data['details_charges']['charges_patronales'] = {}
            updated_data['details_charges']['charges_patronales'].update(modifications['charges_patronales'])

        modifications = {k: v for k, v in modifications.items()
                        if k not in ['charges_salariales', 'charges_patronales']}

    updated_data.update(modifications)

    # Get cumulative annual gross
    cumul_brut_annuel = 0.0
    if company_id and year and month:
        matricule = updated_data.get('matricule', '')
        if matricule:
            cumul_brut_annuel = DataManager.get_cumul_brut_annuel(company_id, matricule, year, month)

    # Recalculate
    calculator = CalculateurPaieMonaco(year, month)
    return calculator.process_employee_payslip(updated_data, cumul_brut_annuel=cumul_brut_annuel)

# ============================================================================
# DATA CLEANING AND VALIDATION
# ============================================================================

def clean_employee_data_for_pdf(employee_dict: Dict) -> Dict:
    """Clean employee data to ensure numeric fields are not dicts"""
    numeric_fields = [
        'salaire_brut', 'salaire_base', 'salaire_net',
        'total_charges_salariales', 'total_charges_patronales',
        'heures_sup_125', 'heures_sup_150', 'prime',
        'montant_hs_125', 'montant_hs_150', 'cout_total_employeur',
        'taux_horaire', 'base_heures', 'heures_payees',
        'retenue_absence', 'heures_absence', 'indemnite_cp',
        'heures_jours_feries', 'montant_jours_feries',
        'cumul_brut', 'cumul_base_ss', 'cumul_net_percu',
        'cumul_charges_sal', 'cumul_charges_pat',
        'jours_cp_pris', 'tickets_restaurant'
    ]

    cleaned = {}

    for key, value in employee_dict.items():
        if key in numeric_fields:
            if value is None:
                cleaned[key] = 0
            elif isinstance(value, dict):
                cleaned[key] = 0
            elif isinstance(value, (list, tuple)):
                cleaned[key] = 0
            elif isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                cleaned[key] = 0
            elif isinstance(value, (int, float, np.integer, np.floating)):
                cleaned[key] = float(value)
            else:
                try:
                    cleaned[key] = float(value)
                except (TypeError, ValueError, AttributeError):
                    cleaned[key] = 0
        else:
            cleaned[key] = value if value is not None else ""

    return cleaned

def safe_get_charge_value(details_charges: Dict, charge_type: str, charge_code: str) -> float:
    """Safely extract charge value from details_charges structure"""
    try:
        charges = details_charges.get(charge_type, {})
        if isinstance(charges, dict):
            value = charges.get(charge_code, 0)
            if isinstance(value, dict):
                return float(value.get('montant', value.get('value', 0)))
            return float(value) if value is not None else 0.0
        return 0.0
    except (TypeError, ValueError, AttributeError):
        return 0.0

def safe_get_numeric(row: Dict, field: str, default: float = 0.0) -> float:
    """Safely extract numeric value from dict"""
    try:
        value = row.get(field, default)
        if isinstance(value, dict):
            return float(value.get('montant', value.get('value', value.get('amount', default))))
        if value is None or (isinstance(value, float) and pl.datatypes.Float64.is_null(value)):
            return default
        return float(value)
    except (TypeError, ValueError, AttributeError):
        return default

# ============================================================================
# AUDIT AND MODIFICATION TRACKING
# ============================================================================

def log_modification(matricule: str, field: str, old_value, new_value, 
                    user: str, reason: str, company: str, period: str):
    """Log paystub modification for audit trail"""
    log_dir = Path("data/audit_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'user': user,
        'matricule': matricule,
        'field': field,
        'old_value': str(old_value),
        'new_value': str(new_value),
        'reason': reason,
        'period': period,
        'company': company
    }

    log_file = log_dir / f"modifications_{datetime.now().strftime('%Y%m')}.jsonl"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

def log_time_entry(user: str, company: str, period: str, duration_seconds: float, 
                   session_start: str, session_end: str):
    """Log time spent on company payslips"""
    log_dir = Path("data/audit_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_entry = {
        'timestamp': session_end,
        'entry_type': 'time_tracking',
        'user': user,
        'company': company,
        'period': period,
        'session_start': session_start,
        'session_end': session_end,
        'duration_seconds': duration_seconds,
        'duration_minutes': round(duration_seconds / 60, 2)
    }

    log_file = log_dir / f"modifications_{datetime.now().strftime('%Y%m')}.jsonl"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

def get_audit_logs(start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   company: Optional[str] = None,
                   user: Optional[str] = None) -> pl.DataFrame:
    """Load audit logs with optional filtering"""
    log_dir = Path("data/audit_logs")
    if not log_dir.exists():
        return pl.DataFrame()

    all_logs = []
    for log_file in log_dir.glob("*.jsonl"):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    all_logs.append(json.loads(line))
                except:
                    pass

    if not all_logs:
        return pl.DataFrame()

    df = pl.DataFrame(all_logs)

    # Add entry_type if missing
    if 'entry_type' not in df.columns:
        df = df.with_columns(pl.lit('modification').alias('entry_type'))

    # Parse timestamps
    df = df.with_columns(
        pl.col('timestamp').str.strptime(pl.Datetime, format='%Y-%m-%dT%H:%M:%S%.f')
    )

    # Apply filters
    if start_date:
        df = df.filter(pl.col('timestamp') >= start_date)
    if end_date:
        df = df.filter(pl.col('timestamp') <= end_date)
    if company:
        df = df.filter(pl.col('company') == company)
    if user:
        df = df.filter(pl.col('user') == user)

    return df.sort('timestamp', descending=True)

def get_time_tracking_summary(company: Optional[str] = None,
                               user: Optional[str] = None) -> pl.DataFrame:
    """Get time tracking summary by company and user"""
    df = get_audit_logs(company=company, user=user)

    if df.is_empty():
        return pl.DataFrame()

    # Filter for time tracking entries
    time_df = df.filter(pl.col('entry_type') == 'time_tracking')

    if time_df.is_empty():
        return pl.DataFrame()

    # Aggregate by user and company
    summary = time_df.group_by(['user', 'company']).agg([
        pl.col('duration_minutes').sum().alias('total_minutes'),
        pl.col('duration_minutes').count().alias('session_count'),
        pl.col('duration_minutes').mean().alias('avg_minutes_per_session')
    ]).with_columns([
        (pl.col('total_minutes') / 60).round(2).alias('total_hours')
    ])

    return summary.sort('total_minutes', descending=True)
