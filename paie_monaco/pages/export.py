"""Export page for downloading payroll data."""
import reflex as rx
from typing import Dict
from io import BytesIO
from xlsxwriter import Workbook
import base64
from ..state import GlobalState
from ..components import navbar, sidebar_nav
from ..services.data_mgt import DataManager
from ..services.dsm_xml_generator import DSMXMLGenerator


class ExportState(GlobalState):
    """State for export page."""
    
    export_status: str = ""
    employee_count: int = 0
    total_brut: float = 0
    total_net: float = 0
    
    # Download data
    excel_data: str = ""
    dsm_data: str = ""
    
    # DSM config
    employer_number: str = ""
    plafond_t1: float = 3428.00
    
    def load_export_data(self):
        """Load data for export."""
        if not self.has_selection:
            return
        
        month, year = map(int, self.current_period.split('-'))
        summary = DataManager.get_company_summary(self.current_company, year, month)
        
        if summary:
            self.employee_count = summary.get('employee_count', 0)
            self.total_brut = summary.get('total_brut', 0)
            self.total_net = summary.get('total_net', 0)
        
        # Load employer number
        company_details = DataManager.get_company_details(self.current_company)
        if company_details:
            self.employer_number = company_details.get('employer_number_monaco', '')
    
    async def generate_excel(self):
        """Generate Excel export."""
        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)
            
            if df.is_empty():
                self.export_status = "No data to export"
                return
            
            # Create Excel file
            output = BytesIO()
            
            with Workbook(output) as wb:
                # Main data sheet
                ws = wb.add_worksheet('Payroll')
                
                # Header format
                header_format = wb.add_format({
                    'bold': True,
                    'bg_color': '#34495e',
                    'font_color': 'white',
                })
                
                # Write headers
                headers = ['Matricule', 'Nom', 'Prénom', 'Salaire Brut', 'Charges Sal.', 'Salaire Net', 'Charges Pat.', 'Coût Total']
                for col, header in enumerate(headers):
                    ws.write(0, col, header, header_format)
                
                # Write data
                for row_idx, row in enumerate(df.iter_rows(named=True), start=1):
                    ws.write(row_idx, 0, row.get('matricule', ''))
                    ws.write(row_idx, 1, row.get('nom', ''))
                    ws.write(row_idx, 2, row.get('prenom', ''))
                    ws.write(row_idx, 3, row.get('salaire_brut', 0))
                    ws.write(row_idx, 4, row.get('total_charges_salariales', 0))
                    ws.write(row_idx, 5, row.get('salaire_net', 0))
                    ws.write(row_idx, 6, row.get('total_charges_patronales', 0))
                    ws.write(row_idx, 7, row.get('cout_total_employeur', 0))
                
                # Auto-fit columns
                ws.set_column('A:A', 12)
                ws.set_column('B:C', 15)
                ws.set_column('D:H', 14)
            
            self.excel_data = base64.b64encode(output.getvalue()).decode()
            self.export_status = "✓ Excel generated"
            
        except Exception as e:
            self.export_status = f"Error: {str(e)}"
    
    async def generate_dsm_xml(self):
        """Generate DSM XML."""
        if not self.employer_number:
            self.export_status = "Employer number required for DSM"
            return
        
        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)
            
            if df.is_empty():
                self.export_status = "No data to export"
                return
            
            # Generate XML
            generator = DSMXMLGenerator(self.employer_number, self.plafond_t1)
            xml_buffer = generator.generate_dsm_xml(df, self.current_period)
            
            self.dsm_data = base64.b64encode(xml_buffer.getvalue()).decode()
            self.export_status = "✓ DSM XML generated"
            
        except Exception as e:
            self.export_status = f"Error: {str(e)}"


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
                            rx.tabs.trigger("DSM Monaco", value="dsm"),
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
                                
                                rx.cond(
                                    ExportState.excel_data,
                                    rx.download(
                                        rx.button("Download Excel", size="3", variant="soft"),
                                        url=f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{ExportState.excel_data}",
                                        filename=f"payroll_{ExportState.current_period}.xlsx",
                                    ),
                                    rx.fragment(),
                                ),
                                
                                spacing="4",
                            ),
                            value="excel",
                        ),
                        
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("DSM Monaco Declaration", size="6"),
                                rx.text("Generate XML file for Monaco social security declaration", size="2", color="#6c757d"),
                                
                                rx.cond(
                                    ExportState.employer_number,
                                    rx.callout(
                                        f"Employer Number: {ExportState.employer_number}",
                                        icon="check-circle",
                                        color_scheme="green",
                                    ),
                                    rx.callout(
                                        "Employer number not configured. Set in Config → Company",
                                        icon="alert-circle",
                                        color_scheme="red",
                                    ),
                                ),
                                
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
                                            rx.text("Plafond T1", size="2", color="#6c757d"),
                                            rx.text(f"{ExportState.plafond_t1:,.2f} €", size="5", weight="bold"),
                                            spacing="2",
                                        ),
                                        bg="white",
                                        padding="1.5rem",
                                        border_radius="8px",
                                    ),
                                    columns="2",
                                    spacing="4",
                                ),
                                
                                rx.button(
                                    "Generate DSM XML",
                                    on_click=ExportState.generate_dsm_xml,
                                    size="3",
                                    disabled=~ExportState.employer_number.bool(),
                                ),
                                
                                rx.cond(
                                    ExportState.dsm_data,
                                    rx.download(
                                        rx.button("Download DSM XML", size="3", variant="soft"),
                                        url=f"data:application/xml;base64,{ExportState.dsm_data}",
                                        filename=f"DSM_{ExportState.employer_number}_{ExportState.current_period}.xml",
                                    ),
                                    rx.fragment(),
                                ),
                                
                                spacing="4",
                            ),
                            value="dsm",
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
        on_mount=ExportState.load_export_data,
    )
