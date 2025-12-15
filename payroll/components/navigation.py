"""Navigation bar component."""
import reflex as rx
from ..state import GlobalState


def navbar() -> rx.Component:
    """Create navigation bar with company/period selectors."""
    return rx.box(
        rx.hstack(
            # Logo/Title
            rx.heading("Monaco Payroll", size="7", weight="bold"),
            
            rx.spacer(),
            
            # Company selector
            rx.vstack(
                rx.text("Company", size="1", weight="medium"),
                rx.select(
                    GlobalState.available_companies,
                    value=GlobalState.current_company,
                    on_change=GlobalState.set_company,
                    placeholder="Select company",
                ),
                spacing="1",
                align="start",
            ),
            
            # Period selector
            rx.vstack(
                rx.text("Period", size="1", weight="medium"),
                rx.select(
                    GlobalState.available_periods,
                    value=GlobalState.current_period,
                    on_change=GlobalState.set_period,
                    placeholder="MM-YYYY",
                ),
                spacing="1",
                align="start",
            ),
            
            rx.spacer(),
            
            # User info and logout
            rx.hstack(
                rx.text(GlobalState.name, weight="medium"),
                rx.badge(GlobalState.role, color_scheme="blue"),
                rx.button(
                    "Logout",
                    on_click=GlobalState.logout,
                    variant="soft",
                ),
                spacing="3",
            ),
            
            spacing="5",
            align="center",
            width="100%",
        ),
        bg="white",
        padding="1rem",
        border_bottom="1px solid #e5e7eb",
        position="sticky",
        top="0",
        z_index="10",
    )


def sidebar_nav() -> rx.Component:
    """Create sidebar navigation."""
    nav_items = [
        ("Home", "/", "home"),
        ("Import", "/import", "upload"),
        ("Processing", "/processing", "settings"),
        ("Validation", "/validation", "check-circle"),
        ("Dashboard", "/dashboard", "bar-chart-2"),
        ("PDFs", "/pdf", "file-text"),
        ("Export", "/export", "download"),
        ("Config", "/config", "settings"),
    ]
    
    return rx.box(
        rx.vstack(
            *[
                rx.link(
                    rx.hstack(
                        rx.icon(icon),
                        rx.text(label, size="3"),
                        spacing="3",
                        width="100%",
                        padding="0.75rem",
                        border_radius="8px",
                        _hover={"bg": "#f3f4f6"},
                    ),
                    href=route,
                    width="100%",
                )
                for label, route, icon in nav_items
            ],
            spacing="2",
            width="100%",
        ),
        width="240px",
        padding="1rem",
        bg="white",
        border_right="1px solid #e5e7eb",
        height="calc(100vh - 64px)",
    )


def metric_card(label: str, value: str, delta: str = None) -> rx.Component:
    """Create a metric card."""
    return rx.box(
        rx.vstack(
            rx.text(label, size="2", color="#6c757d", weight="medium"),
            rx.text(value, size="6", weight="bold", color="#2c3e50"),
            rx.cond(
                delta,
                rx.text(delta, size="2", color="#28a745"),
                rx.fragment(),
            ),
            spacing="2",
            align="start",
        ),
        bg="white",
        padding="1.5rem",
        border_radius="8px",
        box_shadow="0 2px 8px rgba(0,0,0,0.1)",
    )
