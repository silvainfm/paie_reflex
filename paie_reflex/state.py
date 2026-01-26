"""Authentication state management using Reflex built-in auth"""

import reflex as rx
from typing import Optional
from datetime import datetime
from .services.auth import AuthManager


class GlobalState(rx.State):
    """Base global state - parent for all substates"""

    # Authentication
    username: str = ""
    password: str = ""
    is_authenticated: bool = False
    user: str = ""
    role: str = ""
    login_error: str = ""

    # Company & Period selection
    current_company: str = ""
    current_period: str = ""
    available_companies: list[str] = []
    available_periods: list[str] = []

    # Time tracking
    time_tracking_active: bool = False
    time_tracking_start: Optional[str] = None
    time_tracking_company: str = ""
    time_tracking_period: str = ""

    def check_auth(self):
        """Check if user is authenticated - used in on_load"""
        if not self.is_authenticated:
            return rx.redirect("/")

    def set_company(self, company: str):
        """Set current company and load available periods"""
        self.current_company = company
        # Load periods for this company
        from .services.data_mgt import DataManager
        periods = DataManager.get_available_period_strings(company)
        self.available_periods = periods
        if periods:
            self.current_period = periods[0]

        # Restart time tracking for new company
        self.check_and_restart_time_tracking()

    def set_period(self, period: str):
        """Set current period"""
        self.current_period = period

        # Restart time tracking for new period
        self.check_and_restart_time_tracking()

    def load_companies(self):
        """Load available companies"""
        from .services.data_mgt import DataManager
        companies = DataManager.get_companies()
        self.available_companies = companies
        if companies and not self.current_company:
            self.set_company(companies[0])

    @rx.var
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.role == "admin"

    @rx.var
    def has_selection(self) -> bool:
        """Check if company and period are selected"""
        return bool(self.current_company and self.current_period)

    def set_username(self, value: str):
        self.username = value

    def set_password(self, value: str):
        self.password = value

    async def login(self, form_data: dict):
        """Authenticate user"""
        username = form_data.get("username", "")
        password = form_data.get("password", "")

        if not username or not password:
            self.login_error = "Nom d'utilisateur et mot de passe requis"
            return

        # Use existing AuthManager
        if AuthManager.verify_login(username, password):
            user_data = AuthManager.get_user(username)
            self.is_authenticated = True
            self.user = username
            self.username = username
            self.role = user_data.get('role', 'comptable')
            self.login_error = ""

            # Load companies on login
            self.load_companies()

            # Start time tracking
            self.start_time_tracking()

            # Redirect to import page
            return rx.redirect("/import")
        else:
            self.login_error = "Identifiants invalides"
            self.is_authenticated = False

    def logout(self):
        """Logout user"""
        # Stop time tracking before logout
        self.stop_time_tracking()

        self.is_authenticated = False
        self.user = ""
        self.role = ""
        self.username = ""
        self.password = ""
        return rx.redirect("/")

    def start_time_tracking(self):
        """Start tracking time for current company/period"""
        if not self.is_authenticated or not self.current_company:
            return

        # Stop any existing session first
        if self.time_tracking_active:
            self.stop_time_tracking()

        self.time_tracking_active = True
        self.time_tracking_start = datetime.now().isoformat()
        self.time_tracking_company = self.current_company
        self.time_tracking_period = self.current_period

    def stop_time_tracking(self):
        """Stop tracking time and log session"""
        if not self.time_tracking_active or not self.time_tracking_start:
            return

        from .services.payslip_helpers import log_time_entry

        session_end = datetime.now()
        session_start = datetime.fromisoformat(self.time_tracking_start)
        duration_seconds = (session_end - session_start).total_seconds()

        # Only log if session > 10 seconds (avoid accidental clicks)
        if duration_seconds > 10:
            log_time_entry(
                user=self.user,
                company=self.time_tracking_company,
                period=self.time_tracking_period,
                duration_seconds=duration_seconds,
                session_start=self.time_tracking_start,
                session_end=session_end.isoformat()
            )

        self.time_tracking_active = False
        self.time_tracking_start = None
        self.time_tracking_company = ""
        self.time_tracking_period = ""

    def check_and_restart_time_tracking(self):
        """Check if company/period changed and restart tracking"""
        if not self.is_authenticated:
            return

        # If tracking is active and company/period changed
        if self.time_tracking_active:
            if (self.time_tracking_company != self.current_company or
                self.time_tracking_period != self.current_period):
                # Stop old session and start new one
                self.stop_time_tracking()
                self.start_time_tracking()
        else:
            # Start tracking if not active
            self.start_time_tracking()


class AuthState(GlobalState):
    """Manages authentication state - inherits from GlobalState"""
    pass


class CompanyState(GlobalState):
    """Manages company and period selection"""
    pass


class DataState(GlobalState):
    """Manages payroll data state"""

    processed_data: list[dict] = []
    edge_cases: list[dict] = []
    summary: dict = {}
    
    def load_period_data(self):
        """Load data for current company/period"""
        if not self.current_company or not self.current_period:
            return

        from .services.data_mgt import DataManager
        import polars as pl

        month, year = map(int, self.current_period.split('-'))
        df = DataManager.load_period_data(self.current_company, month, year)

        if not df.is_empty():
            self.processed_data = df.to_dicts()

            # Load edge cases
            edge_df = df.filter(pl.col('edge_case_flag') == True)
            self.edge_cases = edge_df.to_dicts() if not edge_df.is_empty() else []

            # Load summary
            self.summary = DataManager.get_company_summary(
                self.current_company, year, month
            )
    
    def clear_data(self):
        """Clear loaded data"""
        self.processed_data = []
        self.edge_cases = []
        self.summary = {}
