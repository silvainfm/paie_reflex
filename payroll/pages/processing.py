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
            self.processing_message = "Select company and period first"
            self.processing_status = "error"
            return
        
        self.processing_status = "running"
        self.processing_message = "Processing payroll..."
        
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
            self.processing_message = "Processing completed successfully"
            
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
                    rx.heading("Process Payroll", size="8", margin_bottom="1rem"),
                    
                    rx.cond(
                        ~GlobalState.has_selection,
                        rx.callout(
                            "Select company and period first",
                            icon="alert-circle",
                            color_scheme="red",
                        ),
                        rx.fragment(),
                    ),
                    
                    rx.card(
                        rx.vstack(
                            rx.heading("Automatic Processing", size="5"),
                            rx.text(
                                "Salary calculation per Monaco legislation • Intelligent remark analysis • "
                                "Previous month comparison • Automatic corrections (≥95% confidence) • "
                                "Anomaly detection",
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
                        rx.text("Enable intelligent agent processing", size="3"),
                        spacing="3",
                    ),
                    
                    rx.divider(),
                    
                    rx.button(
                        "Start Processing",
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
                            
                            rx.heading("Results", size="6"),
                            rx.grid(
                                rx.box(
                                    rx.vstack(
                                        rx.text("Processed", size="2", color="#6c757d"),
                                        rx.text(ProcessingState.processed_count, size="6", weight="bold"),
                                        spacing="2",
                                    ),
                                    bg="white",
                                    padding="1.5rem",
                                    border_radius="8px",
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.text("Validated", size="2", color="#6c757d"),
                                        rx.text(ProcessingState.validated_count, size="6", weight="bold", color="green"),
                                        spacing="2",
                                    ),
                                    bg="white",
                                    padding="1.5rem",
                                    border_radius="8px",
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.text("Edge Cases", size="2", color="#6c757d"),
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
                                    rx.heading("Agent Report", size="6"),
                                    rx.grid(
                                        rx.box(
                                            rx.vstack(
                                                rx.text("Automatic Mods", size="2", color="#6c757d"),
                                                rx.text(ProcessingState.automatic_mods, size="5", weight="bold"),
                                                spacing="2",
                                            ),
                                            bg="white",
                                            padding="1.5rem",
                                            border_radius="8px",
                                        ),
                                        rx.box(
                                            rx.vstack(
                                                rx.text("Flagged Cases", size="2", color="#6c757d"),
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
