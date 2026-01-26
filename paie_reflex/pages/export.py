"""Export page for downloading payroll data."""
import reflex as rx
from typing import Dict, List
from io import BytesIO
from xlsxwriter import Workbook
import base64
from pathlib import Path
from ..state import GlobalState
from ..components import navbar, sidebar_nav
from ..services.data_mgt import DataManager
from ..services.dsm_xml_generator import DSMXMLGenerator
from ..services.email_archive import EmailConfigManager, create_email_distribution_system
from ..services.pdf_generation import PDFGeneratorService


class ExportState(GlobalState):
    """State for export page."""

    export_status: str = ""
    employee_count: int = 0
    total_brut: float = 0
    total_net: float = 0
    total_charges_sal: float = 0
    total_charges_pat: float = 0
    total_cout: float = 0

    # Download data
    excel_data: str = ""
    dsm_data: str = ""

    # DSM config
    employer_number: str = ""
    plafond_t1: float = 3428.00

    # Client validation email
    client_name: str = ""
    client_email: str = ""
    test_mode: bool = True
    protect_pdfs: bool = False
    pdf_password: str = ""
    email_status: str = ""
    email_result: Dict = {}
    
    def set_client_name(self, value):
        self.client_name = value
    def set_client_email(self, value):
        self.client_email = value
    def set_test_mode(self, value):
        self.test_mode = value
    def set_protect_pdfs(self, value):
        self.protect_pdfs = value
    def set_pdf_password(self, value):
        self.pdf_password = value

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
            self.total_charges_sal = summary.get('total_charges_sal', 0)
            self.total_charges_pat = summary.get('total_charges_pat', 0)
            self.total_cout = summary.get('total_cout', 0)

        # Load employer number and client contact
        company_details = DataManager.get_company_details(self.current_company)
        if company_details:
            self.employer_number = company_details.get('employer_number_monaco', '')
            self.client_name = company_details.get('point_contact', '')
            self.client_email = company_details.get('email', '')
    
    async def generate_excel(self):
        """Generate Excel export."""
        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)

            if df.is_empty():
                self.export_status = "Aucune donnée à exporter"
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
            self.export_status = "✓ Excel généré"

        except Exception as e:
            self.export_status = f"Erreur: {str(e)}"
    
    async def generate_dsm_xml(self):
        """Generate DSM XML."""
        if not self.employer_number:
            self.export_status = "Numéro employeur requis pour la DSM"
            return

        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)

            if df.is_empty():
                self.export_status = "Aucune donnée à exporter"
                return
            
            # Generate XML
            generator = DSMXMLGenerator(self.employer_number, self.plafond_t1)
            xml_buffer = generator.generate_dsm_xml(df, self.current_period)
            
            self.dsm_data = base64.b64encode(xml_buffer.getvalue()).decode()
            self.export_status = "✓ DSM XML généré"

        except Exception as e:
            self.export_status = f"Erreur: {str(e)}"

    async def send_validation_email(self):
        """Send validation email to client with all documents."""
        try:
            # Check email config
            email_config_path = Path("data/config/email_config.json")
            if not email_config_path.exists():
                self.email_status = "Configuration email manquante. Configurez d'abord l'email dans Config → Email"
                return

            # Validate inputs
            if not self.client_email:
                self.email_status = "Email client requis"
                return

            if self.protect_pdfs and not self.pdf_password:
                self.email_status = "Mot de passe requis pour protéger les PDFs"
                return

            self.email_status = "Génération des documents..."

            # Convert period
            month, year = map(int, self.current_period.split('-'))
            period_str = f"{year}-{month:02d}"

            # Load payroll data
            df = DataManager.load_period_data(self.current_company, month, year)
            if df.is_empty():
                self.email_status = "Aucune donnée à envoyer"
                return

            # Get company details
            company_details = DataManager.get_company_details(self.current_company)
            company_info = {
                'name': company_details.get('name', self.current_company),
                'siret': company_details.get('siret', ''),
                'address': company_details.get('address', ''),
                'phone': company_details.get('phone', ''),
                'email': company_details.get('email', '')
            }

            # Initialize PDF generator
            pdf_gen = PDFGeneratorService(company_info)

            # Generate all documents
            self.email_status = "Génération des PDFs..."
            password = self.pdf_password if self.protect_pdfs else None

            docs = pdf_gen.generate_monthly_documents(
                df,
                period_str,
                password=password
            )

            # Prepare payroll summary
            payroll_summary = {
                'total_brut': self.total_brut,
                'total_charges_sal': self.total_charges_sal,
                'total_charges_pat': self.total_charges_pat,
                'total_net': self.total_net,
                'total_cout': self.total_cout
            }

            # Create email system
            self.email_status = "Envoi de l'email..."
            system = create_email_distribution_system()

            # Send validation email
            result = system['email_service'].send_validation_email(
                client_email=self.client_email,
                company_name=company_info['name'],
                paystubs_buffers=docs['paystubs'],
                journal_buffer=docs['journal'],
                pto_buffer=docs['pto_provision'],
                period=period_str,
                payroll_summary=payroll_summary,
                test_mode=self.test_mode
            )

            if result['success']:
                mode_text = " (MODE TEST)" if self.test_mode else ""
                self.email_status = f"✓ Email envoyé avec succès{mode_text} à {self.client_email}"
                self.email_result = result
            else:
                self.email_status = f"Échec: {result.get('error', 'Erreur inconnue')}"
                self.email_result = result

        except Exception as e:
            self.email_status = f"Erreur: {str(e)}"
            self.email_result = {}


def index() -> rx.Component:
    """Export page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    rx.heading("Export des résultats", size="8", margin_bottom="1rem"),

                    rx.cond(
                        ~GlobalState.has_selection,
                        rx.callout(
                            "Sélectionnez d'abord une société et une période",
                            icon="circle-alert",
                            color_scheme="red",
                        ),
                        rx.fragment(),
                    ),

                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("Export Excel", value="excel"),
                            rx.tabs.trigger("DSM Monaco", value="dsm"),
                            rx.tabs.trigger("Validation Client", value="validation"),
                        ),
                        
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Exporter vers Excel", size="6"),

                                rx.grid(
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Employés", size="2", color="#6c757d"),
                                            rx.text(ExportState.employee_count, size="5", weight="bold"),
                                            spacing="2",
                                        ),
                                        bg="white",
                                        padding="1.5rem",
                                        border_radius="8px",
                                    ),
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Masse salariale brute", size="2", color="#6c757d"),
                                            rx.text(f"{ExportState.total_brut:,.0f} €", size="5", weight="bold"),
                                            spacing="2",
                                        ),
                                        bg="white",
                                        padding="1.5rem",
                                        border_radius="8px",
                                    ),
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Net à payer", size="2", color="#6c757d"),
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
                                    "Générer Excel",
                                    on_click=ExportState.generate_excel,
                                    size="3",
                                ),

                                rx.cond(
                                    ExportState.excel_data,
                                    rx.link(
                                        rx.button("Télécharger Excel", size="3", variant="soft"),
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
                                rx.heading("Déclaration DSM Monaco", size="6"),
                                rx.text("Générer le fichier XML pour la déclaration sociale monégasque", size="2", color="#6c757d"),

                                rx.cond(
                                    ExportState.employer_number,
                                    rx.callout(
                                        f"Numéro employeur: {ExportState.employer_number}",
                                        icon="circle-check",
                                        color_scheme="green",
                                    ),
                                    rx.callout(
                                        "Numéro employeur non configuré. Définir dans Config → Société",
                                        icon="circle-alert",
                                        color_scheme="red",
                                    ),
                                ),

                                rx.grid(
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Employés", size="2", color="#6c757d"),
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
                                    "Générer DSM XML",
                                    on_click=ExportState.generate_dsm_xml,
                                    size="3",
                                    disabled=~ExportState.employer_number.bool(),
                                ),

                                rx.cond(
                                    ExportState.dsm_data,
                                    rx.link(
                                        rx.button("Télécharger DSM XML", size="3", variant="soft"),
                                        url=f"data:application/xml;base64,{ExportState.dsm_data}",
                                        filename=f"DSM_{ExportState.employer_number}_{ExportState.current_period}.xml",
                                    ),
                                    rx.fragment(),
                                ),
                                
                                spacing="4",
                            ),
                            value="dsm",
                        ),

                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Envoi validation client", size="6"),
                                rx.text("Envoyer tous les documents de paie au client pour validation", size="2", color="#6c757d"),

                                # Client contact info
                                rx.vstack(
                                    rx.text("Contact client", weight="bold"),
                                    rx.cond(
                                        GlobalState.is_admin,
                                        rx.vstack(
                                            rx.input(
                                                placeholder="Nom du contact",
                                                value=ExportState.client_name,
                                                on_change=ExportState.set_client_name,
                                            ),
                                            rx.input(
                                                placeholder="Email client",
                                                value=ExportState.client_email,
                                                on_change=ExportState.set_client_email,
                                                type="email",
                                            ),
                                            spacing="2",
                                            width="100%",
                                        ),
                                        rx.vstack(
                                            rx.input(
                                                value=ExportState.client_name,
                                                read_only=True,
                                                disabled=True,
                                            ),
                                            rx.input(
                                                value=ExportState.client_email,
                                                type="email",
                                                read_only=True,
                                                disabled=True,
                                            ),
                                            rx.text("(Contact configuré dans la base de données - Admin uniquement)", size="1", color="#6c757d"),
                                            spacing="2",
                                            width="100%",
                                        ),
                                    ),
                                    spacing="2",
                                    width="100%",
                                ),

                                rx.divider(),

                                # Options
                                rx.vstack(
                                    rx.hstack(
                                        rx.switch(
                                            checked=ExportState.test_mode,
                                            on_change=ExportState.set_test_mode,
                                        ),
                                        rx.text("Mode test (pas d'envoi réel)", weight="bold"),
                                        spacing="2",
                                    ),
                                    rx.hstack(
                                        rx.switch(
                                            checked=ExportState.protect_pdfs,
                                            on_change=ExportState.set_protect_pdfs,
                                        ),
                                        rx.text("Protéger les PDFs par mot de passe", weight="bold"),
                                        spacing="2",
                                    ),
                                    rx.cond(
                                        ExportState.protect_pdfs,
                                        rx.input(
                                            placeholder="Mot de passe pour les PDFs",
                                            type="password",
                                            value=ExportState.pdf_password,
                                            on_change=ExportState.set_pdf_password,
                                        ),
                                        rx.fragment(),
                                    ),
                                    spacing="3",
                                    width="100%",
                                ),

                                rx.divider(),

                                # Documents preview
                                rx.vstack(
                                    rx.text("Documents à joindre:", weight="bold"),
                                    rx.hstack(
                                        rx.badge("Bulletins de paie (ZIP)", color_scheme="blue"),
                                        rx.badge("Journal de paie (PDF)", color_scheme="green"),
                                        rx.badge("Provision CP (PDF)", color_scheme="purple"),
                                        spacing="2",
                                    ),
                                    spacing="2",
                                ),

                                rx.divider(),

                                # Financial summary
                                rx.heading("Récapitulatif financier", size="5"),
                                rx.grid(
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Employés", size="2", color="#6c757d"),
                                            rx.text(ExportState.employee_count, size="5", weight="bold"),
                                            spacing="2",
                                        ),
                                        bg="white",
                                        padding="1.5rem",
                                        border_radius="8px",
                                    ),
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Brut total", size="2", color="#6c757d"),
                                            rx.text(f"{ExportState.total_brut:,.0f} €", size="5", weight="bold"),
                                            spacing="2",
                                        ),
                                        bg="white",
                                        padding="1.5rem",
                                        border_radius="8px",
                                    ),
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Charges sal.", size="2", color="#6c757d"),
                                            rx.text(f"{ExportState.total_charges_sal:,.0f} €", size="5", weight="bold"),
                                            spacing="2",
                                        ),
                                        bg="white",
                                        padding="1.5rem",
                                        border_radius="8px",
                                    ),
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Charges pat.", size="2", color="#6c757d"),
                                            rx.text(f"{ExportState.total_charges_pat:,.0f} €", size="5", weight="bold"),
                                            spacing="2",
                                        ),
                                        bg="white",
                                        padding="1.5rem",
                                        border_radius="8px",
                                    ),
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Net à payer", size="2", color="#6c757d"),
                                            rx.text(f"{ExportState.total_net:,.0f} €", size="5", weight="bold", color="green"),
                                            spacing="2",
                                        ),
                                        bg="white",
                                        padding="1.5rem",
                                        border_radius="8px",
                                    ),
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Coût total employeur", size="2", color="#6c757d"),
                                            rx.text(f"{ExportState.total_cout:,.0f} €", size="5", weight="bold", color="red"),
                                            spacing="2",
                                        ),
                                        bg="white",
                                        padding="1.5rem",
                                        border_radius="8px",
                                    ),
                                    columns="3",
                                    spacing="4",
                                ),

                                rx.divider(),

                                # Send button
                                rx.button(
                                    "Envoyer l'email de validation",
                                    on_click=ExportState.send_validation_email,
                                    size="3",
                                    color_scheme="blue",
                                    disabled=~ExportState.client_email.bool(),
                                ),

                                # Status
                                rx.cond(
                                    ExportState.email_status != "",
                                    rx.cond(
                                        ExportState.email_status.to_string().contains("✓"),
                                        rx.callout(
                                            ExportState.email_status,
                                            icon="circle-check",
                                            color_scheme="green",
                                        ),
                                        rx.callout(
                                            ExportState.email_status,
                                            icon="circle-alert",
                                            color_scheme="red",
                                        ),
                                    ),
                                    rx.fragment(),
                                ),

                                spacing="4",
                            ),
                            value="validation",
                        ),

                        default_value="excel",
                    ),
                    
                    rx.cond(
                        ExportState.export_status,
                        rx.callout(
                            ExportState.export_status,
                            icon="circle-check",
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
