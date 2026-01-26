"""Components for Monaco Paie - Premium design system."""
from .navigation import navbar, sidebar_nav, metric_card
from .primitives import (
    card,
    metric_card as premium_metric_card,
    button_primary,
    button_secondary,
    button_ghost,
    text_input,
    status_badge,
    info_card,
    section_heading,
    page_heading,
    label_text,
    divider,
    loading_spinner,
    empty_state,
)
import reflex as rx
from ..design_tokens import COMPONENT_SPACING, COLORS

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
                padding=COMPONENT_SPACING["page_padding"],
                width="100%",
                min_height="calc(100vh - 64px)",
            ),
            spacing="0",
            width="100%",
            align_items="start",
        ),
    )

# Info box for displaying messages (legacy, prefer info_card from primitives)
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

__all__ = [
    "navbar",
    "sidebar_nav",
    "metric_card",
    "layout",
    "info_box",
    # Primitives
    "card",
    "premium_metric_card",
    "button_primary",
    "button_secondary",
    "button_ghost",
    "text_input",
    "status_badge",
    "info_card",
    "section_heading",
    "page_heading",
    "label_text",
    "divider",
    "loading_spinner",
    "empty_state",
]
