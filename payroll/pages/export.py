"""Export page for downloading payroll data."""
import reflex as rx
from ..state import GlobalState
from ..components import navbar, sidebar_nav


class ExportState(GlobalState):
    """State for export page."""
    
    export_status: str = ""
    employee_count: int = 25
    total_brut: float = 87500.00
    total_net: float = 70000.00
    
    def generate_excel(self):
        """Generate Excel export."""
        self.export_status = "Excel file generated"
    
    def generate_report(self):
        """Generate summary report."""
        self.export_status = "Report generated"


def index() -> rx.Component:
    """Export page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    rx.heading("Export Results", size="8", margin_bottom="1rem"),
                    
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
                            rx.tabs.trigger("Excel Export", value="excel"),
                            rx.tabs.trigger("Summary Report", value="report"),
                        ),
                        
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Export to Excel", size="6"),
                                
                                rx.grid(
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Employees", size="2", color="#6c757d"),
                                            rx.text(ExportState.employee_count, size="5", weight="bold"),
                                            spacing="2",
                                        ),
                                        bg="white",
                                        padding="1.5rem",
                                        border_radius="8px",
                                    ),
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Gross Payroll", size="2", color="#6c757d"),
                                            rx.text(f"{ExportState.total_brut:,.0f} €", size="5", weight="bold"),
                                            spacing="2",
                                        ),
                                        bg="white",
                                        padding="1.5rem",
                                        border_radius="8px",
                                    ),
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Net to Pay", size="2", color="#6c757d"),
                                            rx.text(f"{ExportState.total_net:,.0f} €", size="5", weight="bold"),
                                            spacing="2",
                                        ),
                                        bg="white",
                                        padding="1.5rem",
                                        border_radius="8px",
                                    ),
                                    columns="3",
                                    spacing="4",
                                ),
                                
                                rx.button(
                                    "Generate Excel",
                                    on_click=ExportState.generate_excel,
                                    size="3",
                                ),
                                
                                spacing="4",
                            ),
                            value="excel",
                        ),
                        
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Summary Report", size="6"),
                                
                                rx.button(
                                    "Generate Report",
                                    on_click=ExportState.generate_report,
                                    size="3",
                                ),
                                
                                spacing="4",
                            ),
                            value="report",
                        ),
                        
                        default_value="excel",
                    ),
                    
                    rx.cond(
                        ExportState.export_status,
                        rx.callout(
                            ExportState.export_status,
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
    )
