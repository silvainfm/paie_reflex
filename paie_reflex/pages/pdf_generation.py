"""PDF generation page - Premium design."""
import reflex as rx
from typing import List, Dict
import zipfile
from io import BytesIO
from pathlib import Path
from ..state import GlobalState
from ..components import navbar, sidebar_nav
from ..services.data_mgt import DataManager
from ..services.pdf_generation import PDFGeneratorService
from ..services.pdf_storage import PDFStorageService, StorageConfigManager
from ..design_tokens import (
    COLORS,
    SHADOWS,
    RADIUS,
    COMPONENT_SPACING,
    HEADING_XL,
    HEADING_MD,
    HEADING_SM,
    BODY_MD,
    BODY_SM,
    LABEL,
)


class PDFState(GlobalState):
    """State for PDF generation."""

    generation_mode: str = "individual"
    selected_employee: str = ""
    employees: List[Dict] = []
    pdf_status: str = ""
    is_generating: bool = False
    progress: int = 0
    total_items: int = 0

    # Download triggers
    individual_pdf_data: str = ""
    all_bulletins_data: str = ""
    journal_data: str = ""
    provision_data: str = ""
    charges_data: str = ""
    recap_data: str = ""

    # Recap year input
    recap_year: str = ""

    # Cloud storage
    saved_locations: List[str] = []  # Track where PDFs were saved

    @rx.var
    def employee_labels(self) -> List[str]:
        """Get list of employee labels for select dropdown."""
        return [emp["label"] for emp in self.employees]

    @rx.var
    def pdf_status_message(self) -> str:
        """Extract message from pdf_status."""
        if ":" in self.pdf_status:
            return self.pdf_status.split(":", 1)[1]
        return self.pdf_status

    def load_employees(self):
        """Load employees for PDF generation."""
        if not self.has_selection:
            return

        month, year = map(int, self.current_period.split('-'))
        df = DataManager.load_period_data(self.current_company, month, year)

        if not df.is_empty():
            self.employees = [
                {
                    "matricule": row.get("matricule", ""),
                    "nom": row.get("nom", ""),
                    "prenom": row.get("prenom", ""),
                    "label": f"{row.get('matricule', '')} - {row.get('nom', '')} {row.get('prenom', '')}"
                }
                for row in df.iter_rows(named=True)
            ]

    def set_mode(self, mode: str):
        """Set generation mode."""
        self.generation_mode = mode

    def set_selected_employee(self, employee: str):
        """Set selected employee."""
        self.selected_employee = employee

    def set_recap_year(self, year: str):
        """Set recap year."""
        self.recap_year = year

    async def generate_individual(self):
        """Generate individual bulletin."""
        if not self.selected_employee:
            self.pdf_status = "error:Veuillez sélectionner un employé"
            return

        self.is_generating = True
        self.progress = 0
        self.total_items = 1
        self.individual_pdf_data = ""

        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)

            # Find employee
            matricule = self.selected_employee.split(' - ')[0]
            emp_df = df.filter(df['matricule'] == matricule)

            if emp_df.is_empty():
                self.pdf_status = "error:Employé non trouvé"
                self.is_generating = False
                return

            # Generate PDF
            company_info = {"name": self.current_company, "address": "", "siret": ""}
            pdf_service = PDFGeneratorService(company_info)

            emp_data = emp_df.to_dicts()[0]
            pdf_buffer = pdf_service.paystub_gen.generate_paystub(emp_data, self.current_period)

            self.progress = 1

            # Save to cloud if configured
            config_mgr = StorageConfigManager(Path("data/config/storage_config.json"))
            storage_config = config_mgr.load_config()

            self.saved_locations = []

            if storage_config and storage_config.enabled:
                storage_service = PDFStorageService(storage_config)
                success, location = storage_service.save_pdf(
                    pdf_buffer,
                    "bulletin",
                    self.current_company,
                    self.current_company,
                    year,
                    month,
                    matricule=matricule,
                    nom=emp_data.get('nom', ''),
                    prenom=emp_data.get('prenom', '')
                )
                if success:
                    self.saved_locations.append(location)

            # Convert to base64 for download
            import base64
            self.individual_pdf_data = base64.b64encode(pdf_buffer.getvalue()).decode()

            if self.saved_locations:
                self.pdf_status = f"success:Bulletin généré et sauvegardé dans: {self.saved_locations[0]}"
            else:
                self.pdf_status = "success:Bulletin généré avec succès"

        except Exception as e:
            self.pdf_status = f"error:{str(e)}"
        finally:
            self.is_generating = False

    async def generate_all(self):
        """Generate all bulletins as ZIP with progress tracking."""
        self.is_generating = True
        self.progress = 0
        self.all_bulletins_data = ""
        self.pdf_status = "info:Démarrage de la génération groupée..."

        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)

            employee_data = df.to_dicts()
            self.total_items = len(employee_data)

            company_info = {"name": self.current_company, "address": "", "siret": ""}
            pdf_service = PDFGeneratorService(company_info)

            # Check for cloud storage
            config_mgr = StorageConfigManager(Path("data/config/storage_config.json"))
            storage_config = config_mgr.load_config()
            storage_service = None

            self.saved_locations = []

            if storage_config and storage_config.enabled:
                storage_service = PDFStorageService(storage_config)

            # Create ZIP
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for idx, emp_data in enumerate(employee_data):
                    # Generate individual paystub
                    pdf_buffer = pdf_service.paystub_gen.generate_paystub(emp_data, self.current_period)

                    # Add to ZIP
                    filename = f"bulletin_{emp_data['matricule']}_{emp_data['nom']}.pdf"
                    zf.writestr(filename, pdf_buffer.getvalue())

                    # Save to cloud if configured
                    if storage_service:
                        success, location = storage_service.save_pdf(
                            pdf_buffer,
                            "bulletin",
                            self.current_company,
                            self.current_company,
                            year,
                            month,
                            matricule=emp_data.get('matricule', ''),
                            nom=emp_data.get('nom', ''),
                            prenom=emp_data.get('prenom', '')
                        )
                        if success:
                            self.saved_locations.append(location)

                    # Update progress
                    self.progress = idx + 1
                    self.pdf_status = f"info:Génération {self.progress}/{self.total_items}..."

            import base64
            self.all_bulletins_data = base64.b64encode(zip_buffer.getvalue()).decode()

            if self.saved_locations:
                self.pdf_status = f"success:{self.total_items} bulletins générés et sauvegardés ({len(self.saved_locations)} fichiers)"
            else:
                self.pdf_status = f"success:{self.total_items} bulletins générés avec succès"

        except Exception as e:
            self.pdf_status = f"error:{str(e)}"
        finally:
            self.is_generating = False

    async def generate_journal(self):
        """Generate pay journal."""
        self.is_generating = True
        self.journal_data = ""

        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)

            company_info = {"name": self.current_company, "address": "", "siret": ""}
            pdf_service = PDFGeneratorService(company_info)

            journal_buffer = pdf_service.journal_gen.generate_journal(df.to_dicts(), self.current_period)

            import base64
            self.journal_data = base64.b64encode(journal_buffer.getvalue()).decode()
            self.pdf_status = "success:Journal généré avec succès"

        except Exception as e:
            self.pdf_status = f"error:{str(e)}"
        finally:
            self.is_generating = False

    async def generate_provision_cp(self):
        """Generate PTO provision."""
        self.is_generating = True
        self.provision_data = ""

        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)

            company_info = {"name": self.current_company, "address": "", "siret": ""}
            pdf_service = PDFGeneratorService(company_info)

            provisions_data = pdf_service._prepare_provisions_data(df)
            provision_buffer = pdf_service.pto_gen.generate_provision(provisions_data, self.current_period)

            import base64
            self.provision_data = base64.b64encode(provision_buffer.getvalue()).decode()
            self.pdf_status = "success:Provision CP générée avec succès"

        except Exception as e:
            self.pdf_status = f"error:{str(e)}"
        finally:
            self.is_generating = False

    async def generate_charges_sociales(self):
        """Generate charges sociales PDF."""
        self.is_generating = True
        self.charges_data = ""

        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)

            if df.is_empty():
                self.pdf_status = "error:Aucune donnée disponible"
                return

            company_info = {"name": self.current_company, "address": "", "siret": ""}
            pdf_service = PDFGeneratorService(company_info)

            employees_data = df.to_dicts()
            charges_buffer = pdf_service.charges_sociales_gen.generate_charges_sociales(
                employees_data, self.current_period
            )

            import base64
            self.charges_data = base64.b64encode(charges_buffer.getvalue()).decode()
            self.pdf_status = "success:État des charges sociales généré avec succès"

        except Exception as e:
            self.pdf_status = f"error:{str(e)}"
        finally:
            self.is_generating = False

    async def generate_recap_annuel(self):
        """Generate annual recap PDF."""
        if not self.recap_year:
            self.pdf_status = "error:Veuillez saisir une année"
            return

        self.is_generating = True
        self.recap_data = ""

        try:
            year = int(self.recap_year)
            company_info = {"name": self.current_company, "address": "", "siret": ""}
            pdf_service = PDFGeneratorService(company_info)

            recap_buffer = pdf_service.recap_gen.generate_recap_paie(
                self.current_company, year
            )

            import base64
            self.recap_data = base64.b64encode(recap_buffer.getvalue()).decode()
            self.pdf_status = f"success:Récapitulatif annuel {year} généré avec succès"

        except ValueError:
            self.pdf_status = "error:Année invalide"
        except Exception as e:
            self.pdf_status = f"error:{str(e)}"
        finally:
            self.is_generating = False

    @rx.var
    def progress_percentage(self) -> int:
        """Calculate progress percentage."""
        if self.total_items == 0:
            return 0
        return int((self.progress / self.total_items) * 100)


def mode_radio_card(icon: str, label: str, value: str) -> rx.Component:
    """Premium radio card for mode selection."""
    return rx.box(
        rx.vstack(
            rx.icon(icon, size=32, color=COLORS["primary-600"], stroke_width=1.5),
            rx.text(
                label,
                size=BODY_MD["size"],
                weight="medium",
                color=COLORS["primary-900"],
            ),
            spacing="3",
            align="center",
        ),
        padding="1.5rem",
        border=f"2px solid {COLORS['neutral-200']}",
        border_radius=RADIUS["card"],
        cursor="pointer",
        transition="all 0.2s ease",
        _hover={
            "border_color": COLORS["primary-300"],
            "bg": COLORS["primary-50"],
        },
    )


def index() -> rx.Component:
    """Premium PDF generation page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    # Page header
                    rx.vstack(
                        rx.heading(
                            "Génération PDF",
                            size=HEADING_XL["size"],
                            weight=HEADING_XL["weight"],
                            letter_spacing=HEADING_XL["letter_spacing"],
                            color=COLORS["primary-900"],
                        ),
                        rx.text(
                            "Générez les bulletins de paie, journaux et provisions",
                            size=BODY_MD["size"],
                            color=COLORS["neutral-600"],
                        ),
                        spacing="2",
                        align="start",
                    ),

                    # Selection warning
                    rx.cond(
                        ~GlobalState.has_selection,
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-alert", size=20, color=COLORS["warning-600"]),
                                rx.text(
                                    "Sélectionnez d'abord une société et une période",
                                    size=BODY_SM["size"],
                                    color=COLORS["warning-600"],
                                ),
                                spacing="2",
                            ),
                            bg=COLORS["warning-100"],
                            border=f"1px solid {COLORS['warning-600']}",
                            border_radius=RADIUS["lg"],
                            padding="1rem",
                        ),
                        rx.fragment(),
                    ),

                    # Premium tabs
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger(
                                "Bulletins de paie",
                                value="paystubs",
                                style={
                                    "padding": "0.75rem 1.5rem",
                                    "font_weight": "500",
                                    "color": COLORS["neutral-600"],
                                    "border_bottom": "2px solid transparent",
                                    "_selected": {
                                        "color": COLORS["primary-600"],
                                        "border_bottom_color": COLORS["primary-600"],
                                    },
                                },
                            ),
                            rx.tabs.trigger(
                                "Journal de paie",
                                value="journal",
                                style={
                                    "padding": "0.75rem 1.5rem",
                                    "font_weight": "500",
                                    "color": COLORS["neutral-600"],
                                    "border_bottom": "2px solid transparent",
                                    "_selected": {
                                        "color": COLORS["primary-600"],
                                        "border_bottom_color": COLORS["primary-600"],
                                    },
                                },
                            ),
                            rx.tabs.trigger(
                                "Provision CP",
                                value="pto",
                                style={
                                    "padding": "0.75rem 1.5rem",
                                    "font_weight": "500",
                                    "color": COLORS["neutral-600"],
                                    "border_bottom": "2px solid transparent",
                                    "_selected": {
                                        "color": COLORS["primary-600"],
                                        "border_bottom_color": COLORS["primary-600"],
                                    },
                                },
                            ),
                            rx.tabs.trigger(
                                "Charges Sociales",
                                value="charges",
                                style={
                                    "padding": "0.75rem 1.5rem",
                                    "font_weight": "500",
                                    "color": COLORS["neutral-600"],
                                    "border_bottom": "2px solid transparent",
                                    "_selected": {
                                        "color": COLORS["primary-600"],
                                        "border_bottom_color": COLORS["primary-600"],
                                    },
                                },
                            ),
                            rx.tabs.trigger(
                                "Récapitulatif annuel",
                                value="recap",
                                style={
                                    "padding": "0.75rem 1.5rem",
                                    "font_weight": "500",
                                    "color": COLORS["neutral-600"],
                                    "border_bottom": "2px solid transparent",
                                    "_selected": {
                                        "color": COLORS["primary-600"],
                                        "border_bottom_color": COLORS["primary-600"],
                                    },
                                },
                            ),
                            style={
                                "border_bottom": f"1px solid {COLORS['neutral-200']}",
                            },
                        ),

                        # Paystubs tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading(
                                    "Mode de génération",
                                    size=HEADING_SM["size"],
                                    weight=HEADING_SM["weight"],
                                    color=COLORS["primary-900"],
                                ),

                                # Mode selector with radio cards
                                rx.radio_group.root(
                                    rx.grid(
                                        rx.box(
                                            rx.radio_group.item(
                                                rx.vstack(
                                                    rx.icon("user", size=32, color=COLORS["primary-600"], stroke_width=1.5),
                                                    rx.text(
                                                        "Individuel",
                                                        size=BODY_MD["size"],
                                                        weight="medium",
                                                        color=COLORS["primary-900"],
                                                    ),
                                                    spacing="3",
                                                    align="center",
                                                ),
                                                value="individual",
                                            ),
                                            padding="1.5rem",
                                            border=f"2px solid {COLORS['neutral-200']}",
                                            border_radius=RADIUS["card"],
                                            cursor="pointer",
                                            transition="all 0.2s ease",
                                            _hover={
                                                "border_color": COLORS["primary-300"],
                                                "bg": COLORS["primary-50"],
                                            },
                                        ),
                                        rx.box(
                                            rx.radio_group.item(
                                                rx.vstack(
                                                    rx.icon("users", size=32, color=COLORS["primary-600"], stroke_width=1.5),
                                                    rx.text(
                                                        "Tous les bulletins",
                                                        size=BODY_MD["size"],
                                                        weight="medium",
                                                        color=COLORS["primary-900"],
                                                    ),
                                                    spacing="3",
                                                    align="center",
                                                ),
                                                value="all",
                                            ),
                                            padding="1.5rem",
                                            border=f"2px solid {COLORS['neutral-200']}",
                                            border_radius=RADIUS["card"],
                                            cursor="pointer",
                                            transition="all 0.2s ease",
                                            _hover={
                                                "border_color": COLORS["primary-300"],
                                                "bg": COLORS["primary-50"],
                                            },
                                        ),
                                        columns="2",
                                        spacing=COMPONENT_SPACING["grid_gap"],
                                        width="100%",
                                    ),
                                    value=PDFState.generation_mode,
                                    on_change=PDFState.set_mode,
                                ),

                                # Content based on mode
                                rx.cond(
                                    PDFState.generation_mode == "individual",
                                    rx.vstack(
                                        rx.vstack(
                                            rx.text(
                                                "Sélectionner un employé",
                                                size=LABEL["size"],
                                                weight=LABEL["weight"],
                                                color=COLORS["neutral-500"],
                                                text_transform=LABEL["text_transform"],
                                                letter_spacing=LABEL["letter_spacing"],
                                            ),
                                            rx.select(
                                                PDFState.employee_labels,
                                                placeholder="Choisir un employé...",
                                                value=PDFState.selected_employee,
                                                on_change=PDFState.set_selected_employee,
                                                size="3",
                                                style={
                                                    "width": "100%",
                                                    "bg": COLORS["white"],
                                                    "border": f"1px solid {COLORS['neutral-300']}",
                                                    "border_radius": RADIUS["lg"],
                                                    "_hover": {"border_color": COLORS["primary-300"]},
                                                    "_focus": {
                                                        "border_color": COLORS["primary-500"],
                                                        "box_shadow": SHADOWS["focus_ring"],
                                                    },
                                                },
                                            ),
                                            spacing="2",
                                            width="100%",
                                        ),
                                        rx.button(
                                            rx.cond(
                                                PDFState.is_generating,
                                                rx.hstack(
                                                    rx.spinner(size="2"),
                                                    rx.text("Génération en cours..."),
                                                    spacing="2",
                                                ),
                                                rx.hstack(
                                                    rx.icon("file-text", size=20),
                                                    rx.text("Générer le bulletin"),
                                                    spacing="2",
                                                ),
                                            ),
                                            on_click=PDFState.generate_individual,
                                            size="3",
                                            disabled=PDFState.is_generating,
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
                                                "_disabled": {
                                                    "bg": COLORS["neutral-300"],
                                                    "cursor": "not-allowed",
                                                },
                                            },
                                        ),
                                        rx.cond(
                                            PDFState.individual_pdf_data != "",
                                            rx.link(
                                                rx.button(
                                                    rx.hstack(
                                                        rx.icon("download", size=20),
                                                        rx.text("Télécharger le PDF"),
                                                        spacing="2",
                                                    ),
                                                    size="3",
                                                    style={
                                                        "bg": COLORS["success-600"],
                                                        "color": COLORS["white"],
                                                        "border_radius": RADIUS["lg"],
                                                        "padding": "0.75rem 1.5rem",
                                                        "_hover": {"bg": COLORS["success-500"]},
                                                    },
                                                ),
                                                href=f"data:application/pdf;base64,{PDFState.individual_pdf_data}",
                                                download=f"bulletin_{PDFState.current_period}.pdf",
                                                is_external=True,
                                            ),
                                            rx.fragment(),
                                        ),
                                        spacing="4",
                                        width="100%",
                                    ),
                                    rx.vstack(
                                        rx.button(
                                            rx.cond(
                                                PDFState.is_generating,
                                                rx.hstack(
                                                    rx.spinner(size="2"),
                                                    rx.text("Génération en cours..."),
                                                    spacing="2",
                                                ),
                                                rx.hstack(
                                                    rx.icon("files", size=20),
                                                    rx.text("Générer tous les bulletins"),
                                                    spacing="2",
                                                ),
                                            ),
                                            on_click=PDFState.generate_all,
                                            size="3",
                                            disabled=PDFState.is_generating,
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
                                                "_disabled": {
                                                    "bg": COLORS["neutral-300"],
                                                    "cursor": "not-allowed",
                                                },
                                            },
                                        ),
                                        # Premium progress bar
                                        rx.cond(
                                            PDFState.is_generating & (PDFState.total_items > 0),
                                            rx.vstack(
                                                rx.hstack(
                                                    rx.text(
                                                        "Progression",
                                                        size=BODY_SM["size"],
                                                        weight="medium",
                                                        color=COLORS["neutral-700"],
                                                    ),
                                                    rx.text(
                                                        f"{PDFState.progress}/{PDFState.total_items}",
                                                        size=BODY_SM["size"],
                                                        color=COLORS["primary-600"],
                                                        weight="bold",
                                                        font_variant_numeric="tabular-nums",
                                                    ),
                                                    justify="between",
                                                    width="100%",
                                                ),
                                                rx.box(
                                                    rx.box(
                                                        width=f"{PDFState.progress_percentage}%",
                                                        height="100%",
                                                        bg=COLORS["primary-600"],
                                                        border_radius=RADIUS["full"],
                                                        transition="width 0.3s ease",
                                                    ),
                                                    width="100%",
                                                    height="8px",
                                                    bg=COLORS["neutral-200"],
                                                    border_radius=RADIUS["full"],
                                                    overflow="hidden",
                                                ),
                                                rx.text(
                                                    f"{PDFState.progress_percentage}%",
                                                    size="1",
                                                    color=COLORS["neutral-600"],
                                                    font_variant_numeric="tabular-nums",
                                                ),
                                                spacing="2",
                                                width="100%",
                                            ),
                                            rx.fragment(),
                                        ),
                                        rx.cond(
                                            PDFState.all_bulletins_data != "",
                                            rx.link(
                                                rx.button(
                                                    rx.hstack(
                                                        rx.icon("download", size=20),
                                                        rx.text("Télécharger le ZIP"),
                                                        spacing="2",
                                                    ),
                                                    size="3",
                                                    style={
                                                        "bg": COLORS["success-600"],
                                                        "color": COLORS["white"],
                                                        "border_radius": RADIUS["lg"],
                                                        "padding": "0.75rem 1.5rem",
                                                        "_hover": {"bg": COLORS["success-500"]},
                                                    },
                                                ),
                                                href=f"data:application/zip;base64,{PDFState.all_bulletins_data}",
                                                download=f"bulletins_{PDFState.current_period}.zip",
                                            ),
                                            rx.fragment(),
                                        ),
                                        spacing="4",
                                        width="100%",
                                    ),
                                ),

                                spacing="5",
                                width="100%",
                            ),
                            value="paystubs",
                            style={"padding_top": "1.5rem"},
                        ),

                        # Journal tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.vstack(
                                    rx.icon("book-open", size=48, color=COLORS["primary-600"], stroke_width=1.5),
                                    rx.heading(
                                        "Journal de paie",
                                        size=HEADING_MD["size"],
                                        weight=HEADING_MD["weight"],
                                        color=COLORS["primary-900"],
                                    ),
                                    rx.text(
                                        "Générez le journal de paie mensuel avec tous les employés",
                                        size=BODY_SM["size"],
                                        color=COLORS["neutral-600"],
                                        text_align="center",
                                    ),
                                    spacing="3",
                                    align="center",
                                ),
                                rx.button(
                                    rx.cond(
                                        PDFState.is_generating,
                                        rx.hstack(
                                            rx.spinner(size="2"),
                                            rx.text("Génération..."),
                                            spacing="2",
                                        ),
                                        rx.hstack(
                                            rx.icon("file-text", size=20),
                                            rx.text("Générer le journal"),
                                            spacing="2",
                                        ),
                                    ),
                                    on_click=PDFState.generate_journal,
                                    size="3",
                                    disabled=PDFState.is_generating,
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
                                        "_disabled": {
                                            "bg": COLORS["neutral-300"],
                                            "cursor": "not-allowed",
                                        },
                                    },
                                ),
                                rx.cond(
                                    PDFState.journal_data != "",
                                    rx.link(
                                        rx.button(
                                            rx.hstack(
                                                rx.icon("download", size=20),
                                                rx.text("Télécharger le journal"),
                                                spacing="2",
                                            ),
                                            size="3",
                                            style={
                                                "bg": COLORS["success-600"],
                                                "color": COLORS["white"],
                                                "border_radius": RADIUS["lg"],
                                                "padding": "0.75rem 1.5rem",
                                                "_hover": {"bg": COLORS["success-500"]},
                                            },
                                        ),
                                        href=f"data:application/pdf;base64,{PDFState.journal_data}",
                                        download=f"journal_{PDFState.current_period}.pdf",
                                    ),
                                    rx.fragment(),
                                ),
                                spacing="5",
                                width="100%",
                                align="center",
                            ),
                            value="journal",
                            style={"padding_top": "1.5rem"},
                        ),

                        # PTO tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.vstack(
                                    rx.icon("calendar-days", size=48, color=COLORS["primary-600"], stroke_width=1.5),
                                    rx.heading(
                                        "Provision congés payés",
                                        size=HEADING_MD["size"],
                                        weight=HEADING_MD["weight"],
                                        color=COLORS["primary-900"],
                                    ),
                                    rx.text(
                                        "Calcule la provision pour congés avec charges sociales à 45%",
                                        size=BODY_SM["size"],
                                        color=COLORS["neutral-600"],
                                        text_align="center",
                                    ),
                                    spacing="3",
                                    align="center",
                                ),
                                rx.button(
                                    rx.cond(
                                        PDFState.is_generating,
                                        rx.hstack(
                                            rx.spinner(size="2"),
                                            rx.text("Génération..."),
                                            spacing="2",
                                        ),
                                        rx.hstack(
                                            rx.icon("file-text", size=20),
                                            rx.text("Générer la provision"),
                                            spacing="2",
                                        ),
                                    ),
                                    on_click=PDFState.generate_provision_cp,
                                    size="3",
                                    disabled=PDFState.is_generating,
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
                                        "_disabled": {
                                            "bg": COLORS["neutral-300"],
                                            "cursor": "not-allowed",
                                        },
                                    },
                                ),
                                rx.cond(
                                    PDFState.provision_data != "",
                                    rx.link(
                                        rx.button(
                                            rx.hstack(
                                                rx.icon("download", size=20),
                                                rx.text("Télécharger la provision"),
                                                spacing="2",
                                            ),
                                            size="3",
                                            style={
                                                "bg": COLORS["success-600"],
                                                "color": COLORS["white"],
                                                "border_radius": RADIUS["lg"],
                                                "padding": "0.75rem 1.5rem",
                                                "_hover": {"bg": COLORS["success-500"]},
                                            },
                                        ),
                                        href=f"data:application/pdf;base64,{PDFState.provision_data}",
                                        download=f"provision_cp_{PDFState.current_period}.pdf",
                                    ),
                                    rx.fragment(),
                                ),
                                spacing="5",
                                width="100%",
                                align="center",
                            ),
                            value="pto",
                            style={"padding_top": "1.5rem"},
                        ),

                        # Charges Sociales tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.box(
                                    rx.vstack(
                                        rx.icon("receipt", size=48, color=COLORS["primary-600"], stroke_width=1.5),
                                        rx.heading(
                                            "État des charges sociales",
                                            size=HEADING_MD["size"],
                                            weight="bold",
                                            color=COLORS["primary-900"],
                                        ),
                                        rx.text(
                                            "Génère un état détaillé des charges patronales et salariales",
                                            size=BODY_SM["size"],
                                            color=COLORS["neutral-600"],
                                            text_align="center",
                                        ),
                                        spacing="3",
                                        align="center",
                                    ),
                                    bg=COLORS["white"],
                                    border=f"1px solid {COLORS['neutral-200']}",
                                    border_radius=RADIUS["card"],
                                    padding="2rem",
                                    box_shadow=SHADOWS["card"],
                                ),
                                rx.button(
                                    rx.cond(
                                        PDFState.is_generating,
                                        rx.hstack(
                                            rx.spinner(size="3"),
                                            rx.text("Génération en cours..."),
                                            spacing="2",
                                        ),
                                        rx.hstack(
                                            rx.icon("file-text", size=20),
                                            rx.text("Générer l'état des charges"),
                                            spacing="2",
                                        ),
                                    ),
                                    on_click=PDFState.generate_charges_sociales,
                                    size="3",
                                    disabled=PDFState.is_generating,
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
                                        "_disabled": {
                                            "bg": COLORS["neutral-300"],
                                            "cursor": "not-allowed",
                                        },
                                    },
                                ),
                                rx.cond(
                                    PDFState.charges_data != "",
                                    rx.link(
                                        rx.button(
                                            rx.hstack(
                                                rx.icon("download", size=20),
                                                rx.text("Télécharger l'état"),
                                                spacing="2",
                                            ),
                                            size="3",
                                            style={
                                                "bg": COLORS["success-600"],
                                                "color": COLORS["white"],
                                                "border_radius": RADIUS["lg"],
                                                "padding": "0.75rem 1.5rem",
                                                "_hover": {"bg": COLORS["success-500"]},
                                            },
                                        ),
                                        href=f"data:application/pdf;base64,{PDFState.charges_data}",
                                        download=f"charges_sociales_{PDFState.current_period}.pdf",
                                    ),
                                    rx.fragment(),
                                ),
                                spacing="5",
                                width="100%",
                                align="center",
                            ),
                            value="charges",
                            style={"padding_top": "1.5rem"},
                        ),

                        # Récapitulatif annuel tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.box(
                                    rx.vstack(
                                        rx.icon("calendar", size=48, color=COLORS["primary-600"], stroke_width=1.5),
                                        rx.heading(
                                            "Récapitulatif annuel de paie",
                                            size=HEADING_MD["size"],
                                            weight="bold",
                                            color=COLORS["primary-900"],
                                        ),
                                        rx.text(
                                            "Génère un récapitulatif annuel par employé (1 page/employé)",
                                            size=BODY_SM["size"],
                                            color=COLORS["neutral-600"],
                                            text_align="center",
                                        ),
                                        spacing="3",
                                        align="center",
                                    ),
                                    bg=COLORS["white"],
                                    border=f"1px solid {COLORS['neutral-200']}",
                                    border_radius=RADIUS["card"],
                                    padding="2rem",
                                    box_shadow=SHADOWS["card"],
                                ),
                                rx.hstack(
                                    rx.input(
                                        placeholder="Année (ex: 2024)",
                                        value=PDFState.recap_year,
                                        on_change=PDFState.set_recap_year,
                                        size="3",
                                        style={
                                            "bg": COLORS["white"],
                                            "border": f"1px solid {COLORS['neutral-200']}",
                                            "border_radius": RADIUS["lg"],
                                            "padding": "0.75rem 1rem",
                                            "_focus": {
                                                "border_color": COLORS["primary-500"],
                                                "box_shadow": SHADOWS["focus_ring"],
                                            },
                                        },
                                    ),
                                        rx.button(
                                            rx.cond(
                                                PDFState.is_generating,
                                                rx.hstack(
                                                    rx.spinner(size="3"),
                                                    rx.text("Génération en cours..."),
                                                    spacing="2",
                                                ),
                                                rx.hstack(
                                                    rx.icon("file-text", size=20),
                                                    rx.text("Générer le récapitulatif"),
                                                    spacing="2",
                                                ),
                                            ),
                                            on_click=PDFState.generate_recap_annuel,
                                            size="3",
                                            disabled=PDFState.is_generating,
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
                                                "_disabled": {
                                                    "bg": COLORS["neutral-300"],
                                                    "cursor": "not-allowed",
                                                },
                                            },
                                        ),
                                    spacing="3",
                                    align="center",
                                ),
                                rx.cond(
                                    PDFState.recap_data != "",
                                    rx.link(
                                        rx.button(
                                            rx.hstack(
                                                rx.icon("download", size=20),
                                                rx.text("Télécharger le récapitulatif"),
                                                spacing="2",
                                            ),
                                            size="3",
                                            style={
                                                "bg": COLORS["success-600"],
                                                "color": COLORS["white"],
                                                "border_radius": RADIUS["lg"],
                                                "padding": "0.75rem 1.5rem",
                                                "_hover": {"bg": COLORS["success-500"]},
                                            },
                                        ),
                                        href=f"data:application/pdf;base64,{PDFState.recap_data}",
                                        download=f"recap_annuel_{PDFState.recap_year}.pdf",
                                    ),
                                    rx.fragment(),
                                ),
                                spacing="5",
                                width="100%",
                                align="center",
                            ),
                            value="recap",
                            style={"padding_top": "1.5rem"},
                        ),

                        default_value="paystubs",
                    ),

                    # Status messages
                    rx.cond(
                        PDFState.pdf_status != "",
                        rx.cond(
                            PDFState.pdf_status.startswith("success:"),
                            rx.box(
                                rx.hstack(
                                    rx.icon("circle-check", size=20, color=COLORS["success-600"]),
                                    rx.text(
                                        PDFState.pdf_status_message,
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
                            rx.cond(
                                PDFState.pdf_status.startswith("error:"),
                                rx.box(
                                    rx.hstack(
                                        rx.icon("circle-alert", size=20, color=COLORS["error-600"]),
                                        rx.text(
                                            PDFState.pdf_status_message,
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
                                rx.box(
                                    rx.hstack(
                                        rx.icon("info", size=20, color=COLORS["info-600"]),
                                        rx.text(
                                            PDFState.pdf_status_message,
                                            size=BODY_SM["size"],
                                            color=COLORS["info-600"],
                                        ),
                                        spacing="2",
                                    ),
                                    bg=COLORS["info-100"],
                                    border=f"1px solid {COLORS['info-600']}",
                                    border_radius=RADIUS["lg"],
                                    padding="1rem",
                                ),
                            ),
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
        on_mount=PDFState.load_employees,
    )
