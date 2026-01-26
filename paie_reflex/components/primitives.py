"""
Primitive UI components following the Monaco Paie design system.
Reusable base components with consistent styling.
"""

import reflex as rx
from typing import Optional, List, Dict, Any
from ..design_tokens import (
    COLORS,
    GRADIENTS,
    SHADOWS,
    RADIUS,
    TRANSITIONS,
    COMPONENT_SPACING,
    CARD_STYLE,
    CARD_HOVER_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    BUTTON_GHOST_STYLE,
    INPUT_STYLE,
    BADGE_SUCCESS_STYLE,
    BADGE_WARNING_STYLE,
    BADGE_ERROR_STYLE,
    BADGE_INFO_STYLE,
    HEADING_XL,
    HEADING_LG,
    HEADING_MD,
    BODY_MD,
    BODY_SM,
    BODY_XS,
    LABEL,
)


def card(*children, clickable: bool = False, **kwargs) -> rx.Component:
    """
    Premium card component with consistent styling.

    Args:
        *children: Child components
        clickable: If True, adds hover effects
        **kwargs: Additional props to pass to rx.box
    """
    style = CARD_HOVER_STYLE if clickable else CARD_STYLE
    return rx.box(*children, **{**style, **kwargs})


def metric_card(label: str, value: str, icon: Optional[str] = None, delta: Optional[str] = None) -> rx.Component:
    """
    Metric display card with gradient background and hover effect.

    Args:
        label: Metric label (e.g., "Total Employees")
        value: Metric value (e.g., "324")
        icon: Optional icon name
        delta: Optional delta indicator (e.g., "+5.2%")
    """
    return rx.box(
        rx.vstack(
            # Icon + Label row
            rx.hstack(
                rx.cond(
                    icon,
                    rx.icon(icon, size=20, color=COLORS["primary-600"], stroke_width=2),
                    rx.fragment(),
                ),
                rx.text(
                    label,
                    size=BODY_XS["size"],
                    weight=LABEL["weight"],
                    color=COLORS["neutral-500"],
                    text_transform=LABEL["text_transform"],
                    letter_spacing=LABEL["letter_spacing"],
                ),
                spacing="2",
                align="center",
            ),
            # Value
            rx.text(
                value,
                size=HEADING_LG["size"],
                weight=HEADING_LG["weight"],
                color=COLORS["primary-900"],
                letter_spacing=HEADING_LG["letter_spacing"],
                font_variant_numeric="tabular-nums",
            ),
            # Delta (if provided)
            rx.cond(
                delta,
                rx.text(
                    delta,
                    size=BODY_XS["size"],
                    weight=BODY_XS["weight"],
                    color=COLORS["success-600"],
                ),
                rx.fragment(),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        bg=GRADIENTS["subtle"],
        border=f"1px solid {COLORS['neutral-200']}",
        border_radius=RADIUS["card"],
        padding=COMPONENT_SPACING["card_padding"],
        box_shadow=SHADOWS["card"],
        transition=TRANSITIONS["base"],
        _hover={
            "border_color": COLORS["primary-200"],
            "box_shadow": SHADOWS["card_hover"],
            "transform": "translateY(-2px)",
        },
    )


def button_primary(text: str, **kwargs) -> rx.Component:
    """Primary action button with blue background."""
    return rx.button(
        text,
        **{**BUTTON_PRIMARY_STYLE, **kwargs}
    )


def button_secondary(text: str, **kwargs) -> rx.Component:
    """Secondary action button with white background and blue border."""
    return rx.button(
        text,
        **{**BUTTON_SECONDARY_STYLE, **kwargs}
    )


def button_ghost(text: str, **kwargs) -> rx.Component:
    """Ghost button with transparent background."""
    return rx.button(
        text,
        **{**BUTTON_GHOST_STYLE, **kwargs}
    )


def text_input(
    placeholder: str = "",
    name: str = "",
    value: str = "",
    **kwargs
) -> rx.Component:
    """Styled text input with focus ring."""
    return rx.input(
        placeholder=placeholder,
        name=name,
        value=value,
        **{**INPUT_STYLE, **kwargs}
    )


def status_badge(
    text: str,
    variant: str = "success"
) -> rx.Component:
    """
    Status badge component.

    Args:
        text: Badge text
        variant: "success" | "warning" | "error" | "info"
    """
    style_map = {
        "success": BADGE_SUCCESS_STYLE,
        "warning": BADGE_WARNING_STYLE,
        "error": BADGE_ERROR_STYLE,
        "info": BADGE_INFO_STYLE,
    }

    style = style_map.get(variant, BADGE_SUCCESS_STYLE)

    return rx.box(
        rx.text(text, size="1", weight="medium"),
        **style
    )


def info_card(
    title: str,
    description: str,
    icon: str,
    variant: str = "info"
) -> rx.Component:
    """
    Informational card with icon and content.

    Args:
        title: Card title
        description: Card description
        icon: Icon name
        variant: "info" | "warning" | "error" | "success"
    """
    color_map = {
        "info": {"bg": COLORS["info-100"], "border": COLORS["info-600"], "icon": COLORS["info-600"]},
        "warning": {"bg": COLORS["warning-100"], "border": COLORS["warning-600"], "icon": COLORS["warning-600"]},
        "error": {"bg": COLORS["error-100"], "border": COLORS["error-600"], "icon": COLORS["error-600"]},
        "success": {"bg": COLORS["success-100"], "border": COLORS["success-600"], "icon": COLORS["success-600"]},
    }

    colors = color_map.get(variant, color_map["info"])

    return rx.box(
        rx.hstack(
            rx.icon(icon, size=24, color=colors["icon"], stroke_width=2),
            rx.vstack(
                rx.text(
                    title,
                    size=BODY_MD["size"],
                    weight="bold",
                    color=COLORS["neutral-900"],
                ),
                rx.text(
                    description,
                    size=BODY_SM["size"],
                    color=COLORS["neutral-700"],
                    line_height="1.5",
                ),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="start",
        ),
        bg=colors["bg"],
        border=f"1px solid {colors['border']}",
        border_radius=RADIUS["lg"],
        padding=COMPONENT_SPACING["card_padding"],
    )


def section_heading(text: str, **kwargs) -> rx.Component:
    """Section heading with consistent styling."""
    return rx.heading(
        text,
        size=HEADING_MD["size"],
        weight=HEADING_MD["weight"],
        color=COLORS["primary-900"],
        letter_spacing=HEADING_MD["letter_spacing"],
        **kwargs
    )


def page_heading(text: str, subtitle: Optional[str] = None) -> rx.Component:
    """Page heading with optional subtitle."""
    return rx.vstack(
        rx.heading(
            text,
            size=HEADING_XL["size"],
            weight=HEADING_XL["weight"],
            color=COLORS["primary-900"],
            letter_spacing=HEADING_XL["letter_spacing"],
        ),
        rx.cond(
            subtitle,
            rx.text(
                subtitle,
                size=BODY_MD["size"],
                color=COLORS["neutral-600"],
                line_height="1.6",
            ),
            rx.fragment(),
        ),
        spacing="2",
        align="start",
    )


def label_text(text: str, **kwargs) -> rx.Component:
    """Form label with uppercase styling."""
    return rx.text(
        text,
        size=LABEL["size"],
        weight=LABEL["weight"],
        color=COLORS["neutral-500"],
        text_transform=LABEL["text_transform"],
        letter_spacing=LABEL["letter_spacing"],
        **kwargs
    )


def divider() -> rx.Component:
    """Horizontal divider."""
    return rx.divider(
        border_color=COLORS["neutral-200"],
        margin="1.5rem 0",
    )


def loading_spinner(text: str = "Chargement...") -> rx.Component:
    """Loading spinner with text."""
    return rx.center(
        rx.vstack(
            rx.spinner(
                size="3",
                color=COLORS["primary-600"],
            ),
            rx.text(
                text,
                size=BODY_SM["size"],
                color=COLORS["neutral-600"],
            ),
            spacing="3",
            align="center",
        ),
        padding=COMPONENT_SPACING["page_padding"],
    )


def empty_state(
    icon: str,
    title: str,
    description: str,
    action_text: Optional[str] = None,
    on_click: Optional[Any] = None
) -> rx.Component:
    """
    Empty state component for when there's no data.

    Args:
        icon: Icon name
        title: Empty state title
        description: Empty state description
        action_text: Optional action button text
        on_click: Optional action button click handler
    """
    return rx.center(
        rx.vstack(
            rx.icon(
                icon,
                size=48,
                color=COLORS["neutral-400"],
                stroke_width=1.5,
            ),
            rx.text(
                title,
                size=HEADING_MD["size"],
                weight="bold",
                color=COLORS["neutral-900"],
            ),
            rx.text(
                description,
                size=BODY_SM["size"],
                color=COLORS["neutral-600"],
                text_align="center",
                max_width="400px",
            ),
            rx.cond(
                action_text and on_click,
                button_primary(action_text, on_click=on_click),
                rx.fragment(),
            ),
            spacing="4",
            align="center",
        ),
        padding=COMPONENT_SPACING["page_padding"],
    )
