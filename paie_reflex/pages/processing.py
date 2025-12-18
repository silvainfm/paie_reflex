"""Processing page for payroll calculations - Premium design."""
import reflex as rx
from ..state import GlobalState
from ..components import navbar, sidebar_nav
from ..design_tokens import (
    COLORS,
    SHADOWS,
    RADIUS,
    COMPONENT_SPACING,
    HEADING_XL,
    HEADING_MD,
    BODY_MD,
    BODY_SM,
    LABEL,
)


class ProcessingState(GlobalState):
    """State for processing page."""

    processing_status: str = "idle"  # idle, running, success, error
    processing_message: str = ""
    enable_agent: bool = True
    processed_count: int = 0
    validated_count: int = 0
    edge_cases: int = 0

    # Agent results
    automatic_mods: int = 0
    flagged_cases: int = 0
    anomalies_detected: int = 0

    def start_processing(self):
        """Start payroll processing."""
        if not self.has_selection:
            self.processing_message = "Sélectionnez d'abord une société et une période"
            self.processing_status = "error"
            return

        self.processing_status = "running"
        self.processing_message = "Traitement de la paie en cours..."

        try:
            # Implement processing logic
            # system.process_monthly_payroll(company, period)

            # Mock results for MVP
            self.processed_count = 25
            self.validated_count = 23
            self.edge_cases = 2

            if self.enable_agent:
                self.automatic_mods = 3
                self.flagged_cases = 2
                self.anomalies_detected = 1

            self.processing_status = "success"
            self.processing_message = "Traitement terminé avec succès"

        except Exception as e:
            self.processing_status = "error"
            self.processing_message = str(e)

    def toggle_agent(self):
        """Toggle edge case agent."""
        self.enable_agent = not self.enable_agent


def index() -> rx.Component:
    """Premium processing page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    # Page header
                    rx.vstack(
                        rx.heading(
                            "Traitement de la paie",
                            size=HEADING_XL["size"],
                            weight=HEADING_XL["weight"],
                            letter_spacing=HEADING_XL["letter_spacing"],
                            color=COLORS["primary-900"],
                        ),
                        rx.text(
                            "Calcul automatique des salaires et détection d'anomalies",
                            size=BODY_MD["size"],
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

                    # Info card
                    rx.box(
                        rx.hstack(
                            rx.icon("cpu", size=48, color=COLORS["primary-600"], stroke_width=1.5),
                            rx.vstack(
                                rx.heading(
                                    "Traitement automatique",
                                    size=HEADING_MD["size"],
                                    weight="bold",
                                    color=COLORS["primary-900"],
                                ),
                                rx.text(
                                    "• Calcul des salaires selon la législation monégasque\n"
                                    "• Analyse intelligente des remarques\n"
                                    "• Comparaison avec le mois précédent\n"
                                    "• Corrections automatiques (≥95% de confiance)\n"
                                    "• Détection d'anomalies",
                                    size=BODY_SM["size"],
                                    color=COLORS["neutral-600"],
                                    line_height="1.8",
                                    white_space="pre-line",
                                ),
                                spacing="3",
                                align="start",
                            ),
                            spacing="4",
                            align="start",
                        ),
                        bg=COLORS["primary-50"],
                        border=f"1px solid {COLORS['primary-200']}",
                        border_radius=RADIUS["card"],
                        padding=COMPONENT_SPACING["card_padding_lg"],
                    ),

                    # Configuration
                    rx.vstack(
                        rx.heading(
                            "Configuration",
                            size=HEADING_MD["size"],
                            weight="bold",
                            color=COLORS["primary-900"],
                        ),
                        rx.box(
                            rx.hstack(
                                rx.switch(
                                    checked=ProcessingState.enable_agent,
                                    on_change=ProcessingState.toggle_agent,
                                    size="3",
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Activer le traitement par agent intelligent",
                                        size=BODY_MD["size"],
                                        weight="medium",
                                        color=COLORS["primary-900"],
                                    ),
                                    rx.text(
                                        "L'agent analysera les données et effectuera des corrections automatiques",
                                        size=BODY_SM["size"],
                                        color=COLORS["neutral-600"],
                                    ),
                                    spacing="1",
                                    align="start",
                                ),
                                spacing="3",
                            ),
                            bg=COLORS["white"],
                            border=f"1px solid {COLORS['neutral-200']}",
                            border_radius=RADIUS["card"],
                            padding=COMPONENT_SPACING["card_padding"],
                        ),
                        spacing="3",
                        width="100%",
                    ),

                    # Process button
                    rx.center(
                        rx.button(
                            rx.hstack(
                                rx.icon("play", size=20),
                                rx.text("Lancer le traitement"),
                                spacing="2",
                            ),
                            on_click=ProcessingState.start_processing,
                            disabled=ProcessingState.processing_status == "running",
                            size="3",
                            style={
                                "bg": COLORS["primary-600"],
                                "color": COLORS["white"],
                                "border_radius": RADIUS["lg"],
                                "padding": "1rem 2rem",
                                "font_size": "1rem",
                                "box_shadow": SHADOWS["button"],
                                "_hover": {
                                    "bg": COLORS["primary-700"],
                                    "box_shadow": SHADOWS["button_hover"],
                                },
                                "_disabled": {
                                    "bg": COLORS["neutral-300"],
                                    "cursor": "not-allowed",
                                },
                            },
                        ),
                        width="100%",
                    ),

                    # Loading state
                    rx.cond(
                        ProcessingState.processing_status == "running",
                        rx.center(
                            rx.vstack(
                                rx.spinner(size="3", color=COLORS["primary-600"]),
                                rx.text(
                                    "Traitement en cours...",
                                    size=BODY_SM["size"],
                                    color=COLORS["neutral-600"],
                                ),
                                spacing="3",
                            ),
                            padding="2rem",
                        ),
                        rx.fragment(),
                    ),

                    # Success results
                    rx.cond(
                        ProcessingState.processing_status == "success",
                        rx.vstack(
                            rx.box(
                                rx.hstack(
                                    rx.icon("circle-check", size=20, color=COLORS["success-600"]),
                                    rx.text(
                                        ProcessingState.processing_message,
                                        size=BODY_SM["size"],
                                        color=COLORS["success-600"],
                                    ),
                                    spacing="2",
                                ),
                                bg=COLORS["success-100"],
                                border=f"1px solid {COLORS['success-600']}",
                                border_radius=RADIUS["lg"],
                                padding="1rem",
                            ),

                            # Results grid
                            rx.vstack(
                                rx.heading(
                                    "Résultats",
                                    size=HEADING_MD["size"],
                                    weight="bold",
                                    color=COLORS["primary-900"],
                                ),
                                rx.grid(
                                    # Processed
                                    rx.box(
                                        rx.vstack(
                                            rx.icon("users", size=24, color=COLORS["primary-600"], stroke_width=2),
                                            rx.text(
                                                "Traités",
                                                size=LABEL["size"],
                                                weight=LABEL["weight"],
                                                color=COLORS["neutral-500"],
                                                text_transform=LABEL["text_transform"],
                                                letter_spacing=LABEL["letter_spacing"],
                                            ),
                                            rx.text(
                                                ProcessingState.processed_count,
                                                size=HEADING_MD["size"],
                                                weight="bold",
                                                color=COLORS["primary-900"],
                                                font_variant_numeric="tabular-nums",
                                            ),
                                            spacing="2",
                                            align="start",
                                        ),
                                        bg=COLORS["white"],
                                        border=f"1px solid {COLORS['neutral-200']}",
                                        border_radius=RADIUS["card"],
                                        padding=COMPONENT_SPACING["card_padding"],
                                        box_shadow=SHADOWS["card"],
                                    ),
                                    # Validated
                                    rx.box(
                                        rx.vstack(
                                            rx.icon("circle-check", size=24, color=COLORS["success-600"], stroke_width=2),
                                            rx.text(
                                                "Validés",
                                                size=LABEL["size"],
                                                weight=LABEL["weight"],
                                                color=COLORS["neutral-500"],
                                                text_transform=LABEL["text_transform"],
                                                letter_spacing=LABEL["letter_spacing"],
                                            ),
                                            rx.text(
                                                ProcessingState.validated_count,
                                                size=HEADING_MD["size"],
                                                weight="bold",
                                                color=COLORS["success-600"],
                                                font_variant_numeric="tabular-nums",
                                            ),
                                            spacing="2",
                                            align="start",
                                        ),
                                        bg=COLORS["white"],
                                        border=f"1px solid {COLORS['neutral-200']}",
                                        border_radius=RADIUS["card"],
                                        padding=COMPONENT_SPACING["card_padding"],
                                        box_shadow=SHADOWS["card"],
                                    ),
                                    # Edge cases
                                    rx.box(
                                        rx.vstack(
                                            rx.icon("triangle-alert", size=24, color=COLORS["warning-600"], stroke_width=2),
                                            rx.text(
                                                "Cas particuliers",
                                                size=LABEL["size"],
                                                weight=LABEL["weight"],
                                                color=COLORS["neutral-500"],
                                                text_transform=LABEL["text_transform"],
                                                letter_spacing=LABEL["letter_spacing"],
                                            ),
                                            rx.text(
                                                ProcessingState.edge_cases,
                                                size=HEADING_MD["size"],
                                                weight="bold",
                                                color=COLORS["warning-600"],
                                                font_variant_numeric="tabular-nums",
                                            ),
                                            spacing="2",
                                            align="start",
                                        ),
                                        bg=COLORS["white"],
                                        border=f"1px solid {COLORS['neutral-200']}",
                                        border_radius=RADIUS["card"],
                                        padding=COMPONENT_SPACING["card_padding"],
                                        box_shadow=SHADOWS["card"],
                                    ),
                                    columns="3",
                                    spacing=COMPONENT_SPACING["grid_gap"],
                                    width="100%",
                                ),
                                spacing="3",
                                width="100%",
                            ),

                            # Agent report
                            rx.cond(
                                ProcessingState.enable_agent,
                                rx.vstack(
                                    rx.heading(
                                        "Rapport de l'agent",
                                        size=HEADING_MD["size"],
                                        weight="bold",
                                        color=COLORS["primary-900"],
                                    ),
                                    rx.grid(
                                        # Automatic mods
                                        rx.box(
                                            rx.vstack(
                                                rx.icon("wand-sparkles", size=24, color=COLORS["info-600"], stroke_width=2),
                                                rx.text(
                                                    "Modifications auto",
                                                    size=LABEL["size"],
                                                    weight=LABEL["weight"],
                                                    color=COLORS["neutral-500"],
                                                    text_transform=LABEL["text_transform"],
                                                    letter_spacing=LABEL["letter_spacing"],
                                                ),
                                                rx.text(
                                                    ProcessingState.automatic_mods,
                                                    size=HEADING_MD["size"],
                                                    weight="bold",
                                                    color=COLORS["info-600"],
                                                    font_variant_numeric="tabular-nums",
                                                ),
                                                spacing="2",
                                                align="start",
                                            ),
                                            bg=COLORS["white"],
                                            border=f"1px solid {COLORS['neutral-200']}",
                                            border_radius=RADIUS["card"],
                                            padding=COMPONENT_SPACING["card_padding"],
                                            box_shadow=SHADOWS["card"],
                                        ),
                                        # Flagged
                                        rx.box(
                                            rx.vstack(
                                                rx.icon("flag", size=24, color=COLORS["warning-600"], stroke_width=2),
                                                rx.text(
                                                    "Cas signalés",
                                                    size=LABEL["size"],
                                                    weight=LABEL["weight"],
                                                    color=COLORS["neutral-500"],
                                                    text_transform=LABEL["text_transform"],
                                                    letter_spacing=LABEL["letter_spacing"],
                                                ),
                                                rx.text(
                                                    ProcessingState.flagged_cases,
                                                    size=HEADING_MD["size"],
                                                    weight="bold",
                                                    color=COLORS["warning-600"],
                                                    font_variant_numeric="tabular-nums",
                                                ),
                                                spacing="2",
                                                align="start",
                                            ),
                                            bg=COLORS["white"],
                                            border=f"1px solid {COLORS['neutral-200']}",
                                            border_radius=RADIUS["card"],
                                            padding=COMPONENT_SPACING["card_padding"],
                                            box_shadow=SHADOWS["card"],
                                        ),
                                        # Anomalies
                                        rx.box(
                                            rx.vstack(
                                                rx.icon("octagon-alert", size=24, color=COLORS["error-600"], stroke_width=2),
                                                rx.text(
                                                    "Anomalies",
                                                    size=LABEL["size"],
                                                    weight=LABEL["weight"],
                                                    color=COLORS["neutral-500"],
                                                    text_transform=LABEL["text_transform"],
                                                    letter_spacing=LABEL["letter_spacing"],
                                                ),
                                                rx.text(
                                                    ProcessingState.anomalies_detected,
                                                    size=HEADING_MD["size"],
                                                    weight="bold",
                                                    color=COLORS["error-600"],
                                                    font_variant_numeric="tabular-nums",
                                                ),
                                                spacing="2",
                                                align="start",
                                            ),
                                            bg=COLORS["white"],
                                            border=f"1px solid {COLORS['neutral-200']}",
                                            border_radius=RADIUS["card"],
                                            padding=COMPONENT_SPACING["card_padding"],
                                            box_shadow=SHADOWS["card"],
                                        ),
                                        columns="3",
                                        spacing=COMPONENT_SPACING["grid_gap"],
                                        width="100%",
                                    ),
                                    spacing="3",
                                    width="100%",
                                ),
                                rx.fragment(),
                            ),

                            spacing="4",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),

                    # Error state
                    rx.cond(
                        ProcessingState.processing_status == "error",
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-alert", size=20, color=COLORS["error-600"]),
                                rx.text(
                                    ProcessingState.processing_message,
                                    size=BODY_SM["size"],
                                    color=COLORS["error-600"],
                                ),
                                spacing="2",
                            ),
                            bg=COLORS["error-100"],
                            border=f"1px solid {COLORS['error-600']}",
                            border_radius=RADIUS["lg"],
                            padding="1rem",
                        ),
                        rx.fragment(),
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
    )
