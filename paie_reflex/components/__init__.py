"""Navigation components."""
from .navigation import navbar, sidebar_nav, metric_card
import reflex as rx

# Layout wrapper with navbar and sidebar
def layout(*children) -> rx.Component:
    """Standard page layout with navbar and sidebar."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                *children,
                flex="1",
                padding="2rem",
                width="100%",
            ),
            spacing="0",
            width="100%",
            align_items="start",
        ),
    )

# Info box for displaying messages
def info_box(title: str, message: str = "", icon: str = "info", color: str = "blue") -> rx.Component:
    """Display an info callout box."""
    return rx.callout(
        rx.vstack(
            rx.heading(title, size="4"),
            rx.text(message) if message else rx.fragment(),
            spacing="2",
        ),
        icon=icon,
        color_scheme=color,
    )

__all__ = ["navbar", "sidebar_nav", "metric_card", "layout", "info_box"]
