"""Authentication state management using Reflex built-in auth"""

import reflex as rx
from typing import Optional
import sys
from pathlib import Path

# Add services path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from services.auth import AuthManager


class AuthState(rx.State):
    """Manages authentication state"""
    
    username: str = ""
    password: str = ""
    is_authenticated: bool = False
    user: str = ""
    role: str = ""
    error_message: str = ""
    
    def set_username(self, value: str):
        self.username = value
        
    def set_password(self, value: str):
        self.password = value
    
    async def login(self):
        """Authenticate user"""
        if not self.username or not self.password:
            self.error_message = "Username and password required"
            return
        
        # Use existing AuthManager
        if AuthManager.verify_user(self.username, self.password):
            user_data = AuthManager.get_user(self.username)
            self.is_authenticated = True
            self.user = self.username
            self.role = user_data.get('role', 'comptable')
            self.error_message = ""
            
            # Redirect to import page
            return rx.redirect("/import")
        else:
            self.error_message = "Invalid credentials"
            self.is_authenticated = False
    
    def logout(self):
        """Logout user"""
        self.is_authenticated = False
        self.user = ""
        self.role = ""
        self.username = ""
        self.password = ""
        return rx.redirect("/")
    
    def check_auth(self):
        """Check if user is authenticated - used in on_load"""
        if not self.is_authenticated:
            return rx.redirect("/")
    
    @property
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.role == "admin"


class CompanyState(rx.State):
    """Manages company and period selection"""
    
    current_company: str = ""
    current_period: str = ""
    available_companies: list[str] = []
    available_periods: list[str] = []
    
    def set_company(self, company: str):
        """Set current company and load available periods"""
        self.current_company = company
        # Load periods for this company
        from services.data_mgt import DataManager
        periods = DataManager.get_available_period_strings(company)
        self.available_periods = periods
        if periods:
            self.current_period = periods[0]
    
    def set_period(self, period: str):
        """Set current period"""
        self.current_period = period
    
    def load_companies(self):
        """Load available companies"""
        from services.data_mgt import DataManager
        companies = DataManager.get_all_companies()
        self.available_companies = companies
        if companies and not self.current_company:
            self.set_company(companies[0])


class DataState(rx.State):
    """Manages payroll data state"""
    
    processed_data: list[dict] = []
    edge_cases: list[dict] = []
    summary: dict = {}
    
    def load_period_data(self):
        """Load data for current company/period"""
        company_state = self.get_state(CompanyState)
        
        if not company_state.current_company or not company_state.current_period:
            return
        
        from services.data_mgt import DataManager
        import polars as pl
        
        month, year = map(int, company_state.current_period.split('-'))
        df = DataManager.load_period_data(company_state.current_company, month, year)
        
        if not df.is_empty():
            self.processed_data = df.to_dicts()
            
            # Load edge cases
            edge_df = df.filter(pl.col('edge_case_flag') == True)
            self.edge_cases = edge_df.to_dicts() if not edge_df.is_empty() else []
            
            # Load summary
            self.summary = DataManager.get_company_summary(
                company_state.current_company, year, month
            )
    
    def clear_data(self):
        """Clear loaded data"""
        self.processed_data = []
        self.edge_cases = []
        self.summary = {}
