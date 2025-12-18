"""Dashboard page with payroll metrics and trends - Premium design."""
import reflex as rx
from typing import List, Dict
from ..state import GlobalState
from ..components import navbar, sidebar_nav
from ..design_tokens import (
    COLORS,
    GRADIENTS,
    SHADOWS,
    RADIUS,
    COMPONENT_SPACING,
    HEADING_XL,
    HEADING_MD,
    BODY_SM,
    LABEL,
)


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


def premium_metric_card(icon: str, label: str, value: str, color: str = "primary", delta: str = None) -> rx.Component:
    """Premium metric card with icon and optional delta."""
    color_map = {
        "primary": {"icon": COLORS["primary-600"], "value": COLORS["primary-900"]},
        "success": {"icon": COLORS["success-600"], "value": COLORS["success-600"]},
        "warning": {"icon": COLORS["warning-600"], "value": COLORS["warning-600"]},
        "info": {"icon": COLORS["info-600"], "value": COLORS["info-600"]},
    }
    colors = color_map.get(color, color_map["primary"])

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=24, color=colors["icon"], stroke_width=2),
                rx.cond(
                    delta,
                    rx.box(
                        rx.text(delta, size="1", weight="medium"),
                        bg=COLORS["success-100"],
                        color=COLORS["success-600"],
                        padding="0.25rem 0.5rem",
                        border_radius=RADIUS["md"],
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                justify="between",
                width="100%",
            ),
            rx.text(
                label,
                size=LABEL["size"],
                weight=LABEL["weight"],
                color=COLORS["neutral-500"],
                text_transform=LABEL["text_transform"],
                letter_spacing=LABEL["letter_spacing"],
            ),
            rx.text(
                value,
                size=HEADING_MD["size"],
                weight="bold",
                color=colors["value"],
                letter_spacing="-0.01em",
                font_variant_numeric="tabular-nums",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        background=GRADIENTS["subtle"],
        padding=COMPONENT_SPACING["card_padding"],
        border=f"1px solid {COLORS['neutral-200']}",
        border_radius=RADIUS["card"],
        box_shadow=SHADOWS["card"],
        transition="all 0.25s ease",
        _hover={
            "border_color": COLORS["primary-200"],
            "box_shadow": SHADOWS["card_hover"],
            "transform": "translateY(-2px)",
        },
    )


def index() -> rx.Component:
    """Premium dashboard page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    # Page header
                    rx.vstack(
                        rx.heading(
                            "Tableau de bord",
                            size=HEADING_XL["size"],
                            weight=HEADING_XL["weight"],
                            letter_spacing=HEADING_XL["letter_spacing"],
                            color=COLORS["primary-900"],
                        ),
                        rx.text(
                            "Vue d'ensemble de la paie mensuelle",
                            size=BODY_SM["size"],
                            color=COLORS["neutral-600"],
                        ),
                        spacing="2",
                        align="start",
                    ),

                    # Selection warning
                    rx.cond(
                        ~GlobalState.has_selection,
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-alert", size=20, color=COLORS["warning-600"]),
                                rx.text(
                                    "Sélectionnez d'abord une société et une période",
                                    size=BODY_SM["size"],
                                    color=COLORS["warning-600"],
                                ),
                                spacing="2",
                            ),
                            bg=COLORS["warning-100"],
                            border=f"1px solid {COLORS['warning-600']}",
                            border_radius=RADIUS["lg"],
                            padding="1rem",
                        ),
                        rx.fragment(),
                    ),

                    # Metrics grid
                    rx.grid(
                        premium_metric_card(
                            icon="users",
                            label="Employés",
                            value=DashboardState.employee_count,
                            color="primary",
                            delta=None,
                        ),
                        premium_metric_card(
                            icon="euro",
                            label="Masse salariale brute",
                            value=rx.cond(
                                DashboardState.total_brut > 0,
                                f"{DashboardState.total_brut:,.0f} €",
                                "0 €",
                            ),
                            color="primary",
                            delta="+2.3%",
                        ),
                        premium_metric_card(
                            icon="triangle-alert",
                            label="À vérifier",
                            value=DashboardState.edge_cases,
                            color="warning",
                            delta=None,
                        ),
                        premium_metric_card(
                            icon="circle-check",
                            label="Validés",
                            value=f"{DashboardState.validated}/{DashboardState.employee_count}",
                            color="success",
                            delta=DashboardState.validation_rate,
                        ),
                        columns="4",
                        spacing=COMPONENT_SPACING["grid_gap"],
                        width="100%",
                    ),

                    # Chart section
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.vstack(
                                    rx.heading(
                                        "Évolution des salaires",
                                        size=HEADING_MD["size"],
                                        weight="bold",
                                        color=COLORS["primary-900"],
                                    ),
                                    rx.text(
                                        "Tendances des 6 derniers mois",
                                        size=BODY_SM["size"],
                                        color=COLORS["neutral-600"],
                                    ),
                                    spacing="1",
                                    align="start",
                                ),
                                rx.spacer(),
                                rx.hstack(
                                    rx.box(
                                        rx.hstack(
                                            rx.box(
                                                width="12px",
                                                height="12px",
                                                bg=COLORS["primary-600"],
                                                border_radius=RADIUS["sm"],
                                            ),
                                            rx.text("Brut", size="1", color=COLORS["neutral-600"]),
                                            spacing="2",
                                        ),
                                    ),
                                    rx.box(
                                        rx.hstack(
                                            rx.box(
                                                width="12px",
                                                height="12px",
                                                bg=COLORS["success-600"],
                                                border_radius=RADIUS["sm"],
                                            ),
                                            rx.text("Net", size="1", color=COLORS["neutral-600"]),
                                            spacing="2",
                                        ),
                                    ),
                                    spacing="4",
                                ),
                                width="100%",
                                align="center",
                            ),

                            # Chart
                            rx.cond(
                                DashboardState.trend_data,
                                rx.box(
                                    rx.recharts.line_chart(
                                        rx.recharts.line(
                                            data_key="total_brut",
                                            stroke=COLORS["primary-600"],
                                            stroke_width=2,
                                        ),
                                        rx.recharts.line(
                                            data_key="total_net",
                                            stroke=COLORS["success-600"],
                                            stroke_width=2,
                                        ),
                                        rx.recharts.x_axis(
                                            data_key="period",
                                            style={"font_size": "12px", "fill": COLORS["neutral-600"]},
                                        ),
                                        rx.recharts.y_axis(
                                            style={"font_size": "12px", "fill": COLORS["neutral-600"]},
                                        ),
                                        rx.recharts.cartesian_grid(
                                            stroke_dasharray="3 3",
                                            stroke=COLORS["neutral-200"],
                                        ),
                                        data=DashboardState.trend_data,
                                        width="100%",
                                        height=400,
                                    ),
                                    padding_top="1rem",
                                ),
                                rx.center(
                                    rx.vstack(
                                        rx.icon("line-chart", size=48, color=COLORS["neutral-400"], stroke_width=1.5),
                                        rx.text(
                                            "Aucune donnée de tendance disponible",
                                            size=BODY_SM["size"],
                                            color=COLORS["neutral-600"],
                                        ),
                                        spacing="3",
                                    ),
                                    padding="4rem",
                                ),
                            ),

                            spacing="4",
                            width="100%",
                        ),
                        bg=COLORS["white"],
                        border=f"1px solid {COLORS['neutral-200']}",
                        border_radius=RADIUS["card"],
                        padding=COMPONENT_SPACING["card_padding_lg"],
                        box_shadow=SHADOWS["card"],
                    ),

                    spacing=COMPONENT_SPACING["section_gap"],
                    width="100%",
                ),
                flex="1",
                padding=COMPONENT_SPACING["page_padding"],
                min_height="calc(100vh - 64px)",
            ),
            spacing="0",
            width="100%",
            align_items="start",
        ),
        on_mount=DashboardState.load_dashboard_data,
    )
