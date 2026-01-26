"""Home and login pages - Premium design."""
import reflex as rx
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
    BODY_MD,
    BODY_SM,
    LABEL,
)


def login() -> rx.Component:
    """Premium login page with gradient background."""
    return rx.center(
        rx.box(
            rx.vstack(
                # Premium logo with gradient
                rx.heading(
                    "Monaco Paie",
                    size="9",
                    weight="bold",
                    letter_spacing="-0.03em",
                    background=GRADIENTS["primary"],
                    background_clip="text",
                    style={
                        "-webkit-background-clip": "text",
                        "-webkit-text-fill-color": "transparent",
                    },
                ),
                rx.text(
                    "Connectez-vous pour continuer",
                    size=BODY_MD["size"],
                    color=COLORS["neutral-600"],
                    weight="regular",
                ),

                # Premium form
                rx.form(
                    rx.vstack(
                        rx.input(
                            placeholder="Nom d'utilisateur",
                            name="username",
                            required=True,
                            size="3",
                            style={
                                "bg": COLORS["white"],
                                "border": f"1px solid {COLORS['neutral-300']}",
                                "border_radius": RADIUS["lg"],
                                "padding": "0.75rem 1rem",
                                "_focus": {
                                    "border_color": COLORS["primary-500"],
                                    "box_shadow": SHADOWS["focus_ring"],
                                },
                            },
                        ),
                        rx.input(
                            placeholder="Mot de passe",
                            name="password",
                            type="password",
                            required=True,
                            size="3",
                            style={
                                "bg": COLORS["white"],
                                "border": f"1px solid {COLORS['neutral-300']}",
                                "border_radius": RADIUS["lg"],
                                "padding": "0.75rem 1rem",
                                "_focus": {
                                    "border_color": COLORS["primary-500"],
                                    "box_shadow": SHADOWS["focus_ring"],
                                },
                            },
                        ),
                        rx.button(
                            "Se connecter",
                            type="submit",
                            width="100%",
                            size="3",
                            style={
                                "bg": COLORS["primary-600"],
                                "color": COLORS["white"],
                                "border": "none",
                                "border_radius": RADIUS["lg"],
                                "padding": "0.75rem 1.5rem",
                                "font_weight": "500",
                                "box_shadow": SHADOWS["button"],
                                "transition": "all 0.2s ease",
                                "cursor": "pointer",
                                "_hover": {
                                    "bg": COLORS["primary-700"],
                                    "box_shadow": SHADOWS["button_hover"],
                                    "transform": "translateY(-1px)",
                                },
                            },
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    on_submit=GlobalState.login,
                    width="100%",
                ),

                # Error message
                rx.cond(
                    GlobalState.login_error,
                    rx.box(
                        rx.hstack(
                            rx.icon("circle-alert", size=20, color=COLORS["error-600"]),
                            rx.text(
                                GlobalState.login_error,
                                size="2",
                                color=COLORS["error-600"],
                            ),
                            spacing="2",
                        ),
                        bg=COLORS["error-100"],
                        border=f"1px solid {COLORS['error-600']}",
                        border_radius=RADIUS["lg"],
                        padding="0.75rem 1rem",
                    ),
                    rx.fragment(),
                ),

                spacing="6",
                width="100%",
            ),
            padding="3rem",
            bg=COLORS["white"],
            border=f"1px solid {COLORS['neutral-200']}",
            border_radius=RADIUS["2xl"],
            box_shadow=SHADOWS["2xl"],
            max_width="420px",
            width="100%",
        ),
        height="100vh",
        background=GRADIENTS["page-bg"],
    )


def index() -> rx.Component:
    """Premium home page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    # Premium header
                    rx.vstack(
                        rx.heading(
                            "Système de paie Monaco",
                            size=HEADING_XL["size"],
                            weight=HEADING_XL["weight"],
                            letter_spacing=HEADING_XL["letter_spacing"],
                            color=COLORS["primary-900"],
                        ),
                        rx.text(
                            "Traitement moderne de la paie pour les entreprises monégasques",
                            size=BODY_MD["size"],
                            color=COLORS["neutral-600"],
                            line_height="1.6",
                        ),
                        spacing="3",
                        align="start",
                    ),

                    # Current selection cards
                    rx.cond(
                        GlobalState.has_selection,
                        rx.vstack(
                            rx.text(
                                "Sélection actuelle",
                                size=BODY_SM["size"],
                                weight="medium",
                                color=COLORS["neutral-500"],
                                text_transform=LABEL["text_transform"],
                                letter_spacing=LABEL["letter_spacing"],
                            ),
                            rx.hstack(
                                # Company card
                                rx.box(
                                    rx.hstack(
                                        rx.icon("building-2", size=24, color=COLORS["primary-600"], stroke_width=2),
                                        rx.vstack(
                                            rx.text(
                                                "Société",
                                                size=LABEL["size"],
                                                color=COLORS["neutral-500"],
                                                text_transform=LABEL["text_transform"],
                                                letter_spacing=LABEL["letter_spacing"],
                                            ),
                                            rx.text(
                                                GlobalState.current_company,
                                                size="4",
                                                weight="bold",
                                                color=COLORS["primary-900"],
                                            ),
                                            spacing="1",
                                            align="start",
                                        ),
                                        spacing="3",
                                        align="center",
                                    ),
                                    padding=COMPONENT_SPACING["card_padding"],
                                    bg=COLORS["white"],
                                    border=f"1px solid {COLORS['neutral-200']}",
                                    border_radius=RADIUS["card"],
                                    box_shadow=SHADOWS["card"],
                                    flex="1",
                                ),
                                # Period card
                                rx.box(
                                    rx.hstack(
                                        rx.icon("calendar", size=24, color=COLORS["primary-600"], stroke_width=2),
                                        rx.vstack(
                                            rx.text(
                                                "Période",
                                                size=LABEL["size"],
                                                color=COLORS["neutral-500"],
                                                text_transform=LABEL["text_transform"],
                                                letter_spacing=LABEL["letter_spacing"],
                                            ),
                                            rx.text(
                                                GlobalState.current_period,
                                                size="4",
                                                weight="bold",
                                                color=COLORS["primary-900"],
                                            ),
                                            spacing="1",
                                            align="start",
                                        ),
                                        spacing="3",
                                        align="center",
                                    ),
                                    padding=COMPONENT_SPACING["card_padding"],
                                    bg=COLORS["white"],
                                    border=f"1px solid {COLORS['neutral-200']}",
                                    border_radius=RADIUS["card"],
                                    box_shadow=SHADOWS["card"],
                                    flex="1",
                                ),
                                spacing=COMPONENT_SPACING["grid_gap"],
                                width="100%",
                            ),
                            spacing="3",
                        ),
                        # No selection callout
                        rx.box(
                            rx.hstack(
                                rx.icon("info", size=20, color=COLORS["info-600"]),
                                rx.text(
                                    "Veuillez sélectionner une société et une période pour continuer",
                                    size=BODY_SM["size"],
                                    color=COLORS["info-600"],
                                ),
                                spacing="2",
                            ),
                            bg=COLORS["info-100"],
                            border=f"1px solid {COLORS['info-600']}",
                            border_radius=RADIUS["lg"],
                            padding="1rem",
                        ),
                    ),

                    # Quick actions grid
                    rx.vstack(
                        rx.text(
                            "Actions rapides",
                            size=BODY_SM["size"],
                            weight="medium",
                            color=COLORS["neutral-500"],
                            text_transform=LABEL["text_transform"],
                            letter_spacing=LABEL["letter_spacing"],
                        ),
                        rx.grid(
                            # Import card
                            rx.link(
                                rx.box(
                                    rx.vstack(
                                        rx.icon("upload", size=24, stroke_width=2, color=COLORS["primary-600"]),
                                        rx.text(
                                            "Import",
                                            size=HEADING_MD["size"],
                                            weight="bold",
                                            color=COLORS["primary-900"],
                                        ),
                                        rx.text(
                                            "Fichiers Excel/CSV",
                                            size=BODY_SM["size"],
                                            color=COLORS["neutral-600"],
                                        ),
                                        spacing="3",
                                        align="center",
                                    ),
                                    padding=COMPONENT_SPACING["card_padding"],
                                    bg=COLORS["white"],
                                    border=f"1px solid {COLORS['neutral-200']}",
                                    border_radius=RADIUS["card"],
                                    box_shadow=SHADOWS["card"],
                                    min_height="180px",
                                    display="flex",
                                    align_items="center",
                                    justify_content="center",
                                    transition="all 0.25s ease",
                                    cursor="pointer",
                                    _hover={
                                        "border_color": COLORS["primary-300"],
                                        "box_shadow": f"0 8px 24px {COLORS['primary-300']}40",
                                        "transform": "translateY(-4px)",
                                    },
                                ),
                                href="/import",
                                text_decoration="none",
                            ),
                            # Processing card
                            rx.link(
                                rx.box(
                                    rx.vstack(
                                        rx.icon("cpu", size=24, stroke_width=2, color=COLORS["primary-600"]),
                                        rx.text(
                                            "Traitement",
                                            size=HEADING_MD["size"],
                                            weight="bold",
                                            color=COLORS["primary-900"],
                                        ),
                                        rx.text(
                                            "Calculer salaires",
                                            size=BODY_SM["size"],
                                            color=COLORS["neutral-600"],
                                        ),
                                        spacing="3",
                                        align="center",
                                    ),
                                    padding=COMPONENT_SPACING["card_padding"],
                                    bg=COLORS["white"],
                                    border=f"1px solid {COLORS['neutral-200']}",
                                    border_radius=RADIUS["card"],
                                    box_shadow=SHADOWS["card"],
                                    min_height="180px",
                                    display="flex",
                                    align_items="center",
                                    justify_content="center",
                                    transition="all 0.25s ease",
                                    cursor="pointer",
                                    _hover={
                                        "border_color": COLORS["primary-300"],
                                        "box_shadow": f"0 8px 24px {COLORS['primary-300']}40",
                                        "transform": "translateY(-4px)",
                                    },
                                ),
                                href="/processing",
                                text_decoration="none",
                            ),
                            # Dashboard card
                            rx.link(
                                rx.box(
                                    rx.vstack(
                                        rx.icon("bar-chart-2", size=24, stroke_width=2, color=COLORS["primary-600"]),
                                        rx.text(
                                            "Tableau de bord",
                                            size=HEADING_MD["size"],
                                            weight="bold",
                                            color=COLORS["primary-900"],
                                        ),
                                        rx.text(
                                            "Voir rapports",
                                            size=BODY_SM["size"],
                                            color=COLORS["neutral-600"],
                                        ),
                                        spacing="3",
                                        align="center",
                                    ),
                                    padding=COMPONENT_SPACING["card_padding"],
                                    bg=COLORS["white"],
                                    border=f"1px solid {COLORS['neutral-200']}",
                                    border_radius=RADIUS["card"],
                                    box_shadow=SHADOWS["card"],
                                    min_height="180px",
                                    display="flex",
                                    align_items="center",
                                    justify_content="center",
                                    transition="all 0.25s ease",
                                    cursor="pointer",
                                    _hover={
                                        "border_color": COLORS["primary-300"],
                                        "box_shadow": f"0 8px 24px {COLORS['primary-300']}40",
                                        "transform": "translateY(-4px)",
                                    },
                                ),
                                href="/dashboard",
                                text_decoration="none",
                            ),
                            columns="3",
                            spacing=COMPONENT_SPACING["grid_gap"],
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
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
        on_mount=GlobalState.load_companies,
    )
