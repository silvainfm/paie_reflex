"""Dashboard page with metrics and charts"""

import reflex as rx
from ..state import AuthState, CompanyState, DataState
from ..components import layout, metric_card
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from services.data_mgt import DataManager


class DashboardState(rx.State):
    """Dashboard state"""
    
    trend_data: list[dict] = []
    
    def load_trends(self):
        """Load salary trends"""
        company_state = self.get_state(CompanyState)
        
        if not company_state.current_company or not company_state.current_period:
            return
        
        month, year = map(int, company_state.current_period.split('-'))
        
        from services.shared_utils import load_salary_trend_data
        df = load_salary_trend_data(company_state.current_company, month, year, 6)
        
        if not df.is_empty():
            self.trend_data = df.to_dicts()


def page() -> rx.Component:
    """Dashboard page layout"""
    return layout(
        rx.vstack(
            rx.heading("📊 Tableau de bord", size="7"),
            
            # Metrics
            rx.hstack(
                metric_card(
                    "Employees",
                    str(DataState.summary.get('employee_count', 0)),
                ),
                metric_card(
                    "Total Brut",
                    f"{DataState.summary.get('total_brut', 0):,.0f} €",
                ),
                metric_card(
                    "Cases to verify",
                    str(DataState.summary.get('edge_cases', 0)),
                ),
                metric_card(
                    "Validated",
                    f"{DataState.summary.get('validated', 0)}/{DataState.summary.get('employee_count', 0)}",
                ),
                spacing="4",
                width="100%",
            ),
            
            rx.divider(),
            
            rx.heading("Salary Evolution (6 months)", size="5"),
            
            rx.button(
                "Load Trends",
                on_click=DashboardState.load_trends,
                size="2",
            ),
            
            rx.cond(
                len(DashboardState.trend_data) > 0,
                rx.recharts.line_chart(
                    rx.recharts.line(
                        data_key="total_brut",
                        stroke="#8884d8",
                    ),
                    rx.recharts.x_axis(data_key="period"),
                    rx.recharts.y_axis(),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                    rx.recharts.tooltip(),
                    data=DashboardState.trend_data,
                    width="100%",
                    height=300,
                ),
                rx.text("No trend data available", color="gray"),
            ),
            
            rx.divider(),
            
            rx.heading("Edge Cases", size="5"),
            
            rx.cond(
                DataState.summary.get('edge_cases', 0) > 0,
                rx.vstack(
                    rx.foreach(
                        DataState.edge_cases,
                        lambda e: rx.box(
                            rx.hstack(
                                rx.text(
                                    f"{e.get('nom', '')} {e.get('prenom', '')}",
                                    weight="bold",
                                ),
                                rx.text(e.get('matricule', ''), color="gray"),
                                rx.spacer(),
                                rx.text(
                                    f"{e.get('salaire_brut', 0):,.2f} €",
                                    size="2",
                                ),
                                width="100%",
                            ),
                            padding="1rem",
                            bg="white",
                            border_radius="0.5rem",
                            margin_bottom="0.5rem",
                        ),
                    ),
                    width="100%",
                ),
                rx.text("No edge cases detected ✅", color="green"),
            ),
            
            spacing="6",
            width="100%",
            on_mount=DataState.load_period_data,
        ),
        AuthState,
    )
