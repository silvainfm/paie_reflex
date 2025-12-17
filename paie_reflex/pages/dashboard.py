"""Dashboard page with payroll metrics and trends."""
import reflex as rx
from typing import List, Dict
from ..state import GlobalState
from ..components import navbar, sidebar_nav, metric_card


class DashboardState(GlobalState):
    """State for dashboard page."""
    
    employee_count: int = 0
    total_brut: float = 0
    edge_cases: int = 0
    validated: int = 0
    trend_data: List[Dict] = []
    
    def load_dashboard_data(self):
        """Load dashboard data."""
        # Mock data for MVP
        self.employee_count = 25
        self.total_brut = 87500.00
        self.edge_cases = 2
        self.validated = 23
        
        # Mock trend data (last 6 months)
        self.trend_data = [
            {"period": "07-2024", "total_brut": 85000, "total_net": 68000},
            {"period": "08-2024", "total_brut": 86000, "total_net": 68800},
            {"period": "09-2024", "total_brut": 85500, "total_net": 68400},
            {"period": "10-2024", "total_brut": 87000, "total_net": 69600},
            {"period": "11-2024", "total_brut": 86500, "total_net": 69200},
            {"period": "12-2024", "total_brut": 87500, "total_net": 70000},
        ]
    
    @rx.var
    def validation_rate(self) -> str:
        """Calculate validation rate."""
        if self.employee_count == 0:
            return "0%"
        return f"{(self.validated / self.employee_count * 100):.1f}%"


def index() -> rx.Component:
    """Dashboard page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    rx.heading("Dashboard", size="8", margin_bottom="1rem"),
                    
                    rx.cond(
                        ~GlobalState.has_selection,
                        rx.callout(
                            "Sélectionnez d'abord une société et une période",
                            icon="alert-circle",
                            color_scheme="red",
                        ),
                        rx.fragment(),
                    ),
                    
                    # Metrics grid
                    rx.grid(
                        rx.box(
                            rx.vstack(
                                rx.text("EMPLOYÉS", size="2", color="#6c757d", weight="medium"),
                                rx.text(DashboardState.employee_count, size="6", weight="bold"),
                                spacing="2",
                            ),
                            bg="white",
                            padding="1.5rem",
                            border_radius="8px",
                            box_shadow="0 2px 8px rgba(0,0,0,0.1)",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("MASSE SALARIALE BRUTE", size="2", color="#6c757d", weight="medium"),
                                rx.text(f"{DashboardState.total_brut:,.0f} €", size="6", weight="bold"),
                                spacing="2",
                            ),
                            bg="white",
                            padding="1.5rem",
                            border_radius="8px",
                            box_shadow="0 2px 8px rgba(0,0,0,0.1)",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("À VÉRIFIER", size="2", color="#6c757d", weight="medium"),
                                rx.text(DashboardState.edge_cases, size="6", weight="bold", color="orange"),
                                spacing="2",
                            ),
                            bg="white",
                            padding="1.5rem",
                            border_radius="8px",
                            box_shadow="0 2px 8px rgba(0,0,0,0.1)",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("VALIDÉS", size="2", color="#6c757d", weight="medium"),
                                rx.text(
                                    f"{DashboardState.validated}/{DashboardState.employee_count}",
                                    size="6",
                                    weight="bold",
                                    color="green",
                                ),
                                spacing="2",
                            ),
                            bg="white",
                            padding="1.5rem",
                            border_radius="8px",
                            box_shadow="0 2px 8px rgba(0,0,0,0.1)",
                        ),
                        columns="4",
                        spacing="4",
                    ),
                    
                    rx.divider(),

                    rx.heading("Évolution des salaires (6 mois)", size="6"),
                    
                    rx.cond(
                        DashboardState.trend_data,
                        rx.recharts.line_chart(
                            rx.recharts.line(
                                data_key="total_brut",
                                stroke="#2563eb",
                            ),
                            rx.recharts.line(
                                data_key="total_net",
                                stroke="#16a34a",
                            ),
                            rx.recharts.x_axis(data_key="period"),
                            rx.recharts.y_axis(),
                            rx.recharts.legend(),
                            data=DashboardState.trend_data,
                            width="100%",
                            height=300,
                        ),
                        rx.text("Aucune donnée de tendance disponible", color="#6c757d"),
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
        on_mount=DashboardState.load_dashboard_data,
    )
