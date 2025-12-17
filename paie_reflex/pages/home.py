"""Home and login pages."""
import reflex as rx
from ..state import GlobalState
from ..components import navbar, sidebar_nav

def login() -> rx.Component:
    """Login page."""
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Monaco Payroll", size="8", weight="bold"),
                rx.text("Connectez-vous pour continuer", size="3", color="#6c757d"),
                
                rx.form(
                    rx.vstack(
                        rx.input(
                            placeholder="Nom d'utilisateur",
                            name="username",
                            required=True,
                        ),
                        rx.input(
                            placeholder="Mot de passe",
                            name="password",
                            type="password",
                            required=True,
                        ),
                        rx.button(
                            "Se connecter",
                            type="submit",
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    on_submit=GlobalState.login,
                    width="100%",
                ),
                
                rx.cond(
                    GlobalState.login_error,
                    rx.callout(
                        GlobalState.login_error,
                        icon="alert_circle",
                        color_scheme="red",
                    ),
                    rx.fragment(),
                ),
                
                spacing="5",
                width="100%",
            ),
            size="4",
            max_width="400px",
        ),
        height="100vh",
        bg="#f8f9fa",
    )


def index() -> rx.Component:
    """Home page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    rx.heading("Système de paie Monaco", size="8"),
                    rx.text(
                        "Traitement moderne de la paie pour les entreprises monégasques",
                        size="4",
                        color="#6c757d",
                    ),
                    
                    rx.divider(),
                    
                    rx.cond(
                        GlobalState.has_selection,
                        rx.vstack(
                            rx.heading("Sélection actuelle", size="6"),
                            rx.grid(
                                rx.box(
                                    rx.vstack(
                                        rx.text("Société", size="2", color="#6c757d"),
                                        rx.text(GlobalState.current_company, size="5", weight="bold"),
                                        spacing="2",
                                    ),
                                    bg="white",
                                    padding="1.5rem",
                                    border_radius="8px",
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.text("Période", size="2", color="#6c757d"),
                                        rx.text(GlobalState.current_period, size="5", weight="bold"),
                                        spacing="2",
                                    ),
                                    bg="white",
                                    padding="1.5rem",
                                    border_radius="8px",
                                ),
                                columns="2",
                                spacing="4",
                            ),
                            spacing="4",
                        ),
                        rx.callout(
                            "Veuillez sélectionner une société et une période pour continuer",
                            icon="info",
                            color_scheme="blue",
                        ),
                    ),
                    
                    rx.divider(),

                    rx.heading("Actions rapides", size="6"),
                    rx.grid(
                        rx.link(
                            rx.card(
                                rx.vstack(
                                    rx.icon("upload", size=32),
                                    rx.heading("Importer des données", size="4"),
                                    rx.text("Télécharger des fichiers Excel/CSV", size="2"),
                                    spacing="3",
                                ),
                            ),
                            href="/import",
                        ),
                        rx.link(
                            rx.card(
                                rx.vstack(
                                    rx.icon("settings", size=32),
                                    rx.heading("Traiter la paie", size="4"),
                                    rx.text("Calculer les salaires", size="2"),
                                    spacing="3",
                                ),
                            ),
                            href="/processing",
                        ),
                        rx.link(
                            rx.card(
                                rx.vstack(
                                    rx.icon("bar-chart-2", size=32),
                                    rx.heading("Dashboard", size="4"),
                                    rx.text("Voir les rapports", size="2"),
                                    spacing="3",
                                ),
                            ),
                            href="/dashboard",
                        ),
                        columns="3",
                        spacing="4",
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
        on_mount=GlobalState.load_companies,
    )
