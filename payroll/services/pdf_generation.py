"""PDF generation page."""
import reflex as rx
from typing import List, Dict
from ..state import GlobalState
from ..components import navbar, sidebar_nav


class PDFState(GlobalState):
    """State for PDF generation."""
    
    generation_mode: str = "individual"  # individual or all
    selected_employee: str = ""
    employees: List[str] = []
    pdf_status: str = ""
    pdf_data: Dict = {}
    
    def load_employees(self):
        """Load employees for PDF generation."""
        # Mock data
        self.employees = ["001 - Dupont Jean", "002 - Martin Marie"]
    
    def set_mode(self, mode: str):
        """Set generation mode."""
        self.generation_mode = mode
    
    def generate_individual(self):
        """Generate individual bulletin."""
        self.pdf_status = "Bulletin generated successfully"
        # Store PDF data for download
    
    def generate_all(self):
        """Generate all bulletins."""
        self.pdf_status = f"Generated {len(self.employees)} bulletins"
    
    def generate_journal(self):
        """Generate pay journal."""
        self.pdf_status = "Pay journal generated"
    
    def generate_provision_cp(self):
        """Generate PTO provision."""
        self.pdf_status = "PTO provision generated"
    
    def generate_charges(self):
        """Generate social charges statement."""
        self.pdf_status = "Charges statement generated"
    
    def generate_recap(self):
        """Generate annual recap."""
        self.pdf_status = "Annual recap generated"


def index() -> rx.Component:
    """PDF generation page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    rx.heading("PDF Generation", size="8", margin_bottom="1rem"),
                    
                    rx.cond(
                        ~GlobalState.has_selection,
                        rx.callout(
                            "Select company and period first",
                            icon="alert-circle",
                            color_scheme="red",
                        ),
                        rx.fragment(),
                    ),
                    
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("Paystubs", value="paystubs"),
                            rx.tabs.trigger("Pay Journal", value="journal"),
                            rx.tabs.trigger("PTO Provision", value="pto"),
                            rx.tabs.trigger("Social Charges", value="charges"),
                            rx.tabs.trigger("Annual Recap", value="recap"),
                        ),
                        
                        # Paystubs tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Generate Paystubs", size="6"),
                                
                                rx.radio(
                                    ["individual", "all"],
                                    value=PDFState.generation_mode,
                                    on_change=PDFState.set_mode,
                                ),
                                
                                rx.cond(
                                    PDFState.generation_mode == "individual",
                                    rx.vstack(
                                        rx.select(
                                            PDFState.employees,
                                            placeholder="Select employee",
                                            on_change=PDFState.selected_employee.set,
                                        ),
                                        rx.button(
                                            "Generate Individual",
                                            on_click=PDFState.generate_individual,
                                        ),
                                        spacing="3",
                                    ),
                                    rx.button(
                                        "Generate All",
                                        on_click=PDFState.generate_all,
                                    ),
                                ),
                                
                                spacing="4",
                            ),
                            value="paystubs",
                        ),
                        
                        # Journal tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Generate Pay Journal", size="6"),
                                rx.button(
                                    "Generate Journal",
                                    on_click=PDFState.generate_journal,
                                ),
                                spacing="4",
                            ),
                            value="journal",
                        ),
                        
                        # PTO tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Generate PTO Provision", size="6"),
                                rx.button(
                                    "Generate Provision",
                                    on_click=PDFState.generate_provision_cp,
                                ),
                                spacing="4",
                            ),
                            value="pto",
                        ),
                        
                        # Charges tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Generate Social Charges", size="6"),
                                rx.button(
                                    "Generate Statement",
                                    on_click=PDFState.generate_charges,
                                ),
                                spacing="4",
                            ),
                            value="charges",
                        ),
                        
                        # Recap tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Generate Annual Recap", size="6"),
                                rx.button(
                                    "Generate Recap",
                                    on_click=PDFState.generate_recap,
                                ),
                                spacing="4",
                            ),
                            value="recap",
                        ),
                        
                        default_value="paystubs",
                    ),
                    
                    rx.cond(
                        PDFState.pdf_status,
                        rx.callout(
                            PDFState.pdf_status,
                            icon="check-circle",
                            color_scheme="green",
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
        on_mount=PDFState.load_employees,
    )
