"""Navigation components - Premium design."""
import reflex as rx
from ..state import GlobalState
from ..design_tokens import (
    COLORS,
    GRADIENTS,
    SHADOWS,
    RADIUS,
    TRANSITIONS,
    COMPONENT_SPACING,
    Z_INDEX,
    HEADING_LG,
    LABEL,
)


def navbar() -> rx.Component:
    """Premium navigation bar with glass morphism effect."""
    return rx.box(
        rx.hstack(
            # Logo with gradient text
            rx.heading(
                "Monaco Paie",
                size=HEADING_LG["size"],
                weight=HEADING_LG["weight"],
                letter_spacing=HEADING_LG["letter_spacing"],
                background=GRADIENTS["primary"],
                background_clip="text",
                style={
                    "-webkit-background-clip": "text",
                    "-webkit-text-fill-color": "transparent",
                },
            ),

            rx.spacer(),

            # Company selector
            rx.vstack(
                rx.text(
                    "Société",
                    size=LABEL["size"],
                    weight=LABEL["weight"],
                    color=COLORS["neutral-500"],
                    text_transform=LABEL["text_transform"],
                    letter_spacing=LABEL["letter_spacing"],
                ),
                rx.select(
                    GlobalState.available_companies,
                    value=GlobalState.current_company,
                    on_change=GlobalState.set_company,
                    placeholder="Sélectionner",
                    size="2",
                    style={
                        "bg": COLORS["white"],
                        "border": f"1px solid {COLORS['neutral-200']}",
                        "border_radius": RADIUS["lg"],
                        "padding": "0.625rem 1rem",
                        "_hover": {"border_color": COLORS["primary-300"]},
                        "_focus": {
                            "border_color": COLORS["primary-500"],
                            "box_shadow": SHADOWS["focus_ring"],
                        },
                    },
                ),
                spacing="2",
                align="start",
            ),

            # Period selector
            rx.vstack(
                rx.text(
                    "Période",
                    size=LABEL["size"],
                    weight=LABEL["weight"],
                    color=COLORS["neutral-500"],
                    text_transform=LABEL["text_transform"],
                    letter_spacing=LABEL["letter_spacing"],
                ),
                rx.select(
                    GlobalState.available_periods,
                    value=GlobalState.current_period,
                    on_change=GlobalState.set_period,
                    placeholder="MM-YYYY",
                    size="2",
                    style={
                        "bg": COLORS["white"],
                        "border": f"1px solid {COLORS['neutral-200']}",
                        "border_radius": RADIUS["lg"],
                        "padding": "0.625rem 1rem",
                        "_hover": {"border_color": COLORS["primary-300"]},
                        "_focus": {
                            "border_color": COLORS["primary-500"],
                            "box_shadow": SHADOWS["focus_ring"],
                        },
                    },
                ),
                spacing="2",
                align="start",
            ),

            rx.spacer(),

            # User info and logout
            rx.hstack(
                rx.text(
                    GlobalState.user,
                    size="2",
                    weight="medium",
                    color=COLORS["neutral-700"],
                ),
                rx.box(
                    rx.text(
                        GlobalState.role,
                        size="1",
                        weight="medium",
                    ),
                    bg=COLORS["primary-50"],
                    color=COLORS["primary-700"],
                    border=f"1px solid {COLORS['primary-200']}",
                    border_radius=RADIUS["badge"],
                    padding="0.375rem 0.75rem",
                ),
                rx.button(
                    "Déconnexion",
                    on_click=GlobalState.logout,
                    variant="ghost",
                    size="2",
                    style={
                        "color": COLORS["neutral-600"],
                        "_hover": {
                            "bg": COLORS["neutral-100"],
                            "color": COLORS["neutral-900"],
                        },
                    },
                ),
                spacing="3",
                align="center",
            ),

            spacing="6",
            align="center",
            width="100%",
        ),
        background=GRADIENTS["glass"],
        backdrop_filter="blur(12px)",
        padding=COMPONENT_SPACING["navbar_padding"],
        border_bottom=f"1px solid rgba(228, 228, 231, 0.6)",
        box_shadow=SHADOWS["navbar"],
        position="sticky",
        top="0",
        z_index=Z_INDEX["navbar"],
    )


def sidebar_nav() -> rx.Component:
    """Premium sidebar navigation with active state."""
    nav_items = [
        ("Accueil", "/", "home"),
        ("Import", "/import", "upload"),
        ("Traitement", "/processing", "cpu"),
        ("Validation", "/validation", "circle-check"),
        ("Tableau de bord", "/dashboard", "bar-chart-2"),
        ("PDF", "/pdf", "file-text"),
        ("Export", "/export", "download"),
        ("Portail Client", "/client-portal", "users"),
        ("Configuration", "/config", "settings"),
    ]

    return rx.box(
        rx.vstack(
            *[
                rx.link(
                    rx.hstack(
                        rx.icon(icon, size=20, stroke_width=2, color=COLORS["neutral-600"]),
                        rx.text(
                            label,
                            size="2",
                            weight="regular",
                            color=COLORS["neutral-600"],
                        ),
                        spacing="3",
                        width="100%",
                        padding="0.75rem 1rem",
                        border_radius=RADIUS["lg"],
                        transition=TRANSITIONS["base"],
                        _hover={
                            "bg": COLORS["white"],
                            "color": COLORS["neutral-900"],
                            "box_shadow": SHADOWS["xs"],
                        },
                    ),
                    href=route,
                    width="100%",
                    text_decoration="none",
                )
                for label, route, icon in nav_items
            ],
            spacing="2",
            width="100%",
            padding_top="1rem",
        ),
        width="200px",
        padding=COMPONENT_SPACING["sidebar_padding"],
        bg=COLORS["neutral-50"],
        border_right=f"1px solid {COLORS['neutral-200']}",
        height="calc(100vh - 64px)",
    )


def metric_card(label: str, value: str, delta: str = None) -> rx.Component:
    """Premium metric card with gradient background and hover effect."""
    return rx.box(
        rx.vstack(
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
                size=HEADING_LG["size"],
                weight=HEADING_LG["weight"],
                color=COLORS["primary-900"],
                letter_spacing=HEADING_LG["letter_spacing"],
                font_variant_numeric="tabular-nums",
            ),
            rx.cond(
                delta,
                rx.text(
                    delta,
                    size="1",
                    color=COLORS["success-600"],
                    weight="medium",
                ),
                rx.fragment(),
            ),
            spacing="2",
            align="start",
        ),
        background=GRADIENTS["subtle"],
        padding=COMPONENT_SPACING["card_padding"],
        border=f"1px solid {COLORS['neutral-200']}",
        border_radius=RADIUS["card"],
        box_shadow=SHADOWS["card"],
        transition=TRANSITIONS["base"],
        _hover={
            "border_color": COLORS["primary-200"],
            "box_shadow": SHADOWS["card_hover"],
            "transform": "translateY(-2px)",
        },
    )
