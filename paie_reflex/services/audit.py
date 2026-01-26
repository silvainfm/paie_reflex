"""Audit trail and time tracking page."""
import reflex as rx
from datetime import datetime, timedelta
from typing import List, Dict
from ..state import GlobalState
from ..components import navbar, sidebar_nav
from ..services.payslip_helpers import get_audit_logs


class AuditState(GlobalState):
    """State for audit page."""
    
    # Filters
    user_filter: str = "All"
    period_filter: str = "All"
    company_filter: str = "All"
    date_from: str = ""
    date_to: str = ""
    
    # Data
    all_logs: List[Dict] = []
    modification_logs: List[Dict] = []
    time_logs: List[Dict] = []
    
    # Stats
    total_modifications: int = 0
    total_time_sessions: int = 0
    total_hours: float = 0.0
    
    # Time reports
    time_by_company: List[Dict] = []
    time_by_user: List[Dict] = []
    
    def load_audit_data(self):
        """Load all audit logs."""
        import polars as pl
        
        # Load logs
        df = get_audit_logs()
        
        if df.is_empty():
            self.all_logs = []
            self.modification_logs = []
            self.time_logs = []
            return
        
        # Convert to list of dicts
        self.all_logs = df.to_dicts()
        
        # Separate modifications and time tracking
        mod_df = df.filter(pl.col('entry_type') != 'time_tracking')
        time_df = df.filter(pl.col('entry_type') == 'time_tracking')
        
        self.modification_logs = mod_df.to_dicts() if not mod_df.is_empty() else []
        self.time_logs = time_df.to_dicts() if not time_df.is_empty() else []
        
        # Calculate stats
        self.total_modifications = len(self.modification_logs)
        self.total_time_sessions = len(self.time_logs)
        
        if not time_df.is_empty():
            self.total_hours = round(time_df['duration_minutes'].sum() / 60, 2)
        
        # Generate reports
        self._generate_time_reports(time_df)
    
    def _generate_time_reports(self, time_df):
        """Generate time aggregation reports."""
        import polars as pl
        
        if time_df.is_empty():
            self.time_by_company = []
            self.time_by_user = []
            return
        
        # Time by company/period
        by_company = time_df.group_by(['company', 'period']).agg([
            pl.col('duration_minutes').sum().alias('total_minutes'),
            pl.col('duration_minutes').count().alias('sessions')
        ]).with_columns(
            (pl.col('total_minutes') / 60).round(2).alias('total_hours')
        ).sort('total_minutes', descending=True)
        
        self.time_by_company = by_company.to_dicts()
        
        # Time by user
        by_user = time_df.group_by('user').agg([
            pl.col('duration_minutes').sum().alias('total_minutes'),
            pl.col('duration_minutes').count().alias('sessions'),
            pl.col('company').n_unique().alias('companies')
        ]).with_columns(
            (pl.col('total_minutes') / 60).round(2).alias('total_hours')
        ).sort('total_minutes', descending=True)
        
        self.time_by_user = by_user.to_dicts()
    
    async def apply_filters(self):
        """Apply filters to logs."""
        import polars as pl
        
        # Reload fresh data
        df = get_audit_logs()
        
        if df.is_empty():
            return
        
        # Apply filters
        if self.user_filter != "All":
            df = df.filter(pl.col('user') == self.user_filter)
        
        if self.period_filter != "All":
            df = df.filter(pl.col('period') == self.period_filter)
        
        if self.company_filter != "All":
            df = df.filter(pl.col('company') == self.company_filter)
        
        if self.date_from:
            from_dt = datetime.fromisoformat(self.date_from)
            df = df.filter(pl.col('timestamp') >= from_dt)
        
        if self.date_to:
            to_dt = datetime.fromisoformat(self.date_to)
            df = df.filter(pl.col('timestamp') <= to_dt)
        
        # Update filtered data
        self.all_logs = df.to_dicts()
        
        mod_df = df.filter(pl.col('entry_type') != 'time_tracking')
        time_df = df.filter(pl.col('entry_type') == 'time_tracking')
        
        self.modification_logs = mod_df.to_dicts() if not mod_df.is_empty() else []
        self.time_logs = time_df.to_dicts() if not time_df.is_empty() else []
        
        self.total_modifications = len(self.modification_logs)
        self.total_time_sessions = len(self.time_logs)
        
        if not time_df.is_empty():
            self.total_hours = round(time_df['duration_minutes'].sum() / 60, 2)
        else:
            self.total_hours = 0.0
        
        self._generate_time_reports(time_df)
    
    @rx.var
    def audit_users(self) -> List[str]:
        """Get list of users from logs."""
        users = set()
        for log in self.all_logs:
            if log.get('user'):
                users.add(log['user'])
        return ["All"] + sorted(list(users))

    @rx.var
    def audit_periods(self) -> List[str]:
        """Get list of periods from logs."""
        periods = set()
        for log in self.all_logs:
            if log.get('period'):
                periods.add(log['period'])
        return ["All"] + sorted(list(periods), reverse=True)

    @rx.var
    def audit_companies(self) -> List[str]:
        """Get list of companies from logs."""
        companies = set()
        for log in self.all_logs:
            if log.get('company'):
                companies.add(log['company'])
        return ["All"] + sorted(list(companies))


def modification_row(log: Dict) -> rx.Component:
    """Render a modification log row."""
    return rx.table.row(
        rx.table.cell(log.get('timestamp', '')[:19]),
        rx.table.cell(log.get('user', '')),
        rx.table.cell(log.get('matricule', '')),
        rx.table.cell(log.get('field', '')),
        rx.table.cell(str(log.get('old_value', ''))),
        rx.table.cell(str(log.get('new_value', ''))),
        rx.table.cell(log.get('reason', '')),
    )


def time_session_row(log: Dict) -> rx.Component:
    """Render a time tracking session row."""
    return rx.table.row(
        rx.table.cell(log.get('timestamp', '')[:19]),
        rx.table.cell(log.get('user', '')),
        rx.table.cell(log.get('company', '')),
        rx.table.cell(log.get('period', '')),
        rx.table.cell(f"{log.get('duration_minutes', 0):.1f} min"),
        rx.table.cell(log.get('session_start', '')[:19]),
        rx.table.cell(log.get('session_end', '')[:19]),
    )


def company_time_row(item: Dict) -> rx.Component:
    """Render company time aggregation row."""
    return rx.table.row(
        rx.table.cell(item.get('company', '')),
        rx.table.cell(item.get('period', '')),
        rx.table.cell(f"{item.get('total_hours', 0):.2f}h"),
        rx.table.cell(str(item.get('sessions', 0))),
    )


def user_time_row(item: Dict) -> rx.Component:
    """Render user time aggregation row."""
    return rx.table.row(
        rx.table.cell(item.get('user', '')),
        rx.table.cell(f"{item.get('total_hours', 0):.2f}h"),
        rx.table.cell(str(item.get('sessions', 0))),
        rx.table.cell(str(item.get('companies', 0))),
    )


def index() -> rx.Component:
    """Audit page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    rx.heading("Audit Trail & Time Tracking", size="8", margin_bottom="1rem"),
                    
                    rx.cond(
                        ~GlobalState.is_admin,
                        rx.callout(
                            "Admin access required",
                            icon="lock",
                            color_scheme="red",
                        ),
                        rx.vstack(
                            # Filters
                            rx.card(
                                rx.vstack(
                                    rx.heading("Filters", size="5"),
                                    rx.hstack(
                                        rx.vstack(
                                            rx.text("User", size="2"),
                                            rx.select(
                                                AuditState.audit_users,
                                                value=AuditState.user_filter,
                                                on_change=AuditState.user_filter.set,
                                            ),
                                            spacing="1",
                                        ),
                                        rx.vstack(
                                            rx.text("Period", size="2"),
                                            rx.select(
                                                AuditState.audit_periods,
                                                value=AuditState.period_filter,
                                                on_change=AuditState.period_filter.set,
                                            ),
                                            spacing="1",
                                        ),
                                        rx.vstack(
                                            rx.text("Company", size="2"),
                                            rx.select(
                                                AuditState.audit_companies,
                                                value=AuditState.company_filter,
                                                on_change=AuditState.company_filter.set,
                                            ),
                                            spacing="1",
                                        ),
                                        rx.vstack(
                                            rx.text("Date From", size="2"),
                                            rx.input(
                                                type="date",
                                                value=AuditState.date_from,
                                                on_change=AuditState.date_from.set,
                                            ),
                                            spacing="1",
                                        ),
                                        rx.vstack(
                                            rx.text("Date To", size="2"),
                                            rx.input(
                                                type="date",
                                                value=AuditState.date_to,
                                                on_change=AuditState.date_to.set,
                                            ),
                                            spacing="1",
                                        ),
                                        rx.button(
                                            "Apply Filters",
                                            on_click=AuditState.apply_filters,
                                            size="3",
                                        ),
                                        spacing="4",
                                        width="100%",
                                    ),
                                    spacing="3",
                                ),
                            ),
                            
                            # Stats
                            rx.grid(
                                rx.box(
                                    rx.vstack(
                                        rx.text("Modifications", size="2", color="#6c757d"),
                                        rx.text(AuditState.total_modifications, size="6", weight="bold"),
                                        spacing="2",
                                    ),
                                    bg="white",
                                    padding="1.5rem",
                                    border_radius="8px",
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.text("Time Sessions", size="2", color="#6c757d"),
                                        rx.text(AuditState.total_time_sessions, size="6", weight="bold"),
                                        spacing="2",
                                    ),
                                    bg="white",
                                    padding="1.5rem",
                                    border_radius="8px",
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.text("Total Hours", size="2", color="#6c757d"),
                                        rx.text(f"{AuditState.total_hours}h", size="6", weight="bold"),
                                        spacing="2",
                                    ),
                                    bg="white",
                                    padding="1.5rem",
                                    border_radius="8px",
                                ),
                                columns="3",
                                spacing="4",
                            ),
                            
                            # Tabs
                            rx.tabs.root(
                                rx.tabs.list(
                                    rx.tabs.trigger("Modifications", value="mods"),
                                    rx.tabs.trigger("Time Sessions", value="time"),
                                    rx.tabs.trigger("Time Reports", value="reports"),
                                ),
                                
                                # Modifications tab
                                rx.tabs.content(
                                    rx.vstack(
                                        rx.heading("Modification Log", size="6"),
                                        rx.cond(
                                            AuditState.modification_logs,
                                            rx.table.root(
                                                rx.table.header(
                                                    rx.table.row(
                                                        rx.table.column_header_cell("Timestamp"),
                                                        rx.table.column_header_cell("User"),
                                                        rx.table.column_header_cell("Matricule"),
                                                        rx.table.column_header_cell("Field"),
                                                        rx.table.column_header_cell("Old Value"),
                                                        rx.table.column_header_cell("New Value"),
                                                        rx.table.column_header_cell("Reason"),
                                                    ),
                                                ),
                                                rx.table.body(
                                                    rx.foreach(
                                                        AuditState.modification_logs,
                                                        modification_row,
                                                    ),
                                                ),
                                                width="100%",
                                            ),
                                            rx.text("No modifications found", color="#6c757d"),
                                        ),
                                        spacing="4",
                                        width="100%",
                                    ),
                                    value="mods",
                                ),
                                
                                # Time sessions tab
                                rx.tabs.content(
                                    rx.vstack(
                                        rx.heading("Time Tracking Sessions", size="6"),
                                        rx.cond(
                                            AuditState.time_logs,
                                            rx.table.root(
                                                rx.table.header(
                                                    rx.table.row(
                                                        rx.table.column_header_cell("Timestamp"),
                                                        rx.table.column_header_cell("User"),
                                                        rx.table.column_header_cell("Company"),
                                                        rx.table.column_header_cell("Period"),
                                                        rx.table.column_header_cell("Duration"),
                                                        rx.table.column_header_cell("Start"),
                                                        rx.table.column_header_cell("End"),
                                                    ),
                                                ),
                                                rx.table.body(
                                                    rx.foreach(
                                                        AuditState.time_logs,
                                                        time_session_row,
                                                    ),
                                                ),
                                                width="100%",
                                            ),
                                            rx.text("No time sessions found", color="#6c757d"),
                                        ),
                                        spacing="4",
                                        width="100%",
                                    ),
                                    value="time",
                                ),
                                
                                # Reports tab
                                rx.tabs.content(
                                    rx.vstack(
                                        rx.heading("Time by Company/Period", size="6"),
                                        rx.cond(
                                            AuditState.time_by_company,
                                            rx.table.root(
                                                rx.table.header(
                                                    rx.table.row(
                                                        rx.table.column_header_cell("Company"),
                                                        rx.table.column_header_cell("Period"),
                                                        rx.table.column_header_cell("Total Hours"),
                                                        rx.table.column_header_cell("Sessions"),
                                                    ),
                                                ),
                                                rx.table.body(
                                                    rx.foreach(
                                                        AuditState.time_by_company,
                                                        company_time_row,
                                                    ),
                                                ),
                                                width="100%",
                                            ),
                                            rx.text("No data", color="#6c757d"),
                                        ),
                                        
                                        rx.divider(),
                                        
                                        rx.heading("Time by User", size="6"),
                                        rx.cond(
                                            AuditState.time_by_user,
                                            rx.table.root(
                                                rx.table.header(
                                                    rx.table.row(
                                                        rx.table.column_header_cell("User"),
                                                        rx.table.column_header_cell("Total Hours"),
                                                        rx.table.column_header_cell("Sessions"),
                                                        rx.table.column_header_cell("Companies"),
                                                    ),
                                                ),
                                                rx.table.body(
                                                    rx.foreach(
                                                        AuditState.time_by_user,
                                                        user_time_row,
                                                    ),
                                                ),
                                                width="100%",
                                            ),
                                            rx.text("No data", color="#6c757d"),
                                        ),
                                        
                                        spacing="4",
                                        width="100%",
                                    ),
                                    value="reports",
                                ),
                                
                                default_value="mods",
                            ),
                            
                            spacing="5",
                            width="100%",
                        ),
                    ),
                    
                    spacing="5",
                    padding="2rem",
                    width="100%",
                ),
                flex="1",
            ),
            spacing="0",
            width="100%",
            align_items="start",
        ),
        on_mount=AuditState.load_audit_data,
    )