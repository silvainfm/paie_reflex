"""PDF generation page."""
import reflex as rx
from typing import List, Dict
import zipfile
from io import BytesIO
from ..state import GlobalState
from ..components import navbar, sidebar_nav
from ..services.data_mgt import DataManager
from ..services.pdf_generation import PDFGeneratorService


class PDFState(GlobalState):
    """State for PDF generation."""
    
    generation_mode: str = "individual"
    selected_employee: str = ""
    employees: List[Dict] = []
    pdf_status: str = ""
    
    # Download triggers
    individual_pdf_data: str = ""
    all_bulletins_data: str = ""
    journal_data: str = ""
    provision_data: str = ""
    
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
    
    async def generate_individual(self):
        """Generate individual bulletin."""
        if not self.selected_employee:
            self.pdf_status = "Please select an employee"
            return
        
        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)
            
            # Find employee
            matricule = self.selected_employee.split(' - ')[0]
            emp_df = df.filter(df['matricule'] == matricule)
            
            if emp_df.is_empty():
                self.pdf_status = "Employee not found"
                return
            
            # Generate PDF
            company_info = {"name": self.current_company, "address": "", "siret": ""}
            pdf_service = PDFGeneratorService(company_info)
            
            emp_data = emp_df.to_dicts()[0]
            pdf_buffer = pdf_service.paystub_gen.generate_paystub(emp_data, self.current_period)
            
            # Convert to base64 for download
            import base64
            self.individual_pdf_data = base64.b64encode(pdf_buffer.getvalue()).decode()
            self.pdf_status = "✓ Bulletin generated"
            
        except Exception as e:
            self.pdf_status = f"Error: {str(e)}"
    
    async def generate_all(self):
        """Generate all bulletins as ZIP."""
        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)
            
            company_info = {"name": self.current_company, "address": "", "siret": ""}
            pdf_service = PDFGeneratorService(company_info)
            
            # Generate all PDFs
            documents = pdf_service.generate_monthly_documents(df, self.current_period)
            
            # Create ZIP
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for paystub in documents['paystubs']:
                    filename = f"bulletin_{paystub['matricule']}_{paystub['nom']}.pdf"
                    zf.writestr(filename, paystub['buffer'].getvalue())
            
            import base64
            self.all_bulletins_data = base64.b64encode(zip_buffer.getvalue()).decode()
            self.pdf_status = f"✓ Generated {len(documents['paystubs'])} bulletins"
            
        except Exception as e:
            self.pdf_status = f"Error: {str(e)}"
    
    async def generate_journal(self):
        """Generate pay journal."""
        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)
            
            company_info = {"name": self.current_company, "address": "", "siret": ""}
            pdf_service = PDFGeneratorService(company_info)
            
            journal_buffer = pdf_service.journal_gen.generate_journal(df.to_dicts(), self.current_period)
            
            import base64
            self.journal_data = base64.b64encode(journal_buffer.getvalue()).decode()
            self.pdf_status = "✓ Journal generated"
            
        except Exception as e:
            self.pdf_status = f"Error: {str(e)}"
    
    async def generate_provision_cp(self):
        """Generate PTO provision."""
        try:
            month, year = map(int, self.current_period.split('-'))
            df = DataManager.load_period_data(self.current_company, month, year)
            
            company_info = {"name": self.current_company, "address": "", "siret": ""}
            pdf_service = PDFGeneratorService(company_info)
            
            provisions_data = pdf_service._prepare_provisions_data(df)
            provision_buffer = pdf_service.pto_gen.generate_provision(provisions_data, self.current_period)
            
            import base64
            self.provision_data = base64.b64encode(provision_buffer.getvalue()).decode()
            self.pdf_status = "✓ PTO provision generated"
            
        except Exception as e:
            self.pdf_status = f"Error: {str(e)}"


def index() -> rx.Component:
    """PDF generation page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    rx.heading("PDF Generation", size="8", margin_bottom="1rem"),
                    
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
                            rx.tabs.trigger("Paystubs", value="paystubs"),
                            rx.tabs.trigger("Pay Journal", value="journal"),
                            rx.tabs.trigger("PTO Provision", value="pto"),
                        ),
                        
                        # Paystubs tab
                        rx.tabs.content(
                            rx.vstack(
                                rx.heading("Generate Paystubs", size="6"),
                                
                                rx.radio_group(
                                    rx.hstack(
                                        rx.radio("Individual", value="individual"),
                                        rx.radio("All Bulletins", value="all"),
                                        spacing="4",
                                    ),
                                    value=PDFState.generation_mode,
                                    on_change=PDFState.set_mode,
                                ),
                                
                                rx.cond(
                                    PDFState.generation_mode == "individual",
                                    rx.vstack(
                                        rx.select(
                                            [emp["label"] for emp in PDFState.employees],
                                            placeholder="Select employee",
                                            value=PDFState.selected_employee,
                                            on_change=PDFState.selected_employee.set,
                                        ),
                                        rx.button(
                                            "Generate Individual",
                                            on_click=PDFState.generate_individual,
                                            size="3",
                                        ),
                                        rx.cond(
                                            PDFState.individual_pdf_data,
                                            rx.download(
                                                rx.button("Download PDF", size="3", variant="soft"),
                                                url=f"data:application/pdf;base64,{PDFState.individual_pdf_data}",
                                                filename=f"bulletin_{PDFState.current_period}.pdf",
                                            ),
                                            rx.fragment(),
                                        ),
                                        spacing="3",
                                    ),
                                    rx.vstack(
                                        rx.button(
                                            "Generate All Bulletins",
                                            on_click=PDFState.generate_all,
                                            size="3",
                                        ),
                                        rx.cond(
                                            PDFState.all_bulletins_data,
                                            rx.download(
                                                rx.button("Download ZIP", size="3", variant="soft"),
                                                url=f"data:application/zip;base64,{PDFState.all_bulletins_data}",
                                                filename=f"bulletins_{PDFState.current_period}.zip",
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
                                rx.heading("Generate Pay Journal", size="6"),
                                rx.button(
                                    "Generate Journal",
                                    on_click=PDFState.generate_journal,
                                    size="3",
                                ),
                                rx.cond(
                                    PDFState.journal_data,
                                    rx.download(
                                        rx.button("Download Journal", size="3", variant="soft"),
                                        url=f"data:application/pdf;base64,{PDFState.journal_data}",
                                        filename=f"journal_{PDFState.current_period}.pdf",
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
                                rx.heading("Generate PTO Provision", size="6"),
                                rx.text("Calculates accrued leave provision with 45% social charges", size="2", color="#6c757d"),
                                rx.button(
                                    "Generate Provision",
                                    on_click=PDFState.generate_provision_cp,
                                    size="3",
                                ),
                                rx.cond(
                                    PDFState.provision_data,
                                    rx.download(
                                        rx.button("Download Provision", size="3", variant="soft"),
                                        url=f"data:application/pdf;base64,{PDFState.provision_data}",
                                        filename=f"provision_cp_{PDFState.current_period}.pdf",
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
