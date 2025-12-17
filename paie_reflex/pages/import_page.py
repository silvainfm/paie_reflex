"""Import data page"""

import reflex as rx
from ..state import AuthState, CompanyState, DataState
from ..components import layout, info_box
from ..services.data_mgt import DataManager
from ..services.import_export import ExcelImportExport


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
            self.upload_status = "Sélectionnez d'abord une société et une période"
            return
        
        try:
            file = files[0]
            content = await file.read()
            
            # Process file
            import polars as pl
            import io

            excel_manager = ExcelImportExport()

            if file.filename.endswith('.csv'):
                dtypes = {"Matricule": pl.Utf8}
                df_import = pl.read_csv(io.BytesIO(content), dtypes=dtypes)

                rename_mapping = {
                    k: v for k, v in excel_manager.EXCEL_COLUMN_MAPPING.items()
                    if k in df_import.columns
                }
                df_import = df_import.rename(rename_mapping)

                if 'matricule' in df_import.columns:
                    df_import = df_import.with_columns(
                        pl.col('matricule').cast(pl.Utf8, strict=False)
                    )
            else:
                df_import = excel_manager.import_from_excel(io.BytesIO(content))
            
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
        excel_manager = ExcelImportExport()
        template_buffer = excel_manager.create_template()

        company_state = self.get_state(CompanyState)
        filename = f"template_paie_{company_state.current_period}.xlsx"

        return rx.download(
            data=template_buffer.getvalue(),
            filename=filename,
        )


def index() -> rx.Component:
    """Import page layout"""
    return layout(
        rx.vstack(
            rx.heading("📥 Import des données", size="7"),


            info_box(
                "Template Excel",
                "Téléchargez le modèle pour importer les données de paie correctement formatées",
                "download",
            ),
            
            rx.button(
                "📥 Télécharger le modèle",
                on_click=ImportState.download_template,
                size="3",
            ),

            rx.divider(),

            rx.heading("Télécharger les données", size="5"),
            
            rx.upload(
                rx.vstack(
                    rx.button("Sélectionner un fichier", size="3"),
                    rx.text("Excel ou CSV", size="2", color="gray"),
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
                    rx.heading("Résumé de l'import", size="4"),
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
                                rx.text("Nouveaux", size="2", color="gray"),
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
                                rx.text("Existants", size="2", color="gray"),
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
                        "💾 Enregistrer les données",
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
    )
