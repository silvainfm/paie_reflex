"""Client Portal - Data entry for clients."""

import reflex as rx
from ..state import GlobalState
from ..components import navbar, sidebar_nav
from ..services.data_mgt import DataManager, ClientInputsManager
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
from datetime import datetime
import polars as pl


# Field configuration with validation rules
EDITABLE_FIELDS = {
    # Hours
    "base_heures": {"label": "Heures de base", "type": "number", "default": 169.0, "min": 0, "max": 250, "category": "hours"},
    "heures_conges_payes": {"label": "Heures CP", "type": "number", "default": 0.0, "min": 0, "max": 169, "category": "hours"},
    "heures_absence": {"label": "Heures absence", "type": "number", "default": 0.0, "min": 0, "max": 169, "category": "hours"},
    "type_absence": {"label": "Type absence", "type": "select", "options": ["", "maladie", "non_payee", "conge_sans_solde", "maternite", "accident_travail"], "default": "", "category": "hours"},
    "heures_sup_125": {"label": "HS 125%", "type": "number", "default": 0.0, "min": 0, "max": 50, "category": "hours"},
    "heures_sup_150": {"label": "HS 150%", "type": "number", "default": 0.0, "min": 0, "max": 50, "category": "hours"},
    # Salary
    "salaire_base": {"label": "Salaire de base", "type": "number", "default": 0.0, "min": 0, "max": 50000, "category": "salary"},
    "prime": {"label": "Prime", "type": "number", "default": 0.0, "min": 0, "max": 20000, "category": "salary"},
    "type_prime": {"label": "Type prime", "type": "select", "options": ["", "performance", "anciennete", "exceptionnelle", "objectif"], "default": "", "category": "salary"},
    "prime_exceptionnelle": {"label": "Prime exceptionnelle", "type": "number", "default": 0.0, "min": 0, "max": 20000, "category": "salary"},
    # Benefits
    "tickets_restaurant": {"label": "Tickets restaurant (nb)", "type": "number", "default": 0.0, "min": 0, "max": 25, "category": "benefits"},
    "avantage_logement": {"label": "Avantage logement", "type": "number", "default": 0.0, "min": 0, "max": 5000, "category": "benefits"},
    "avantage_transport": {"label": "Avantage transport", "type": "number", "default": 0.0, "min": 0, "max": 1000, "category": "benefits"},
    # Other
    "remarques": {"label": "Remarques", "type": "text", "default": "", "category": "other"},
}


class ClientPortalState(rx.State):
    """Client portal page state."""
    
    employees: list[dict] = []
    selected_employee: str = ""
    selected_employee_data: dict = {}
    form_values: dict = {}
    change_history: list[dict] = []
    status_message: str = ""
    active_tab: str = "individual"
    
    # Summary stats
    total_employees: int = 0
    total_absences: float = 0.0
    with_remarks: int = 0
    
    async def load_employees(self):
        """Load employees for current period."""
        global_state = await self.get_state(GlobalState)
        
        if not global_state.current_company or not global_state.current_period:
            self.employees = []
            return
        
        month, year = map(int, global_state.current_period.split('-'))
        
        # Load current period
        df = DataManager.load_period_data(global_state.current_company, month, year)
        
        # If empty, try previous period
        if df.is_empty():
            prev_month = month - 1
            prev_year = year
            if prev_month <= 0:
                prev_month = 12
                prev_year -= 1
            df = DataManager.load_period_data(global_state.current_company, prev_month, prev_year)
        
        if not df.is_empty():
            # Select display columns
            cols = ["matricule", "nom", "prenom", "base_heures", "salaire_base", "prime", "heures_absence", "remarques"]
            available_cols = [c for c in cols if c in df.columns]
            self.employees = df.select(available_cols).to_dicts()
            
            # Calculate stats
            self.total_employees = len(self.employees)
            if "heures_absence" in df.columns:
                self.total_absences = df["heures_absence"].sum() or 0.0
            if "remarques" in df.columns:
                self.with_remarks = df.filter(
                    (pl.col("remarques").is_not_null()) & (pl.col("remarques") != "")
                ).height
        else:
            self.employees = []
            self.total_employees = 0
            self.total_absences = 0.0
            self.with_remarks = 0
    
    async def select_employee(self, matricule: str):
        """Select an employee for editing."""
        self.selected_employee = matricule
        
        global_state = await self.get_state(GlobalState)
        month, year = map(int, global_state.current_period.split('-'))
        
        df = DataManager.load_period_data(global_state.current_company, month, year)
        
        if not df.is_empty():
            emp_df = df.filter(pl.col("matricule") == matricule)
            if not emp_df.is_empty():
                self.selected_employee_data = emp_df.row(0, named=True)
                
                # Initialize form values
                self.form_values = {}
                for field, config in EDITABLE_FIELDS.items():
                    val = self.selected_employee_data.get(field)
                    self.form_values[field] = val if val is not None else config["default"]
        
        # Load change history
        history_df = ClientInputsManager.get_client_inputs(
            global_state.current_company, year, month, matricule
        )
        if not history_df.is_empty():
            self.change_history = history_df.to_dicts()
        else:
            self.change_history = []
    
    def update_base_heures(self, value: str):
        """Update base_heures field."""
        self.form_values["base_heures"] = float(value) if value else 0.0
    
    def update_heures_conges_payes(self, value: str):
        """Update heures_conges_payes field."""
        self.form_values["heures_conges_payes"] = float(value) if value else 0.0
    
    def update_heures_absence(self, value: str):
        """Update heures_absence field."""
        self.form_values["heures_absence"] = float(value) if value else 0.0
    
    def update_type_absence(self, value: str):
        """Update type_absence field."""
        self.form_values["type_absence"] = value
    
    def update_heures_sup_125(self, value: str):
        """Update heures_sup_125 field."""
        self.form_values["heures_sup_125"] = float(value) if value else 0.0
    
    def update_heures_sup_150(self, value: str):
        """Update heures_sup_150 field."""
        self.form_values["heures_sup_150"] = float(value) if value else 0.0
    
    def update_salaire_base(self, value: str):
        """Update salaire_base field."""
        self.form_values["salaire_base"] = float(value) if value else 0.0
    
    def update_prime(self, value: str):
        """Update prime field."""
        self.form_values["prime"] = float(value) if value else 0.0
    
    def update_type_prime(self, value: str):
        """Update type_prime field."""
        self.form_values["type_prime"] = value
    
    def update_prime_exceptionnelle(self, value: str):
        """Update prime_exceptionnelle field."""
        self.form_values["prime_exceptionnelle"] = float(value) if value else 0.0
    
    def update_tickets_restaurant(self, value: str):
        """Update tickets_restaurant field."""
        self.form_values["tickets_restaurant"] = float(value) if value else 0.0
    
    def update_avantage_logement(self, value: str):
        """Update avantage_logement field."""
        self.form_values["avantage_logement"] = float(value) if value else 0.0
    
    def update_avantage_transport(self, value: str):
        """Update avantage_transport field."""
        self.form_values["avantage_transport"] = float(value) if value else 0.0
    
    def update_remarques(self, value: str):
        """Update remarques field."""
        self.form_values["remarques"] = value
    
    async def save_employee_data(self):
        """Save employee data."""
        global_state = await self.get_state(GlobalState)
        
        if not self.selected_employee:
            self.status_message = "error:Sélectionnez un employé"
            return
        
        month, year = map(int, global_state.current_period.split('-'))
        
        try:
            # Track changed fields
            changed_fields = []
            for field, new_val in self.form_values.items():
                old_val = self.selected_employee_data.get(field)
                if str(new_val) != str(old_val):
                    changed_fields.append(field)
                    # Log to client_inputs
                    ClientInputsManager.save_client_input(
                        company_id=global_state.current_company,
                        year=year,
                        month=month,
                        matricule=self.selected_employee,
                        field_name=field,
                        field_value=str(new_val) if new_val is not None else None,
                        entered_by=global_state.user
                    )
            
            # Update employee data
            updated_row = dict(self.selected_employee_data)
            updated_row.update(self.form_values)
            updated_row['company_id'] = global_state.current_company
            updated_row['period_year'] = year
            updated_row['period_month'] = month
            updated_row['statut_validation'] = 'À traiter'
            
            # Create DataFrame and save
            row_df = pl.DataFrame([updated_row])
            DataManager.save_period_data(row_df, global_state.current_company, month, year)
            
            if changed_fields:
                self.status_message = f"success:Données enregistrées. Champs modifiés: {', '.join(changed_fields)}"
            else:
                self.status_message = "info:Aucun changement détecté"
            
            # Reload employees
            await self.load_employees()
            
        except Exception as e:
            self.status_message = f"error:{str(e)}"
    
    def set_tab(self, tab: str):
        """Switch active tab."""
        self.active_tab = tab


def employee_card(emp: dict) -> rx.Component:
    """Render employee summary card."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(
                    f"{emp.get('nom', '')} {emp.get('prenom', '')}",
                    font_weight="600",
                    color=COLORS["neutral-900"],
                ),
                rx.text(
                    f"Mat: {emp.get('matricule', '')}",
                    size="1",
                    color=COLORS["neutral-500"],
                ),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.vstack(
                rx.text(
                    f"{emp.get('base_heures', 169):.0f}h",
                    size="2",
                    color=COLORS["neutral-700"],
                ),
                rx.text(
                    f"{emp.get('salaire_base', 0):.0f}€",
                    size="1",
                    color=COLORS["neutral-500"],
                ),
                spacing="1",
                align="end",
            ),
            width="100%",
            padding="0.75rem",
        ),
        border=f"1px solid {COLORS['neutral-200']}",
        border_radius=RADIUS["md"],
        cursor="pointer",
        _hover={"border_color": COLORS["primary-400"], "bg": COLORS["primary-50"]},
        on_click=lambda: ClientPortalState.select_employee(emp.get('matricule', '')),
    )


# Map field names to handlers
FIELD_HANDLERS = {
    "base_heures": ClientPortalState.update_base_heures,
    "heures_conges_payes": ClientPortalState.update_heures_conges_payes,
    "heures_absence": ClientPortalState.update_heures_absence,
    "type_absence": ClientPortalState.update_type_absence,
    "heures_sup_125": ClientPortalState.update_heures_sup_125,
    "heures_sup_150": ClientPortalState.update_heures_sup_150,
    "salaire_base": ClientPortalState.update_salaire_base,
    "prime": ClientPortalState.update_prime,
    "type_prime": ClientPortalState.update_type_prime,
    "prime_exceptionnelle": ClientPortalState.update_prime_exceptionnelle,
    "tickets_restaurant": ClientPortalState.update_tickets_restaurant,
    "avantage_logement": ClientPortalState.update_avantage_logement,
    "avantage_transport": ClientPortalState.update_avantage_transport,
    "remarques": ClientPortalState.update_remarques,
}


def field_input(field: str, config: dict) -> rx.Component:
    """Render form field based on type."""
    handler = FIELD_HANDLERS.get(field)
    if not handler:
        return rx.box()
    
    if config["type"] == "number":
        return rx.vstack(
            rx.text(config["label"], size="1", color=COLORS["neutral-600"]),
            rx.input(
                type="number",
                default_value=str(config.get("default", 0)),
                on_change=handler,
                width="100%",
            ),
            spacing="1",
            align="start",
            width="100%",
        )
    elif config["type"] == "select":
        return rx.vstack(
            rx.text(config["label"], size="1", color=COLORS["neutral-600"]),
            rx.select(
                config["options"],
                default_value=config.get("default", ""),
                on_change=handler,
                width="100%",
            ),
            spacing="1",
            align="start",
            width="100%",
        )
    elif config["type"] == "text":
        return rx.vstack(
            rx.text(config["label"], size="1", color=COLORS["neutral-600"]),
            rx.text_area(
                default_value="",
                on_change=handler,
                width="100%",
                rows="3",
            ),
            spacing="1",
            align="start",
            width="100%",
        )
    return rx.box()


def form_section(title: str, category: str) -> rx.Component:
    """Render form section for a category."""
    fields = [(f, c) for f, c in EDITABLE_FIELDS.items() if c.get("category") == category]
    
    return rx.box(
        rx.text(title, font_weight="600", size="3", color=COLORS["neutral-800"], margin_bottom="0.5rem"),
        rx.grid(
            *[field_input(f, c) for f, c in fields],
            columns="3",
            spacing="4",
            width="100%",
        ),
        margin_bottom="1.5rem",
    )


def individual_tab() -> rx.Component:
    """Individual employee editing tab."""
    return rx.hstack(
        # Employee list
        rx.box(
            rx.vstack(
                rx.text("Employés", font_weight="600", size="4", color=COLORS["neutral-800"]),
                rx.foreach(
                    ClientPortalState.employees,
                    employee_card,
                ),
                spacing="2",
                width="100%",
            ),
            width="280px",
            padding="1rem",
            border_right=f"1px solid {COLORS['neutral-200']}",
            height="calc(100vh - 200px)",
            overflow_y="auto",
        ),
        
        # Edit form
        rx.box(
            rx.cond(
                ClientPortalState.selected_employee != "",
                rx.vstack(
                    # Employee header
                    rx.hstack(
                        rx.heading(
                            f"{ClientPortalState.selected_employee_data.get('nom', '')} {ClientPortalState.selected_employee_data.get('prenom', '')}",
                            size="5",
                        ),
                        rx.badge(
                            ClientPortalState.selected_employee,
                            color_scheme="blue",
                        ),
                        spacing="3",
                    ),
                    
                    # Status message
                    rx.cond(
                        ClientPortalState.status_message != "",
                        rx.callout(
                            ClientPortalState.status_message.split(":")[-1],
                            icon="info",
                            color_scheme=rx.cond(
                                ClientPortalState.status_message.contains("error"),
                                "red",
                                rx.cond(
                                    ClientPortalState.status_message.contains("success"),
                                    "green",
                                    "blue",
                                ),
                            ),
                        ),
                    ),
                    
                    # Form sections
                    form_section("⏰ Heures", "hours"),
                    form_section("💰 Salaire et Primes", "salary"),
                    form_section("🎁 Avantages", "benefits"),
                    form_section("📋 Autres", "other"),
                    
                    # Save button
                    rx.button(
                        "💾 Enregistrer",
                        on_click=ClientPortalState.save_employee_data,
                        color_scheme="blue",
                        size="3",
                        width="100%",
                    ),
                    
                    spacing="4",
                    padding="1.5rem",
                    width="100%",
                ),
                rx.center(
                    rx.text("Sélectionnez un employé", color=COLORS["neutral-500"]),
                    height="200px",
                ),
            ),
            flex="1",
            overflow_y="auto",
        ),
        
        spacing="0",
        width="100%",
    )


def history_tab() -> rx.Component:
    """Change history tab."""
    return rx.box(
        rx.vstack(
            rx.text("Historique des modifications", font_weight="600", size="4"),
            rx.cond(
                ClientPortalState.change_history.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Matricule"),
                            rx.table.column_header_cell("Champ"),
                            rx.table.column_header_cell("Valeur"),
                            rx.table.column_header_cell("Par"),
                            rx.table.column_header_cell("Date"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            ClientPortalState.change_history,
                            lambda h: rx.table.row(
                                rx.table.cell(h["matricule"]),
                                rx.table.cell(h["field_name"]),
                                rx.table.cell(h["field_value"]),
                                rx.table.cell(h["entered_by"]),
                                rx.table.cell(h["entered_at"]),
                            ),
                        ),
                    ),
                    width="100%",
                ),
                rx.text("Aucune modification enregistrée", color=COLORS["neutral-500"]),
            ),
            spacing="4",
            padding="1.5rem",
        ),
    )


def summary_stats() -> rx.Component:
    """Summary statistics."""
    return rx.hstack(
        rx.box(
            rx.vstack(
                rx.text("👥 Employés", size="1", color=COLORS["neutral-500"]),
                rx.text(ClientPortalState.total_employees, font_weight="700", size="5"),
                spacing="1",
            ),
            padding="1rem",
            border=f"1px solid {COLORS['neutral-200']}",
            border_radius=RADIUS["md"],
        ),
        rx.box(
            rx.vstack(
                rx.text("⏰ Heures absence", size="1", color=COLORS["neutral-500"]),
                rx.text(f"{ClientPortalState.total_absences:.0f}h", font_weight="700", size="5"),
                spacing="1",
            ),
            padding="1rem",
            border=f"1px solid {COLORS['neutral-200']}",
            border_radius=RADIUS["md"],
        ),
        rx.box(
            rx.vstack(
                rx.text("📝 Avec remarques", size="1", color=COLORS["neutral-500"]),
                rx.text(ClientPortalState.with_remarks, font_weight="700", size="5"),
                spacing="1",
            ),
            padding="1rem",
            border=f"1px solid {COLORS['neutral-200']}",
            border_radius=RADIUS["md"],
        ),
        spacing="4",
        margin_bottom="1rem",
    )


def index() -> rx.Component:
    """Client portal page."""
    return rx.box(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    # Header
                    rx.hstack(
                        rx.heading("📝 Portail Client", size="6"),
                        rx.spacer(),
                        summary_stats(),
                        width="100%",
                    ),
                    
                    # Tabs
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("👤 Saisie individuelle", value="individual"),
                            rx.tabs.trigger("📜 Historique", value="history"),
                        ),
                        rx.tabs.content(
                            individual_tab(),
                            value="individual",
                        ),
                        rx.tabs.content(
                            history_tab(),
                            value="history",
                        ),
                        default_value="individual",
                        width="100%",
                    ),
                    
                    spacing="4",
                    padding="2rem",
                    width="100%",
                ),
                flex="1",
                bg=COLORS["neutral-50"],
                min_height="100vh",
            ),
            spacing="0",
        ),
        on_mount=ClientPortalState.load_employees,
    )
