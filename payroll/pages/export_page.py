"""Export page"""

import reflex as rx
from ..state import AuthState, CompanyState, DataState
from ..components import layout, metric_card
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from services.data_mgt import DataManager


class ExportState(rx.State):
    """Export state"""
    
    export_status: str = ""
    
    def export_excel(self):
        """Export to Excel"""
        company_state = self.get_state(CompanyState)
        data_state = self.get_state(DataState)
        
        try:
            import polars as pl
            from xlsxwriter import Workbook
            import io
            
            month, year = map(int, company_state.current_period.split('-'))
            df = DataManager.load_period_data(company_state.current_company, month, year)
            
            output = io.BytesIO()
            
            with Workbook(output) as wb:
                df.write_excel(
                    workbook=wb,
                    worksheet="Paies",
                    position=(2, 0),
                    table_style={"style": "Table Style Medium 2"},
                    autofit=True,
                )
            
            filename = f"paies_{company_state.current_company}_{company_state.current_period}.xlsx"
            
            self.export_status = "✅ Excel generated"
            
            return rx.download(
                data=output.getvalue(),
                filename=filename,
            )
            
        except Exception as e:
            self.export_status = f"❌ Error: {str(e)}"
    
    def generate_dsm(self):
        """Generate DSM XML"""
        company_state = self.get_state(CompanyState)
        
        try:
            from services.dsm_xml_generator import DSMXMLGenerator
            from services.payroll_calculations import MonacoPayrollConstants
            from services.shared_utils import get_payroll_system
            
            system = get_payroll_system()
            employer_number = system.company_info.get('employer_number_monaco', '')
            
            if not employer_number:
                self.export_status = "❌ Employer number not configured"
                return
            
            month, year = map(int, company_state.current_period.split('-'))
            constants = MonacoPayrollConstants(year)
            
            df = DataManager.load_period_data(company_state.current_company, month, year)
            
            generator = DSMXMLGenerator(employer_number, constants.PLAFOND_SS_T1)
            xml_buffer = generator.generate_dsm_xml(df, company_state.current_period)
            
            filename = f"DSM_{employer_number}_{company_state.current_period}.xml"
            
            self.export_status = "✅ DSM generated"
            
            return rx.download(
                data=xml_buffer.getvalue(),
                filename=filename,
            )
            
        except Exception as e:
            self.export_status = f"❌ Error: {str(e)}"


def page() -> rx.Component:
    """Export page layout"""
    return layout(
        rx.vstack(
            rx.heading("📤 Export", size="7"),
            
            # Summary metrics
            rx.hstack(
                metric_card("Employees", str(DataState.summary.get('employee_count', 0))),
                metric_card("Total Brut", f"{DataState.summary.get('total_brut', 0):,.0f} €"),
                metric_card("Total Net", f"{DataState.summary.get('total_net', 0):,.0f} €"),
                spacing="4",
                width="100%",
            ),
            
            rx.divider(),
            
            # Excel export
            rx.vstack(
                rx.heading("Excel Export", size="4"),
                rx.text("Export complete payroll data to Excel", color="gray"),
                rx.button(
                    "📥 Generate Excel",
                    on_click=ExportState.export_excel,
                    size="3",
                ),
                align_items="start",
                spacing="3",
                width="100%",
            ),
            
            rx.divider(),
            
            # DSM export
            rx.vstack(
                rx.heading("DSM Declaration", size="4"),
                rx.text("Generate XML for Monaco Social Security", color="gray"),
                rx.button(
                    "📄 Generate DSM",
                    on_click=ExportState.generate_dsm,
                    size="3",
                ),
                align_items="start",
                spacing="3",
                width="100%",
            ),
            
            rx.cond(
                ExportState.export_status != "",
                rx.callout(ExportState.export_status, icon="info", size="2"),
            ),
            
            spacing="6",
            width="100%",
            on_mount=DataState.load_period_data,
        ),
        AuthState,
    )
