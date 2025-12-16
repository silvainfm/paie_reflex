"""Validation page for reviewing and editing payslips."""
import reflex as rx
from typing import List, Dict
from ..state import GlobalState, CompanyState
from ..components import navbar, sidebar_nav
import sys
from pathlib import Path

# Services import
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.data_mgt import DataManager
from services.payslip_helpers import (
    recalculate_employee_payslip,
    get_salary_rubrics,
    get_all_available_salary_rubrics,
    load_rubrics_from_excel,
    get_available_charges
)
from services.audit import DataAuditLogger
import polars as pl


class ValidationState(GlobalState):
    """State for validation page."""

    employees: List[Dict] = []
    search_query: str = ""
    status_filter: str = "All"
    selected_employee: Dict = {}
    edit_mode: bool = False
    show_edit_modal: bool = False
    modifications: Dict = {}
    modification_reason: str = ""
    is_loading: bool = False
    error_message: str = ""

    # Edit tabs
    active_tab: str = "salary"

    # Available rubrics and charges for dropdowns
    available_rubrics: List[Dict] = []
    available_charges: List[Dict] = []

    def load_employees(self):
        """Load employees for current period from database."""
        self.is_loading = True
        self.error_message = ""

        try:
            company_state = self.get_state(CompanyState)

            if not company_state.current_company or not company_state.current_period:
                self.employees = []
                self.is_loading = False
                return

            # Parse period
            month, year = map(int, company_state.current_period.split('-'))

            # Load data from database
            df = DataManager.load_period_data(company_state.current_company, month, year)

            if not df.is_empty():
                self.employees = df.to_dicts()
            else:
                self.employees = []

        except Exception as e:
            self.error_message = f"Error loading employees: {str(e)}"
            self.employees = []
        finally:
            self.is_loading = False

    def set_search(self, query: str):
        """Set search query."""
        self.search_query = query

    def set_filter(self, filter_val: str):
        """Set status filter."""
        self.status_filter = filter_val

    def select_employee(self, matricule: str):
        """Select employee for editing."""
        for emp in self.employees:
            if emp["matricule"] == matricule:
                self.selected_employee = dict(emp)  # Deep copy
                self.show_edit_modal = True
                self.edit_mode = False
                self.modifications = {}
                self.modification_reason = ""
                self.active_tab = "salary"

                # Load available rubrics and charges
                company_state = self.get_state(CompanyState)
                month, year = map(int, company_state.current_period.split('-'))

                self.available_rubrics = load_rubrics_from_excel()
                # Get charges not currently displayed
                from services.payroll_calculations import ChargesSocialesMonaco
                all_charges = ChargesSocialesMonaco.get_all_charges(year)
                self.available_charges = get_available_charges(emp, all_charges)
                break

    def close_edit_modal(self):
        """Close edit modal."""
        self.show_edit_modal = False
        self.edit_mode = False
        self.modifications = {}
        self.modification_reason = ""
        self.selected_employee = {}

    def toggle_edit(self):
        """Toggle edit mode."""
        self.edit_mode = not self.edit_mode
        if not self.edit_mode:
            self.modifications = {}

    def set_modification(self, field: str, value):
        """Set a modification value."""
        self.modifications[field] = value

    def set_modification_reason(self, reason: str):
        """Set modification reason."""
        self.modification_reason = reason

    def set_active_tab(self, tab: str):
        """Set active edit tab."""
        self.active_tab = tab

    async def recalculate_payslip(self):
        """Recalculate payslip with modifications."""
        if not self.modifications:
            return

        self.is_loading = True
        try:
            company_state = self.get_state(CompanyState)
            month, year = map(int, company_state.current_period.split('-'))

            # Recalculate
            recalculated = recalculate_employee_payslip(
                self.selected_employee,
                self.modifications,
                company_state.current_company,
                year,
                month
            )

            # Update selected employee with recalculated values
            self.selected_employee = recalculated

        except Exception as e:
            self.error_message = f"Error recalculating: {str(e)}"
        finally:
            self.is_loading = False

    async def save_modifications(self):
        """Save modifications to employee."""
        if not self.modification_reason:
            self.error_message = "Modification reason required"
            return

        if not self.modifications:
            self.error_message = "No modifications to save"
            return

        self.is_loading = True
        try:
            company_state = self.get_state(CompanyState)
            month, year = map(int, company_state.current_period.split('-'))

            # Recalculate first
            recalculated = recalculate_employee_payslip(
                self.selected_employee,
                self.modifications,
                company_state.current_company,
                year,
                month
            )

            # Save to database
            matricule = self.selected_employee.get("matricule")
            DataManager.update_employee_data(
                company_state.current_company,
                year,
                month,
                matricule,
                recalculated
            )

            # Log modification
            from services.auth import AuthManager
            # Get current user from AuthState
            auth_state = self.get_state(GlobalState)
            user = getattr(auth_state, 'user', 'system')

            DataAuditLogger.log_modification(
                company_state.current_company,
                year,
                month,
                matricule,
                user,
                self.modifications,
                self.modification_reason
            )

            # Update employee in list
            for i, emp in enumerate(self.employees):
                if emp["matricule"] == matricule:
                    self.employees[i] = recalculated
                    break

            # Close modal and reset
            self.show_edit_modal = False
            self.edit_mode = False
            self.modifications = {}
            self.modification_reason = ""
            self.error_message = ""

            # Reload employees
            self.load_employees()

        except Exception as e:
            self.error_message = f"Error saving: {str(e)}"
        finally:
            self.is_loading = False

    def validate_employee(self, matricule: str):
        """Validate an employee's payslip."""
        self.is_loading = True
        try:
            company_state = self.get_state(CompanyState)
            month, year = map(int, company_state.current_period.split('-'))

            # Update validation status
            for emp in self.employees:
                if emp["matricule"] == matricule:
                    emp["statut_validation"] = True
                    emp["edge_case_flag"] = False

                    # Save to database
                    DataManager.update_employee_data(
                        company_state.current_company,
                        year,
                        month,
                        matricule,
                        emp
                    )
                    break
        except Exception as e:
            self.error_message = f"Error validating: {str(e)}"
        finally:
            self.is_loading = False

    @rx.var
    def filtered_employees(self) -> List[Dict]:
        """Get filtered employee list."""
        filtered = self.employees

        # Apply search
        if self.search_query:
            query = self.search_query.lower()
            filtered = [
                e for e in filtered
                if query in e.get("matricule", "").lower()
                or query in e.get("nom", "").lower()
                or query in e.get("prenom", "").lower()
            ]

        # Apply status filter
        if self.status_filter == "To Verify":
            filtered = [e for e in filtered if e.get("edge_case_flag")]
        elif self.status_filter == "Validated":
            filtered = [e for e in filtered if e.get("statut_validation")]

        return filtered

    @rx.var
    def edge_case_count(self) -> int:
        """Count edge cases."""
        return sum(1 for e in self.employees if e.get("edge_case_flag"))


def salary_elements_tab() -> rx.Component:
    """Salary elements editing tab."""
    return rx.vstack(
        # Hours section
        rx.heading("Hours", size="4", margin_bottom="0.5rem"),
        rx.grid(
            rx.vstack(
                rx.text("Base Hours", size="2"),
                rx.cond(
                    ValidationState.edit_mode,
                    rx.input(
                        value=ValidationState.selected_employee.get("base_heures", 0),
                        on_change=lambda v: ValidationState.set_modification("base_heures", float(v)),
                        type="number",
                        step=0.5,
                    ),
                    rx.text(f"{ValidationState.selected_employee.get('base_heures', 0):.2f}"),
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Hours Paid", size="2"),
                rx.cond(
                    ValidationState.edit_mode,
                    rx.input(
                        value=ValidationState.selected_employee.get("heures_payees", 0),
                        on_change=lambda v: ValidationState.set_modification("heures_payees", float(v)),
                        type="number",
                        step=0.5,
                    ),
                    rx.text(f"{ValidationState.selected_employee.get('heures_payees', 0):.2f}"),
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Absence Hours", size="2"),
                rx.cond(
                    ValidationState.edit_mode,
                    rx.input(
                        value=ValidationState.selected_employee.get("heures_absence", 0),
                        on_change=lambda v: ValidationState.set_modification("heures_absence", float(v)),
                        type="number",
                        step=0.5,
                    ),
                    rx.text(f"{ValidationState.selected_employee.get('heures_absence', 0):.2f}"),
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("PTO Hours", size="2"),
                rx.cond(
                    ValidationState.edit_mode,
                    rx.input(
                        value=ValidationState.selected_employee.get("heures_conges_payes", 0),
                        on_change=lambda v: ValidationState.set_modification("heures_conges_payes", float(v)),
                        type="number",
                        step=0.5,
                    ),
                    rx.text(f"{ValidationState.selected_employee.get('heures_conges_payes', 0):.2f}"),
                ),
                spacing="1",
            ),
            columns="4",
            spacing="3",
        ),

        rx.divider(),

        # Overtime section
        rx.heading("Overtime", size="4", margin_bottom="0.5rem"),
        rx.grid(
            rx.vstack(
                rx.text("OT 125%", size="2"),
                rx.cond(
                    ValidationState.edit_mode,
                    rx.input(
                        value=ValidationState.selected_employee.get("heures_sup_125", 0),
                        on_change=lambda v: ValidationState.set_modification("heures_sup_125", float(v)),
                        type="number",
                        step=0.5,
                    ),
                    rx.text(f"{ValidationState.selected_employee.get('heures_sup_125', 0):.2f}"),
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("OT 150%", size="2"),
                rx.cond(
                    ValidationState.edit_mode,
                    rx.input(
                        value=ValidationState.selected_employee.get("heures_sup_150", 0),
                        on_change=lambda v: ValidationState.set_modification("heures_sup_150", float(v)),
                        type="number",
                        step=0.5,
                    ),
                    rx.text(f"{ValidationState.selected_employee.get('heures_sup_150', 0):.2f}"),
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Holiday Hours", size="2"),
                rx.cond(
                    ValidationState.edit_mode,
                    rx.input(
                        value=ValidationState.selected_employee.get("heures_jours_feries", 0),
                        on_change=lambda v: ValidationState.set_modification("heures_jours_feries", float(v)),
                        type="number",
                        step=0.5,
                    ),
                    rx.text(f"{ValidationState.selected_employee.get('heures_jours_feries', 0):.2f}"),
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Sunday Hours", size="2"),
                rx.cond(
                    ValidationState.edit_mode,
                    rx.input(
                        value=ValidationState.selected_employee.get("heures_dimanche", 0),
                        on_change=lambda v: ValidationState.set_modification("heures_dimanche", float(v)),
                        type="number",
                        step=0.5,
                    ),
                    rx.text(f"{ValidationState.selected_employee.get('heures_dimanche', 0):.2f}"),
                ),
                spacing="1",
            ),
            columns="4",
            spacing="3",
        ),

        rx.divider(),

        # Salary & Primes section
        rx.heading("Salary & Bonuses", size="4", margin_bottom="0.5rem"),
        rx.grid(
            rx.vstack(
                rx.text("Base Salary", size="2"),
                rx.cond(
                    ValidationState.edit_mode,
                    rx.input(
                        value=ValidationState.selected_employee.get("salaire_base", 0),
                        on_change=lambda v: ValidationState.set_modification("salaire_base", float(v)),
                        type="number",
                        step=10,
                    ),
                    rx.text(f"{ValidationState.selected_employee.get('salaire_base', 0):,.2f} €"),
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Hourly Rate", size="2"),
                rx.cond(
                    ValidationState.edit_mode,
                    rx.input(
                        value=ValidationState.selected_employee.get("taux_horaire", 0),
                        on_change=lambda v: ValidationState.set_modification("taux_horaire", float(v)),
                        type="number",
                        step=0.1,
                    ),
                    rx.text(f"{ValidationState.selected_employee.get('taux_horaire', 0):.2f} €"),
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Performance Bonus", size="2"),
                rx.cond(
                    ValidationState.edit_mode,
                    rx.input(
                        value=ValidationState.selected_employee.get("prime", 0),
                        on_change=lambda v: ValidationState.set_modification("prime", float(v)),
                        type="number",
                        step=10,
                    ),
                    rx.text(f"{ValidationState.selected_employee.get('prime', 0):,.2f} €"),
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Meal Vouchers", size="2"),
                rx.cond(
                    ValidationState.edit_mode,
                    rx.input(
                        value=ValidationState.selected_employee.get("tickets_restaurant", 0),
                        on_change=lambda v: ValidationState.set_modification("tickets_restaurant", int(v)),
                        type="number",
                    ),
                    rx.text(f"{ValidationState.selected_employee.get('tickets_restaurant', 0)}"),
                ),
                spacing="1",
            ),
            columns="4",
            spacing="3",
        ),

        spacing="4",
        width="100%",
    )


def charges_tab() -> rx.Component:
    """Social charges editing tab."""
    emp = ValidationState.selected_employee
    details = emp.get("details_charges", {})
    charges_sal = details.get("charges_salariales", {})
    charges_pat = details.get("charges_patronales", {})

    return rx.vstack(
        rx.text("Social charges editing - showing current charges", size="3", margin_bottom="1rem"),
        rx.text("Employee Charges", weight="bold", size="4"),
        rx.box(
            rx.foreach(
                charges_sal.items(),
                lambda item: rx.hstack(
                    rx.text(item[0], width="300px"),
                    rx.text(f"{item[1]:,.2f} €", weight="bold"),
                    spacing="3",
                ),
            ),
            padding="1rem",
            bg="#f8f9fa",
            border_radius="4px",
        ),

        rx.divider(),

        rx.text("Employer Charges", weight="bold", size="4"),
        rx.box(
            rx.foreach(
                charges_pat.items(),
                lambda item: rx.hstack(
                    rx.text(item[0], width="300px"),
                    rx.text(f"{item[1]:,.2f} €", weight="bold"),
                    spacing="3",
                ),
            ),
            padding="1rem",
            bg="#f8f9fa",
            border_radius="4px",
        ),

        spacing="4",
        width="100%",
    )


def edit_modal() -> rx.Component:
    """Comprehensive employee edit modal."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.heading(
                        f"{ValidationState.selected_employee.get('nom', '')} {ValidationState.selected_employee.get('prenom', '')} - {ValidationState.selected_employee.get('matricule', '')}",
                        size="6",
                    ),
                    rx.dialog.close(
                        rx.button("×", variant="ghost", on_click=ValidationState.close_edit_modal),
                    ),
                    justify="between",
                    width="100%",
                ),

                # Error message
                rx.cond(
                    ValidationState.error_message != "",
                    rx.callout(
                        ValidationState.error_message,
                        icon="alert-circle",
                        color_scheme="red",
                    ),
                    rx.fragment(),
                ),

                # Summary stats
                rx.grid(
                    rx.vstack(
                        rx.text("Gross", size="2", color="#6c757d"),
                        rx.text(f"{ValidationState.selected_employee.get('salaire_brut', 0):,.2f} €", size="4", weight="bold"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Net", size="2", color="#6c757d"),
                        rx.text(f"{ValidationState.selected_employee.get('salaire_net', 0):,.2f} €", size="4", weight="bold"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Total Cost", size="2", color="#6c757d"),
                        rx.text(f"{ValidationState.selected_employee.get('cout_total_employeur', 0):,.2f} €", size="4", weight="bold"),
                        spacing="1",
                    ),
                    columns="3",
                    spacing="4",
                    margin_bottom="1rem",
                ),

                # Tabs
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Salary Elements", value="salary"),
                        rx.tabs.trigger("Social Charges", value="charges"),
                    ),
                    rx.tabs.content(
                        salary_elements_tab(),
                        value="salary",
                    ),
                    rx.tabs.content(
                        charges_tab(),
                        value="charges",
                    ),
                    default_value="salary",
                    value=ValidationState.active_tab,
                    on_change=ValidationState.set_active_tab,
                ),

                rx.divider(),

                # Modification reason
                rx.vstack(
                    rx.text("Modification Reason (required)", weight="bold"),
                    rx.text_area(
                        placeholder="Explain why these changes are being made...",
                        value=ValidationState.modification_reason,
                        on_change=ValidationState.set_modification_reason,
                        width="100%",
                    ),
                    spacing="2",
                    width="100%",
                ),

                # Action buttons
                rx.hstack(
                    rx.cond(
                        ValidationState.edit_mode,
                        rx.button(
                            "Cancel Edit",
                            on_click=ValidationState.toggle_edit,
                            variant="soft",
                        ),
                        rx.button(
                            "Edit",
                            on_click=ValidationState.toggle_edit,
                            variant="soft",
                        ),
                    ),
                    rx.cond(
                        ValidationState.edit_mode,
                        rx.button(
                            rx.cond(
                                ValidationState.is_loading,
                                rx.spinner(size="3"),
                                rx.text("Recalculate"),
                            ),
                            on_click=ValidationState.recalculate_payslip,
                            disabled=ValidationState.is_loading,
                            variant="outline",
                        ),
                        rx.fragment(),
                    ),
                    rx.button(
                        rx.cond(
                            ValidationState.is_loading,
                            rx.spinner(size="3"),
                            rx.text("Save"),
                        ),
                        on_click=ValidationState.save_modifications,
                        disabled=ValidationState.is_loading,
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),

                spacing="4",
                width="100%",
            ),
            max_width="900px",
            max_height="80vh",
            overflow_y="auto",
        ),
        open=ValidationState.show_edit_modal,
    )


def employee_card(emp: Dict) -> rx.Component:
    """Render employee card."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading(
                    f"{emp['nom']} {emp['prenom']} - {emp['matricule']}",
                    size="5",
                ),
                rx.cond(
                    emp.get("edge_case_flag"),
                    rx.badge("⚠️ To Verify", color_scheme="orange"),
                    rx.cond(
                        emp.get("statut_validation"),
                        rx.badge("✓ Validated", color_scheme="green"),
                        rx.badge("⏳ Pending", color_scheme="gray"),
                    ),
                ),
                justify="between",
                width="100%",
            ),

            rx.cond(
                emp.get("edge_case_flag"),
                rx.callout(
                    emp.get("edge_case_reason", ""),
                    icon="alert-circle",
                    color_scheme="yellow",
                ),
                rx.fragment(),
            ),

            rx.grid(
                rx.vstack(
                    rx.text("Gross Salary", size="2", color="#6c757d"),
                    rx.text(f"{emp.get('salaire_brut', 0):,.2f} €", size="4", weight="bold"),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Employee Charges", size="2", color="#6c757d"),
                    rx.text(f"{emp.get('total_charges_salariales', 0):,.2f} €", size="4", weight="bold"),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Net Salary", size="2", color="#6c757d"),
                    rx.text(f"{emp.get('salaire_net', 0):,.2f} €", size="4", weight="bold"),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Total Cost", size="2", color="#6c757d"),
                    rx.text(f"{emp.get('cout_total_employeur', 0):,.2f} €", size="4", weight="bold"),
                    spacing="1",
                ),
                columns="4",
                spacing="4",
            ),

            rx.hstack(
                rx.button(
                    "Edit",
                    on_click=ValidationState.select_employee(emp["matricule"]),
                    variant="soft",
                ),
                rx.cond(
                    ~emp.get("statut_validation"),
                    rx.button(
                        "Validate",
                        on_click=ValidationState.validate_employee(emp["matricule"]),
                        variant="solid",
                    ),
                    rx.fragment(),
                ),
                spacing="3",
            ),

            spacing="4",
            width="100%",
        ),
        bg="white",
        padding="1.5rem",
        border_radius="8px",
        box_shadow="0 2px 8px rgba(0,0,0,0.1)",
    )


def index() -> rx.Component:
    """Validation page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    rx.heading("Validation", size="8", margin_bottom="1rem"),

                    rx.cond(
                        ~GlobalState.has_selection,
                        rx.callout(
                            "Select company and period first",
                            icon="alert-circle",
                            color_scheme="red",
                        ),
                        rx.fragment(),
                    ),

                    # Error message
                    rx.cond(
                        ValidationState.error_message != "",
                        rx.callout(
                            ValidationState.error_message,
                            icon="alert-circle",
                            color_scheme="red",
                        ),
                        rx.fragment(),
                    ),

                    # Filters
                    rx.hstack(
                        rx.input(
                            placeholder="Search (ID, name)",
                            value=ValidationState.search_query,
                            on_change=ValidationState.set_search,
                        ),
                        rx.select(
                            ["All", "To Verify", "Validated"],
                            value=ValidationState.status_filter,
                            on_change=ValidationState.set_filter,
                        ),
                        rx.box(
                            rx.hstack(
                                rx.text("Edge Cases:", size="3"),
                                rx.badge(ValidationState.edge_case_count, color_scheme="red"),
                                spacing="2",
                            ),
                        ),
                        spacing="4",
                        width="100%",
                    ),

                    rx.divider(),

                    # Loading indicator
                    rx.cond(
                        ValidationState.is_loading,
                        rx.center(
                            rx.spinner(size="3"),
                            padding="2rem",
                        ),
                        # Employee list
                        rx.foreach(
                            ValidationState.filtered_employees,
                            employee_card,
                        ),
                    ),

                    spacing="5",
                    padding="2rem",
                    width="100%",
                ),
                flex="1",
                overflow_y="auto",
            ),
            spacing="0",
            width="100%",
            align_items="start",
        ),
        # Edit modal
        edit_modal(),
        on_mount=ValidationState.load_employees,
    )
