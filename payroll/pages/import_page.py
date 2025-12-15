"""Import data page"""

import reflex as rx
from ..state import AuthState, CompanyState, DataState
from ..components import layout, info_box
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from services.data_mgt import DataManager
from services.shared_utils import get_payroll_system


class ImportState(rx.State):
    """Import page state"""
    
    upload_status: str = ""
    import_summary: dict = {}
    show_summary: bool = False
    
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle file upload"""
        if not files:
            return
        
        company_state = await self.get_state(CompanyState)
        if not company_state.current_company or not company_state.current_period:
            self.upload_status = "Select company and period first"
            return
        
        try:
            file = files[0]
            content = await file.read()
            
            # Process file
            import polars as pl
            import io
            
            system = get_payroll_system()
            
            if file.filename.endswith('.csv'):
                dtypes = {"Matricule": pl.Utf8}
                df_import = pl.read_csv(io.BytesIO(content), dtypes=dtypes)
                
                rename_mapping = {
                    k: v for k, v in system.excel_manager.EXCEL_COLUMN_MAPPING.items()
                    if k in df_import.columns
                }
                df_import = df_import.rename(rename_mapping)
                
                if 'matricule' in df_import.columns:
                    df_import = df_import.with_columns(
                        pl.col('matricule').cast(pl.Utf8, strict=False)
                    )
            else:
                df_import = system.excel_manager.import_from_excel(io.BytesIO(content))
            
            # Check existing employees
            month, year = map(int, company_state.current_period.split('-'))
            check_result = DataManager.check_existing_employees(
                df_import,
                company_state.current_company,
                month,
                year
            )
            
            self.import_summary = {
                'total': len(df_import),
                'new': len(check_result['new']),
                'existing': len(check_result['existing']),
                'df': df_import,
            }
            
            self.upload_status = f"✅ {len(df_import)} employees imported"
            self.show_summary = True
            
        except Exception as e:
            self.upload_status = f"❌ Error: {str(e)}"
            self.show_summary = False
    
    async def save_data(self):
        """Save imported data"""
        if not self.import_summary:
            return
        
        company_state = await self.get_state(CompanyState)
        month, year = map(int, company_state.current_period.split('-'))
        
        DataManager.save_period_data(
            self.import_summary['df'],
            company_state.current_company,
            month,
            year
        )
        
        self.upload_status = "✅ Data saved successfully!"
        
        # Reload data
        data_state = await self.get_state(DataState)
        data_state.load_period_data()
    
    def download_template(self):
        """Generate template for download"""
        system = get_payroll_system()
        template_buffer = system.excel_manager.create_template()
        
        company_state = self.get_state(CompanyState)
        filename = f"template_paie_{company_state.current_period}.xlsx"
        
        return rx.download(
            data=template_buffer.getvalue(),
            filename=filename,
        )


def page() -> rx.Component:
    """Import page layout"""
    return layout(
        rx.vstack(
            rx.heading("📥 Import des données", size="7"),
            
            info_box(
                "Template Excel",
                "Download the template to import payroll data correctly formatted",
                "download",
            ),
            
            rx.button(
                "📥 Download Template",
                on_click=ImportState.download_template,
                size="3",
            ),
            
            rx.divider(),
            
            rx.heading("Upload Data", size="5"),
            
            rx.upload(
                rx.vstack(
                    rx.button("Select File", size="3"),
                    rx.text("Excel or CSV", size="2", color="gray"),
                ),
                id="upload1",
                accept={
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
                    "application/vnd.ms-excel": [".xls"],
                    "text/csv": [".csv"],
                },
                on_drop=ImportState.handle_upload(rx.upload_files(upload_id="upload1")),
            ),
            
            rx.cond(
                ImportState.upload_status != "",
                rx.callout(
                    ImportState.upload_status,
                    icon="info",
                    size="2",
                ),
            ),
            
            rx.cond(
                ImportState.show_summary,
                rx.vstack(
                    rx.heading("Import Summary", size="4"),
                    rx.hstack(
                        rx.box(
                            rx.vstack(
                                rx.text("Total", size="2", color="gray"),
                                rx.heading(ImportState.import_summary.get('total', 0)),
                            ),
                            padding="1rem",
                            bg="white",
                            border_radius="0.5rem",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("New", size="2", color="gray"),
                                rx.heading(
                                    ImportState.import_summary.get('new', 0),
                                    color="green",
                                ),
                            ),
                            padding="1rem",
                            bg="white",
                            border_radius="0.5rem",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("Existing", size="2", color="gray"),
                                rx.heading(
                                    ImportState.import_summary.get('existing', 0),
                                    color="orange",
                                ),
                            ),
                            padding="1rem",
                            bg="white",
                            border_radius="0.5rem",
                        ),
                        spacing="4",
                    ),
                    rx.button(
                        "💾 Save Data",
                        on_click=ImportState.save_data,
                        size="3",
                        color_scheme="green",
                    ),
                    spacing="4",
                    width="100%",
                ),
            ),
            
            spacing="6",
            width="100%",
        ),
        AuthState,
    )
