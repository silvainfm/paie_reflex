"""Import data page - Premium design."""

import reflex as rx
from ..state import AuthState, CompanyState, DataState
from ..components import navbar, sidebar_nav
from ..services.data_mgt import DataManager
from ..services.import_export import ExcelImportExport
from ..design_tokens import (
    COLORS,
    SHADOWS,
    RADIUS,
    COMPONENT_SPACING,
    HEADING_XL,
    HEADING_MD,
    BODY_MD,
    BODY_SM,
    LABEL,
)


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
            self.upload_status = "error:Sélectionnez d'abord une société et une période"
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

            self.upload_status = f"success:{len(df_import)} employés importés avec succès"
            self.show_summary = True

        except Exception as e:
            self.upload_status = f"error:{str(e)}"
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

        self.upload_status = "success:Données enregistrées avec succès!"

        # Reload data
        data_state = await self.get_state(DataState)
        data_state.load_period_data()

    async def download_template(self):
        """Generate template for download"""
        excel_manager = ExcelImportExport()
        template_buffer = excel_manager.create_template()

        company_state = await self.get_state(CompanyState)
        filename = f"template_paie_{company_state.current_period}.xlsx"

        return rx.download(
            data=template_buffer.getvalue(),
            filename=filename,
        )
    
    @rx.var
    def upload_message(self) -> str:
        parts = self.upload_status.split(":", 1)
        return parts[1].strip() if len(parts) > 1 else self.upload_status


def index() -> rx.Component:
    """Premium import page layout"""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    # Page header
                    rx.vstack(
                        rx.heading(
                            "Import des données",
                            size=HEADING_XL["size"],
                            weight=HEADING_XL["weight"],
                            letter_spacing=HEADING_XL["letter_spacing"],
                            color=COLORS["primary-900"],
                        ),
                        rx.text(
                            "Importez vos données de paie depuis Excel ou CSV",
                            size=BODY_MD["size"],
                            color=COLORS["neutral-600"],
                        ),
                        spacing="2",
                        align="start",
                    ),

                    # Template download card
                    rx.box(
                        rx.hstack(
                            rx.icon("file-spreadsheet", size=48, color=COLORS["primary-600"], stroke_width=1.5),
                            rx.vstack(
                                rx.heading(
                                    "Modèle Excel",
                                    size=HEADING_MD["size"],
                                    weight="bold",
                                    color=COLORS["primary-900"],
                                ),
                                rx.text(
                                    "Téléchargez le modèle pour importer les données de paie correctement formatées",
                                    size=BODY_SM["size"],
                                    color=COLORS["neutral-600"],
                                    line_height="1.5",
                                ),
                                rx.button(
                                    rx.hstack(
                                        rx.icon("download", size=20),
                                        rx.text("Télécharger le modèle"),
                                        spacing="2",
                                    ),
                                    on_click=ImportState.download_template,
                                    size="3",
                                    style={
                                        "bg": COLORS["primary-600"],
                                        "color": COLORS["white"],
                                        "border_radius": RADIUS["lg"],
                                        "padding": "0.75rem 1.5rem",
                                        "box_shadow": SHADOWS["button"],
                                        "_hover": {
                                            "bg": COLORS["primary-700"],
                                            "box_shadow": SHADOWS["button_hover"],
                                        },
                                    },
                                ),
                                spacing="3",
                                align="start",
                            ),
                            spacing="4",
                            align="start",
                        ),
                        bg=COLORS["primary-50"],
                        border=f"1px solid {COLORS['primary-200']}",
                        border_radius=RADIUS["card"],
                        padding=COMPONENT_SPACING["card_padding_lg"],
                    ),

                    # Upload section
                    rx.vstack(
                        rx.heading(
                            "Télécharger les données",
                            size=HEADING_MD["size"],
                            weight="bold",
                            color=COLORS["primary-900"],
                        ),

                        rx.upload(
                            rx.box(
                                rx.vstack(
                                    rx.icon("cloud-upload", size=48, color=COLORS["primary-600"], stroke_width=1.5),
                                    rx.text(
                                        "Glissez-déposez votre fichier ici",
                                        size=BODY_MD["size"],
                                        weight="medium",
                                        color=COLORS["primary-900"],
                                    ),
                                    rx.text(
                                        "ou cliquez pour sélectionner",
                                        size=BODY_SM["size"],
                                        color=COLORS["neutral-600"],
                                    ),
                                    rx.text(
                                        "Excel (.xlsx, .xls) ou CSV",
                                        size=BODY_SM["size"],
                                        color=COLORS["neutral-500"],
                                    ),
                                    spacing="3",
                                    align="center",
                                ),
                                border=f"2px dashed {COLORS['neutral-300']}",
                                border_radius=RADIUS["card"],
                                padding="3rem",
                                bg=COLORS["neutral-50"],
                                cursor="pointer",
                                transition="all 0.2s ease",
                                _hover={
                                    "border_color": COLORS["primary-400"],
                                    "bg": COLORS["primary-50"],
                                },
                            ),
                            id="upload1",
                            accept={
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
                                "application/vnd.ms-excel": [".xls"],
                                "text/csv": [".csv"],
                            },
                            on_drop=ImportState.handle_upload(rx.upload_files(upload_id="upload1")),
                        ),

                        spacing="3",
                        width="100%",
                    ),

                    # Status message
                    rx.cond(
                        ImportState.upload_status != "",
                        rx.cond(
                            ImportState.upload_status.startswith("success:"),
                            rx.box(
                                rx.hstack(
                                    rx.icon("circle-check", size=20, color=COLORS["success-600"]),
                                    rx.text(
                                        ImportState.upload_message,
                                        size=BODY_SM["size"],
                                        color=COLORS["success-600"],
                                    ),
                                    spacing="2",
                                ),
                                bg=COLORS["success-100"],
                                border=f"1px solid {COLORS['success-600']}",
                                border_radius=RADIUS["lg"],
                                padding="1rem",
                            ),
                            rx.box(
                                rx.hstack(
                                    rx.icon("circle-alert", size=20, color=COLORS["error-600"]),
                                    rx.text(
                                        ImportState.upload_message,
                                        size=BODY_SM["size"],
                                        color=COLORS["error-600"],
                                        ),
                                    spacing="2",
                                ),
                                bg=COLORS["error-100"],
                                border=f"1px solid {COLORS['error-600']}",
                                border_radius=RADIUS["lg"],
                                padding="1rem",
                            ),
                        ),
                        rx.fragment(),
                    ),

                    # Import summary
                    rx.cond(
                        ImportState.show_summary,
                        rx.vstack(
                            rx.heading(
                                "Résumé de l'import",
                                size=HEADING_MD["size"],
                                weight="bold",
                                color=COLORS["primary-900"],
                            ),
                            rx.grid(
                                # Total card
                                rx.box(
                                    rx.vstack(
                                        rx.icon("users", size=24, color=COLORS["primary-600"], stroke_width=2),
                                        rx.text(
                                            "Total",
                                            size=LABEL["size"],
                                            weight=LABEL["weight"],
                                            color=COLORS["neutral-500"],
                                            text_transform=LABEL["text_transform"],
                                            letter_spacing=LABEL["letter_spacing"],
                                        ),
                                        rx.text(
                                            ImportState.import_summary.get('total', 0),
                                            size=HEADING_MD["size"],
                                            weight="bold",
                                            color=COLORS["primary-900"],
                                            font_variant_numeric="tabular-nums",
                                        ),
                                        spacing="2",
                                        align="start",
                                    ),
                                    bg=COLORS["white"],
                                    border=f"1px solid {COLORS['neutral-200']}",
                                    border_radius=RADIUS["card"],
                                    padding=COMPONENT_SPACING["card_padding"],
                                    box_shadow=SHADOWS["card"],
                                ),
                                # New card
                                rx.box(
                                    rx.vstack(
                                        rx.icon("user-plus", size=24, color=COLORS["success-600"], stroke_width=2),
                                        rx.text(
                                            "Nouveaux",
                                            size=LABEL["size"],
                                            weight=LABEL["weight"],
                                            color=COLORS["neutral-500"],
                                            text_transform=LABEL["text_transform"],
                                            letter_spacing=LABEL["letter_spacing"],
                                        ),
                                        rx.text(
                                            ImportState.import_summary.get('new', 0),
                                            size=HEADING_MD["size"],
                                            weight="bold",
                                            color=COLORS["success-600"],
                                            font_variant_numeric="tabular-nums",
                                        ),
                                        spacing="2",
                                        align="start",
                                    ),
                                    bg=COLORS["white"],
                                    border=f"1px solid {COLORS['neutral-200']}",
                                    border_radius=RADIUS["card"],
                                    padding=COMPONENT_SPACING["card_padding"],
                                    box_shadow=SHADOWS["card"],
                                ),
                                # Existing card
                                rx.box(
                                    rx.vstack(
                                        rx.icon("user-check", size=24, color=COLORS["warning-600"], stroke_width=2),
                                        rx.text(
                                            "Existants",
                                            size=LABEL["size"],
                                            weight=LABEL["weight"],
                                            color=COLORS["neutral-500"],
                                            text_transform=LABEL["text_transform"],
                                            letter_spacing=LABEL["letter_spacing"],
                                        ),
                                        rx.text(
                                            ImportState.import_summary.get('existing', 0),
                                            size=HEADING_MD["size"],
                                            weight="bold",
                                            color=COLORS["warning-600"],
                                            font_variant_numeric="tabular-nums",
                                        ),
                                        spacing="2",
                                        align="start",
                                    ),
                                    bg=COLORS["white"],
                                    border=f"1px solid {COLORS['neutral-200']}",
                                    border_radius=RADIUS["card"],
                                    padding=COMPONENT_SPACING["card_padding"],
                                    box_shadow=SHADOWS["card"],
                                ),
                                columns="3",
                                spacing=COMPONENT_SPACING["grid_gap"],
                                width="100%",
                            ),
                            rx.button(
                                rx.hstack(
                                    rx.icon("save", size=20),
                                    rx.text("Enregistrer les données"),
                                    spacing="2",
                                ),
                                on_click=ImportState.save_data,
                                size="3",
                                style={
                                    "bg": COLORS["success-600"],
                                    "color": COLORS["white"],
                                    "border_radius": RADIUS["lg"],
                                    "padding": "0.75rem 1.5rem",
                                    "box_shadow": SHADOWS["button"],
                                    "_hover": {
                                        "bg": COLORS["success-500"],
                                        "box_shadow": SHADOWS["button_hover"],
                                    },
                                },
                            ),
                            spacing="4",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),

                    spacing=COMPONENT_SPACING["section_gap"],
                    width="100%",
                ),
                flex="1",
                padding=COMPONENT_SPACING["page_padding"],
                min_height="calc(100vh - 64px)",
            ),
            spacing="0",
            width="100%",
            align_items="start",
        ),
    )
