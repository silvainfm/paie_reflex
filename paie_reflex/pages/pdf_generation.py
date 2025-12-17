"""PDF generation page."""
import reflex as rx
from typing import List, Dict
import zipfile
from io import BytesIO
from pathlib import Path
from ..state import GlobalState, CompanyState
from ..components import navbar, sidebar_nav
from ..services.data_mgt import DataManager
from ..services.pdf_generation import PDFGeneratorService
from ..services.pdf_storage import PDFStorageService, StorageConfigManager


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

    # Cloud storage
    saved_locations: List[str] = []  # Track where PDFs were saved

    @rx.var
    def employee_labels(self) -> List[str]:
        """Get list of employee labels for select dropdown."""
        return [emp["label"] for emp in self.employees]

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
    
    async def generate_individual(self):
        """Generate individual bulletin."""
        if not self.selected_employee:
            self.pdf_status = "Veuillez sélectionner un employé"
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
                self.pdf_status = "Employé non trouvé"
                self.is_generating = False
                return

            # Generate PDF
            company_info = {"name": self.current_company, "address": "", "siret": ""}
            pdf_service = PDFGeneratorService(company_info)

            emp_data = emp_df.to_dicts()[0]
            pdf_buffer = pdf_service.paystub_gen.generate_paystub(emp_data, self.current_period)

            self.progress = 1

            # Save to cloud if configured
            company_state = self.get_state(CompanyState)
            config_mgr = StorageConfigManager(Path("data/config/storage_config.json"))
            storage_config = config_mgr.load_config()

            self.saved_locations = []

            if storage_config and storage_config.enabled:
                storage_service = PDFStorageService(storage_config)
                success, location = storage_service.save_pdf(
                    pdf_buffer,
                    "bulletin",
                    company_state.current_company,
                    company_state.current_company,
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
                self.pdf_status = f"✓ Bulletin généré et sauvegardé dans: {self.saved_locations[0]}"
            else:
                self.pdf_status = "✓ Bulletin généré"

        except Exception as e:
            self.pdf_status = f"Erreur: {str(e)}"
        finally:
            self.is_generating = False
    
    async def generate_all(self):
        """Generate all bulletins as ZIP with progress tracking."""
        self.is_generating = True
        self.progress = 0
        self.all_bulletins_data = ""
        self.pdf_status = "Démarrage de la génération groupée..."

        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)

            employee_data = df.to_dicts()
            self.total_items = len(employee_data)

            company_info = {"name": self.current_company, "address": "", "siret": ""}
            pdf_service = PDFGeneratorService(company_info)

            # Check for cloud storage
            company_state = self.get_state(CompanyState)
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
                            company_state.current_company,
                            company_state.current_company,
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
                    self.pdf_status = f"Génération {self.progress}/{self.total_items}..."

            import base64
            self.all_bulletins_data = base64.b64encode(zip_buffer.getvalue()).decode()

            if self.saved_locations:
                self.pdf_status = f"✓ {self.total_items} bulletins générés et sauvegardés ({len(self.saved_locations)} fichiers)"
            else:
                self.pdf_status = f"✓ {self.total_items} bulletins générés"

        except Exception as e:
            self.pdf_status = f"Erreur: {str(e)}"
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
            self.pdf_status = "✓ Journal généré"

        except Exception as e:
            self.pdf_status = f"Erreur: {str(e)}"
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
            self.pdf_status = "✓ Provision CP générée"

        except Exception as e:
            self.pdf_status = f"Erreur: {str(e)}"
        finally:
            self.is_generating = False

    @rx.var
    def progress_percentage(self) -> int:
        """Calculate progress percentage."""
        if self.total_items == 0:
            return 0
        return int((self.progress / self.total_items) * 100)


def index() -> rx.Component:
    """PDF generation page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    rx.heading("Génération PDF", size="8", margin_bottom="1rem"),

                    rx.cond(
                        ~GlobalState.has_selection,
                        rx.callout(
                            "Sélectionnez d'abord une société et une période",
                            icon="alert-circle",
                            color_scheme="red",
                        ),
                        rx.fragment(),
                    ),

                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("Bulletins", value="paystubs"),
                            rx.tabs.trigger("Journal de paie", value="journal"),
                            rx.tabs.trigger("Provision CP", value="pto"),
                        ),
                        
                        # Paystubs tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Générer les bulletins", size="6"),

                                rx.radio_group.root(
                                    rx.hstack(
                                        rx.radio_group.item("Individuel", value="individual"),
                                        rx.radio_group.item("Tous les bulletins", value="all"),
                                        spacing="4",
                                    ),
                                    value=PDFState.generation_mode,
                                    on_change=PDFState.set_mode,
                                ),

                                rx.cond(
                                    PDFState.generation_mode == "individual",
                                    rx.vstack(
                                        rx.select(
                                            PDFState.employee_labels,
                                            placeholder="Sélectionner un employé",
                                            value=PDFState.selected_employee,
                                            on_change=PDFState.set_selected_employee,
                                        ),
                                        rx.button(
                                            rx.cond(
                                                PDFState.is_generating,
                                                rx.hstack(
                                                    rx.spinner(size="3"),
                                                    rx.text("Génération..."),
                                                    spacing="2",
                                                ),
                                                rx.text("Générer individuel"),
                                            ),
                                            on_click=PDFState.generate_individual,
                                            size="3",
                                            disabled=PDFState.is_generating,
                                        ),
                                        rx.cond(
                                            PDFState.individual_pdf_data,
                                            rx.link(
                                                rx.button("Télécharger PDF", size="3", variant="soft"),
                                                href=f"data:application/pdf;base64,{PDFState.individual_pdf_data}",
                                                download=f"bulletin_{PDFState.current_period}.pdf",
                                                is_external=True,
                                            ),
                                            rx.fragment(),
                                        ),
                                        spacing="3",
                                    ),
                                    rx.vstack(
                                        rx.button(
                                            rx.cond(
                                                PDFState.is_generating,
                                                rx.hstack(
                                                    rx.spinner(size="3"),
                                                    rx.text("Génération..."),
                                                    spacing="2",
                                                ),
                                                rx.text("Générer tous les bulletins"),
                                            ),
                                            on_click=PDFState.generate_all,
                                            size="3",
                                            disabled=PDFState.is_generating,
                                        ),
                                        # Progress bar for bulk generation
                                        rx.cond(
                                            PDFState.is_generating & (PDFState.total_items > 0),
                                            rx.vstack(
                                                rx.progress(
                                                    value=PDFState.progress_percentage,
                                                    max=100,
                                                    width="100%",
                                                ),
                                                rx.text(
                                                    f"{PDFState.progress}/{PDFState.total_items} bulletins ({PDFState.progress_percentage}%)",
                                                    size="2",
                                                    color="#6c757d",
                                                ),
                                                spacing="2",
                                                width="100%",
                                            ),
                                            rx.fragment(),
                                        ),
                                        rx.cond(
                                            PDFState.all_bulletins_data,
                                            rx.link(
                                                rx.button("Télécharger ZIP", size="3", variant="soft"),
                                                href=f"data:application/zip;base64,{PDFState.all_bulletins_data}",
                                                download=f"bulletins_{PDFState.current_period}.zip",
                                            ),
                                            rx.fragment(),
                                        ),
                                        spacing="3",
                                    ),
                                ),

                                spacing="4",
                            ),
                            value="paystubs",
                        ),

                        # Journal tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Générer le journal de paie", size="6"),
                                rx.button(
                                    rx.cond(
                                        PDFState.is_generating,
                                        rx.hstack(
                                            rx.spinner(size="3"),
                                            rx.text("Génération..."),
                                            spacing="2",
                                        ),
                                        rx.text("Générer le journal"),
                                    ),
                                    on_click=PDFState.generate_journal,
                                    size="3",
                                    disabled=PDFState.is_generating,
                                ),
                                rx.cond(
                                    PDFState.journal_data,
                                    rx.link(
                                        rx.button("Télécharger le journal", size="3", variant="soft"),
                                        href=f"data:application/pdf;base64,{PDFState.journal_data}",
                                        download=f"journal_{PDFState.current_period}.pdf",
                                    ),
                                    rx.fragment(),
                                ),
                                spacing="4",
                            ),
                            value="journal",
                        ),

                        # PTO tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Générer la provision CP", size="6"),
                                rx.text("Calcule la provision pour congés avec charges sociales à 45%", size="2", color="#6c757d"),
                                rx.button(
                                    rx.cond(
                                        PDFState.is_generating,
                                        rx.hstack(
                                            rx.spinner(size="3"),
                                            rx.text("Génération..."),
                                            spacing="2",
                                        ),
                                        rx.text("Générer la provision"),
                                    ),
                                    on_click=PDFState.generate_provision_cp,
                                    size="3",
                                    disabled=PDFState.is_generating,
                                ),
                                rx.cond(
                                    PDFState.provision_data,
                                    rx.link(
                                        rx.button("Télécharger la provision", size="3", variant="soft"),
                                        href=f"data:application/pdf;base64,{PDFState.provision_data}",
                                        download=f"provision_cp_{PDFState.current_period}.pdf",
                                    ),
                                    rx.fragment(),
                                ),
                                spacing="4",
                            ),
                            value="pto",
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
