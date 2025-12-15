"""PDF generation page"""

import reflex as rx
from ..state import AuthState, CompanyState, DataState
from ..components import layout, metric_card
import sys
from pathlib import Path
import io

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from services.shared_utils import get_payroll_system
from services.pdf_generation import PDFGeneratorService


class PDFState(rx.State):
    """PDF generation state"""
    
    selected_employee: str = ""
    generation_status: str = ""
    
    def generate_individual_bulletin(self):
        """Generate individual payslip"""
        if not self.selected_employee:
            return
        
        company_state = self.get_state(CompanyState)
        data_state = self.get_state(DataState)
        
        employee = next(
            (e for e in data_state.processed_data if e.get('matricule') == self.selected_employee),
            None
        )
        
        if not employee:
            self.generation_status = "Employee not found"
            return
        
        try:
            system = get_payroll_system()
            pdf_service = PDFGeneratorService(system.company_info)
            
            from services.payslip_helpers import clean_employee_data_for_pdf
            import calendar
            
            month, year = map(int, company_state.current_period.split('-'))
            last_day = calendar.monthrange(year, month)[1]
            
            employee_data = clean_employee_data_for_pdf(employee)
            employee_data.update({
                'period_start': f"01/{month:02d}/{year}",
                'period_end': f"{last_day:02d}/{month:02d}/{year}",
                'payment_date': f"{last_day:02d}/{month:02d}/{year}",
            })
            
            pdf_buffer = pdf_service.generate_email_ready_paystub(
                employee_data,
                f"{month:02d}-{year}"
            )
            
            filename = f"bulletin_{self.selected_employee}_{year}_{month:02d}.pdf"
            
            self.generation_status = "✅ PDF generated"
            
            return rx.download(
                data=pdf_buffer.getvalue(),
                filename=filename,
            )
            
        except Exception as e:
            self.generation_status = f"❌ Error: {str(e)}"
    
    def generate_journal(self):
        """Generate pay journal"""
        company_state = self.get_state(CompanyState)
        data_state = self.get_state(DataState)
        
        try:
            system = get_payroll_system()
            pdf_service = PDFGeneratorService(system.company_info)
            
            month, year = map(int, company_state.current_period.split('-'))
            
            journal_buffer = pdf_service.journal_generator.generate_pay_journal(
                data_state.processed_data,
                f"{month:02d}-{year}"
            )
            
            filename = f"journal_paie_{company_state.current_company}_{month:02d}_{year}.pdf"
            
            self.generation_status = "✅ Journal generated"
            
            return rx.download(
                data=journal_buffer.getvalue(),
                filename=filename,
            )
            
        except Exception as e:
            self.generation_status = f"❌ Error: {str(e)}"


def page() -> rx.Component:
    """PDF page layout"""
    return layout(
        rx.vstack(
            rx.heading("📄 PDF Generation", size="7"),
            
            rx.tabs(
                rx.tabs_list(
                    rx.tabs_trigger("Bulletins", value="bulletins"),
                    rx.tabs_trigger("Journal", value="journal"),
                    rx.tabs_trigger("Provision CP", value="provision"),
                ),
                rx.tabs_content(
                    rx.vstack(
                        rx.heading("Individual Bulletin", size="4"),
                        rx.select(
                            [e.get('matricule', '') for e in DataState.processed_data],
                            placeholder="Select employee",
                            value=PDFState.selected_employee,
                            on_change=PDFState.set_selected_employee,
                        ),
                        rx.button(
                            "Generate Bulletin",
                            on_click=PDFState.generate_individual_bulletin,
                            size="3",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    value="bulletins",
                ),
                rx.tabs_content(
                    rx.vstack(
                        rx.heading("Pay Journal", size="4"),
                        rx.hstack(
                            metric_card("Total Brut", f"{DataState.summary.get('total_brut', 0):,.0f} €"),
                            metric_card("Total Net", f"{DataState.summary.get('total_net', 0):,.0f} €"),
                            spacing="4",
                        ),
                        rx.button(
                            "Generate Journal",
                            on_click=PDFState.generate_journal,
                            size="3",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    value="journal",
                ),
                rx.tabs_content(
                    rx.vstack(
                        rx.heading("Provision CP", size="4"),
                        rx.text("Provision generation - simplified for MVP", color="gray"),
                        spacing="4",
                        width="100%",
                    ),
                    value="provision",
                ),
                default_value="bulletins",
            ),
            
            rx.cond(
                PDFState.generation_status != "",
                rx.callout(PDFState.generation_status, icon="info", size="2"),
            ),
            
            spacing="6",
            width="100%",
            on_mount=DataState.load_period_data,
        ),
        AuthState,
    )
