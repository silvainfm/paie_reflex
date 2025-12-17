"""Processing page for payroll calculations."""
import reflex as rx
from ..state import GlobalState
from ..components import navbar, sidebar_nav


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
    """Processing page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    rx.heading("Traitement de la paie", size="8", margin_bottom="1rem"),

                    rx.cond(
                        ~GlobalState.has_selection,
                        rx.callout(
                            "Sélectionnez d'abord une société et une période",
                            icon="alert-circle",
                            color_scheme="red",
                        ),
                        rx.fragment(),
                    ),
                    
                    rx.card(
                        rx.vstack(
                            rx.heading("Traitement automatique", size="5"),
                            rx.text(
                                "Calcul des salaires selon la législation monégasque • Analyse intelligente des remarques • "
                                "Comparaison avec le mois précédent • Corrections automatiques (≥95% de confiance) • "
                                "Détection d'anomalies",
                                size="2",
                                color="#6c757d",
                            ),
                            spacing="3",
                        ),
                    ),
                    
                    rx.divider(),

                    rx.heading("Configuration", size="6"),
                    rx.hstack(
                        rx.switch(
                            checked=ProcessingState.enable_agent,
                            on_change=ProcessingState.toggle_agent,
                        ),
                        rx.text("Activer le traitement par agent intelligent", size="3"),
                        spacing="3",
                    ),
                    
                    rx.divider(),

                    rx.button(
                        "Lancer le traitement",
                        on_click=ProcessingState.start_processing,
                        size="3",
                        disabled=ProcessingState.processing_status == "running",
                    ),
                    
                    rx.cond(
                        ProcessingState.processing_status == "running",
                        rx.spinner(size="3"),
                        rx.fragment(),
                    ),
                    
                    rx.cond(
                        ProcessingState.processing_status == "success",
                        rx.vstack(
                            rx.callout(
                                ProcessingState.processing_message,
                                icon="check-circle",
                                color_scheme="green",
                            ),
                            
                            rx.divider(),

                            rx.heading("Résultats", size="6"),
                            rx.grid(
                                rx.box(
                                    rx.vstack(
                                        rx.text("Traités", size="2", color="#6c757d"),
                                        rx.text(ProcessingState.processed_count, size="6", weight="bold"),
                                        spacing="2",
                                    ),
                                    bg="white",
                                    padding="1.5rem",
                                    border_radius="8px",
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.text("Validés", size="2", color="#6c757d"),
                                        rx.text(ProcessingState.validated_count, size="6", weight="bold", color="green"),
                                        spacing="2",
                                    ),
                                    bg="white",
                                    padding="1.5rem",
                                    border_radius="8px",
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.text("Cas particuliers", size="2", color="#6c757d"),
                                        rx.text(ProcessingState.edge_cases, size="6", weight="bold", color="orange"),
                                        spacing="2",
                                    ),
                                    bg="white",
                                    padding="1.5rem",
                                    border_radius="8px",
                                ),
                                columns="3",
                                spacing="4",
                            ),
                            
                            rx.cond(
                                ProcessingState.enable_agent,
                                rx.vstack(
                                    rx.heading("Rapport de l'agent", size="6"),
                                    rx.grid(
                                        rx.box(
                                            rx.vstack(
                                                rx.text("Modifications auto", size="2", color="#6c757d"),
                                                rx.text(ProcessingState.automatic_mods, size="5", weight="bold"),
                                                spacing="2",
                                            ),
                                            bg="white",
                                            padding="1.5rem",
                                            border_radius="8px",
                                        ),
                                        rx.box(
                                            rx.vstack(
                                                rx.text("Cas signalés", size="2", color="#6c757d"),
                                                rx.text(ProcessingState.flagged_cases, size="5", weight="bold"),
                                                spacing="2",
                                            ),
                                            bg="white",
                                            padding="1.5rem",
                                            border_radius="8px",
                                        ),
                                        rx.box(
                                            rx.vstack(
                                                rx.text("Anomalies", size="2", color="#6c757d"),
                                                rx.text(ProcessingState.anomalies_detected, size="5", weight="bold"),
                                                spacing="2",
                                            ),
                                            bg="white",
                                            padding="1.5rem",
                                            border_radius="8px",
                                        ),
                                        columns="3",
                                        spacing="4",
                                    ),
                                    spacing="4",
                                ),
                                rx.fragment(),
                            ),
                            
                            spacing="4",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    
                    rx.cond(
                        ProcessingState.processing_status == "error",
                        rx.callout(
                            ProcessingState.processing_message,
                            icon="alert-circle",
                            color_scheme="red",
                        ),
                        rx.fragment(),
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
    )
