"""Data management service using DuckDB."""
import duckdb
import polars as pl
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from dateutil.relativedelta import relativedelta


class DataManager:
    """Manage payroll data using DuckDB."""
    
    DB_PATH = Path("data/payroll.duckdb")
    
    @classmethod
    def _get_connection(cls):
        """Get database connection."""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return duckdb.connect(str(cls.DB_PATH))
    
    @classmethod
    def get_connection(cls):
        """Public method to get connection."""
        return cls._get_connection()
    
    @classmethod
    def close_connection(cls, conn):
        """Close connection."""
        if conn:
            conn.close()
    
    @classmethod
    def init_database(cls):
        """Initialize database schema."""
        conn = cls._get_connection()
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payroll_data (
                id INTEGER PRIMARY KEY,
                company_id VARCHAR,
                period_year INTEGER,
                period_month INTEGER,
                matricule VARCHAR,
                nom VARCHAR,
                prenom VARCHAR,
                date_naissance DATE,
                email VARCHAR,
                salaire_brut DOUBLE,
                salaire_net DOUBLE,
                total_charges_salariales DOUBLE,
                total_charges_patronales DOUBLE,
                cout_total_employeur DOUBLE,
                statut_validation BOOLEAN,
                edge_case_flag BOOLEAN,
                edge_case_reason VARCHAR,
                details_charges JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                company_id VARCHAR PRIMARY KEY,
                nom_societe VARCHAR,
                siret VARCHAR,
                adresse VARCHAR,
                email VARCHAR,
                point_contact VARCHAR,
                planning_jour_paie INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.close()
    
    @classmethod
    def get_companies(cls) -> List[str]:
        """Get list of company IDs."""
        conn = cls._get_connection()
        try:
            result = conn.execute("SELECT DISTINCT company_id FROM companies ORDER BY company_id").fetchall()
            return [r[0] for r in result]
        except:
            return []
        finally:
            conn.close()

    @classmethod
    def get_all_companies(cls) -> List[str]:
        """Alias for get_companies for backward compatibility."""
        return cls.get_companies()
    
    @classmethod
    def get_available_period_strings(cls, company_id: str) -> List[str]:
        """Get last 11 months as available periods."""
        # Generate last 11 months from current month
        periods = []
        current_date = datetime.now()

        for i in range(11):
            period_date = current_date - relativedelta(months=i)
            period_str = period_date.strftime("%m-%Y")
            periods.append(period_str)

        return periods
    
    @classmethod
    def load_period_data(cls, company_id: str, month: int, year: int) -> pl.DataFrame:
        """Load payroll data for period."""
        conn = cls._get_connection()
        try:
            df = conn.execute("""
                SELECT * FROM payroll_data
                WHERE company_id = ? AND period_year = ? AND period_month = ?
            """, [company_id, year, month]).pl()
            
            return df if not df.is_empty() else pl.DataFrame()
        except:
            return pl.DataFrame()
        finally:
            conn.close()
    
    @classmethod
    def save_period_data(cls, df: pl.DataFrame, company_id: str, month: int, year: int):
        """Save payroll data for period."""
        conn = cls._get_connection()
        try:
            # Add company/period columns
            df = df.with_columns([
                pl.lit(company_id).alias("company_id"),
                pl.lit(year).alias("period_year"),
                pl.lit(month).alias("period_month"),
            ])
            
            # Delete existing data for period
            conn.execute("""
                DELETE FROM payroll_data 
                WHERE company_id = ? AND period_year = ? AND period_month = ?
            """, [company_id, year, month])
            
            # Insert new data
            conn.execute("INSERT INTO payroll_data SELECT * FROM df")
            
        finally:
            conn.close()
    
    @classmethod
    def get_company_summary(cls, company_id: str, year: int, month: int) -> Optional[Dict]:
        """Get summary statistics for period."""
        conn = cls._get_connection()
        try:
            result = conn.execute("""
                SELECT 
                    COUNT(*) as employee_count,
                    SUM(salaire_brut) as total_brut,
                    SUM(salaire_net) as total_net,
                    SUM(total_charges_patronales) as total_charges_pat,
                    SUM(cout_total_employeur) as total_cost,
                    SUM(CASE WHEN statut_validation THEN 1 ELSE 0 END) as validated,
                    SUM(CASE WHEN edge_case_flag THEN 1 ELSE 0 END) as edge_cases
                FROM payroll_data
                WHERE company_id = ? AND period_year = ? AND period_month = ?
            """, [company_id, year, month]).fetchone()
            
            if result:
                return {
                    "employee_count": result[0],
                    "total_brut": result[1] or 0,
                    "total_net": result[2] or 0,
                    "total_charges_pat": result[3] or 0,
                    "total_cost": result[4] or 0,
                    "validated": result[5] or 0,
                    "edge_cases": result[6] or 0,
                }
            return None
        except:
            return None
        finally:
            conn.close()
    
    @classmethod
    def get_cumul_brut_annuel(cls, company_id: str, matricule: str, year: int, current_month: int) -> float:
        """
        Get cumulative annual gross salary for employee (January to current_month-1)
        Used for annual plafond calculations
        
        Args:
            company_id: Company identifier
            matricule: Employee ID
            year: Current year
            current_month: Current month (1-12)
            
        Returns:
            Sum of salaire_brut from January to current_month-1
        """
        conn = cls._get_connection()
        try:
            result = conn.execute("""
                SELECT COALESCE(SUM(salaire_brut), 0) as cumul
                FROM payroll_data
                WHERE company_id = ? 
                  AND matricule = ?
                  AND period_year = ?
                  AND period_month < ?
            """, [company_id, matricule, year, current_month]).fetchone()
            
            return float(result[0]) if result else 0.0
        except:
            return 0.0
        finally:
            conn.close()
    
    @classmethod
    def get_company_details(cls, company_id: str) -> Optional[Dict]:
        """Get company details."""
        conn = cls._get_connection()
        try:
            result = conn.execute("""
                SELECT * FROM companies WHERE company_id = ?
            """, [company_id]).fetchone()
            
            if result:
                return {
                    "company_id": result[0],
                    "nom_societe": result[1],
                    "siret": result[2],
                    "adresse": result[3],
                    "email": result[4],
                    "point_contact": result[5],
                    "planning_jour_paie": result[6],
                }
            return None
        except:
            return None
        finally:
            conn.close()
    
    @classmethod
    def get_company_age_months(cls, company_id: str) -> Optional[float]:
        """Get company age in months."""
        # Stub for MVP
        return None
    
    @classmethod
    def save_permanent_rubric(cls, company_id: str, matricule: str, code: str, field: str, label: str, user: str):
        """Save permanent rubric for employee."""
        # Stub for MVP
        pass
    
    @classmethod
    def check_existing_employees(cls, df: pl.DataFrame, company_id: str, month: int, year: int) -> Dict:
        """Check for existing employees in period."""
        # Stub for MVP
        return {"new": [], "existing": []}


class DataAuditLogger:
    """Audit logging for data modifications."""
    
    LOG_FILE = Path("data/audit_log.json")
    
    @classmethod
    def log_modification(cls, company_id: str, matricule: str, field: str, 
                        old_value, new_value, user: str, reason: str):
        """Log data modification."""
        cls.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "company_id": company_id,
            "matricule": matricule,
            "field": field,
            "old_value": str(old_value),
            "new_value": str(new_value),
            "user": user,
            "reason": reason
        }
        
        # Append to log file
        logs = []
        if cls.LOG_FILE.exists():
            import json
            with open(cls.LOG_FILE, 'r') as f:
                logs = json.load(f)
        
        logs.append(log_entry)
        
        import json
        with open(cls.LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
    
    @classmethod
    def is_first_bulletin(cls, company_id: str, matricule: str, year: int, month: int) -> bool:
        """Check if this is first bulletin for employee."""
        # Stub for MVP
        return False


# Initialize database on import
DataManager.init_database()
