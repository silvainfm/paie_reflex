"""Validation page for reviewing and editing payslips - Premium design."""
import reflex as rx
from typing import List, Dict
from ..state import GlobalState
from ..components import navbar, sidebar_nav
from ..services.data_mgt import DataManager
from ..services.payslip_helpers import (
    recalculate_employee_payslip,
    get_salary_rubrics,
    get_all_available_salary_rubrics,
    load_rubrics_from_excel,
    get_available_charges_for_employee
)
from ..services.data_mgt import DataAuditLogger
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
import polars as pl


class ValidationState(GlobalState):
    """State for validation page."""

    employees: List[Dict] = []
    search_query: str = ""
    status_filter: str = "Tous"
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

    # Rubric management
    selected_rubric_to_add: str = ""
    added_rubrics: List[Dict] = []  # Rubrics added in this session
    removed_rubrics: List[str] = []  # Field names of removed rubrics

    def load_employees(self):
        """Load employees for current period from database."""
        self.is_loading = True
        self.error_message = ""

        try:
            if not self.current_company or not self.current_period:
                self.employees = []
                self.is_loading = False
                return

            # Parse period
            month, year = map(int, self.current_period.split('-'))

            # Load data from database
            df = DataManager.load_period_data(self.current_company, month, year)

            if not df.is_empty():
                self.employees = df.to_dicts()
            else:
                self.employees = []

        except Exception as e:
            self.error_message = f"Erreur lors du chargement des employés: {str(e)}"
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
                self.added_rubrics = []
                self.removed_rubrics = []
                self.selected_rubric_to_add = ""

                # Load available rubrics and charges
                month, year = map(int, self.current_period.split('-'))

                self.available_rubrics = load_rubrics_from_excel()
                # Get charges not currently displayed
                from ..services.payroll_calculations import ChargesSocialesMonaco
                all_charges = ChargesSocialesMonaco.get_all_charges(year)
                self.available_charges = get_available_charges_for_employee(emp, year, month)
                break

    def close_edit_modal(self):
        """Close edit modal."""
        self.show_edit_modal = False
        self.edit_mode = False
        self.modifications = {}
        self.modification_reason = ""
        self.selected_employee = {}
        self.added_rubrics = []
        self.removed_rubrics = []
        self.selected_rubric_to_add = ""

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

    def set_selected_rubric(self, rubric_label: str):
        """Set selected rubric to add."""
        self.selected_rubric_to_add = rubric_label

    def add_rubric(self):
        """Add selected rubric to employee."""
        if not self.selected_rubric_to_add:
            return

        # Find the rubric details
        for rubric in self.available_rubrics:
            rubric_display = f"{rubric['label']} ({rubric['field_name']})"
            if rubric_display == self.selected_rubric_to_add:
                # Add to added rubrics list with initial value 0
                self.added_rubrics.append({
                    'field_name': rubric['field_name'],
                    'label': rubric['label'],
                    'value': 0.0
                })

                # Add to modifications
                self.modifications[rubric['field_name']] = 0.0

                # Reset selection
                self.selected_rubric_to_add = ""
                break

    def remove_rubric(self, field_name: str):
        """Remove a rubric from employee."""
        # Add to removed rubrics list
        if field_name not in self.removed_rubrics:
            self.removed_rubrics.append(field_name)

        # Set to 0 in modifications
        self.modifications[field_name] = 0.0

    def update_added_rubric_value(self, field_name: str, value: float):
        """Update value of an added rubric."""
        # Update in added_rubrics list
        for rubric in self.added_rubrics:
            if rubric['field_name'] == field_name:
                rubric['value'] = value
                break

        # Update in modifications
        self.modifications[field_name] = value

    @rx.var
    def available_rubrics_for_dropdown(self) -> List[str]:
        """Get rubric labels for dropdown, excluding already added ones."""
        added_fields = [r['field_name'] for r in self.added_rubrics]
        return [
            f"{r['label']} ({r['field_name']})"
            for r in self.available_rubrics
            if r['field_name'] not in added_fields
        ]

    async def recalculate_payslip(self):
        """Recalculate payslip with modifications."""
        if not self.modifications:
            return

        self.is_loading = True
        try:
            month, year = map(int, self.current_period.split('-'))

            # Recalculate
            recalculated = recalculate_employee_payslip(
                self.selected_employee,
                self.modifications,
                self.current_company,
                year,
                month
            )

            # Update selected employee with recalculated values
            self.selected_employee = recalculated

        except Exception as e:
            self.error_message = f"Erreur lors du recalcul: {str(e)}"
        finally:
            self.is_loading = False

    async def save_modifications(self):
        """Save modifications to employee."""
        if not self.modification_reason:
            self.error_message = "Raison de modification requise"
            return

        if not self.modifications and not self.added_rubrics and not self.removed_rubrics:
            self.error_message = "Aucune modification à enregistrer"
            return

        self.is_loading = True
        try:
            month, year = map(int, self.current_period.split('-'))

            # Prepare audit info for rubric changes
            audit_info = dict(self.modifications)
            if self.added_rubrics:
                audit_info['added_rubrics'] = [r['field_name'] for r in self.added_rubrics]
            if self.removed_rubrics:
                audit_info['removed_rubrics'] = self.removed_rubrics

            # Recalculate first
            recalculated = recalculate_employee_payslip(
                self.selected_employee,
                self.modifications,
                self.current_company,
                year,
                month
            )

            # Save to database
            matricule = self.selected_employee.get("matricule")
            DataManager.update_employee_data(
                self.current_company,
                year,
                month,
                matricule,
                recalculated
            )

            # Log modification
            from ..services.auth import AuthManager
            user = getattr(self, 'user', 'system')

            DataAuditLogger.log_modification(
                self.current_company,
                year,
                month,
                matricule,
                user,
                audit_info,
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
            self.added_rubrics = []
            self.removed_rubrics = []

            # Reload employees
            self.load_employees()

        except Exception as e:
            self.error_message = f"Erreur lors de l'enregistrement: {str(e)}"
        finally:
            self.is_loading = False

    def validate_employee(self, matricule: str):
        """Validate an employee's payslip."""
        self.is_loading = True
        try:
            month, year = map(int, self.current_period.split('-'))

            # Update validation status
            for emp in self.employees:
                if emp["matricule"] == matricule:
                    emp["statut_validation"] = True
                    emp["edge_case_flag"] = False

                    # Save to database
                    DataManager.update_employee_data(
                        self.current_company,
                        year,
                        month,
                        matricule,
                        emp
                    )
                    break
        except Exception as e:
            self.error_message = f"Erreur lors de la validation: {str(e)}"
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
        if self.status_filter == "À vérifier":
            filtered = [e for e in filtered if e.get("edge_case_flag")]
        elif self.status_filter == "Validés":
            filtered = [e for e in filtered if e.get("statut_validation")]

        return filtered

    @rx.var
    def edge_case_count(self) -> int:
        """Count edge cases."""
        return sum(1 for e in self.employees if e.get("edge_case_flag"))


def added_rubric_item(rubric: Dict) -> rx.Component:
    """Premium added rubric item."""
    return rx.hstack(
        rx.text(
            rubric['label'],
            size=BODY_SM["size"],
            weight="medium",
            color=COLORS["neutral-700"],
            width="200px",
        ),
        rx.cond(
            ValidationState.edit_mode,
            rx.input(
                value=rubric['value'],
                on_change=lambda v: ValidationState.update_added_rubric_value(rubric['field_name'], v),
                type="number",
                step=10,
                size="2",
                style={
                    "width": "150px",
                    "bg": COLORS["white"],
                    "border": f"1px solid {COLORS['neutral-300']}",
                    "border_radius": RADIUS["lg"],
                    "_focus": {
                        "border_color": COLORS["primary-500"],
                        "box_shadow": SHADOWS["focus_ring"],
                    },
                },
            ),
            rx.text(
                f"{rubric['value']:,.2f} €",
                size=BODY_SM["size"],
                color=COLORS["neutral-900"],
                font_variant_numeric="tabular-nums",
            ),
        ),
        rx.cond(
            ValidationState.edit_mode,
            rx.button(
                rx.icon("x", size=16),
                on_click=ValidationState.remove_rubric(rubric['field_name']),
                size="1",
                style={
                    "bg": COLORS["error-100"],
                    "color": COLORS["error-600"],
                    "border": f"1px solid {COLORS['error-300']}",
                    "border_radius": RADIUS["md"],
                    "_hover": {"bg": COLORS["error-200"]},
                },
            ),
            rx.fragment(),
        ),
        spacing="3",
        align="center",
        width="100%",
        padding="0.5rem",
        border_radius=RADIUS["md"],
        bg=COLORS["neutral-50"],
    )


def form_field(label: str, field_name: str, value, step: float = 0.5, unit: str = "") -> rx.Component:
    """Premium form field for editing."""
    return rx.vstack(
        rx.text(
            label,
            size=LABEL["size"],
            weight=LABEL["weight"],
            color=COLORS["neutral-500"],
            text_transform=LABEL["text_transform"],
            letter_spacing=LABEL["letter_spacing"],
        ),
        rx.cond(
            ValidationState.edit_mode,
            rx.input(
                value=value,
                on_change=lambda v: ValidationState.set_modification(field_name, v),
                type="number",
                step=step,
                size="2",
                style={
                    "bg": COLORS["white"],
                    "border": f"1px solid {COLORS['neutral-300']}",
                    "border_radius": RADIUS["lg"],
                    "padding": "0.625rem 0.875rem",
                    "_focus": {
                        "border_color": COLORS["primary-500"],
                        "box_shadow": SHADOWS["focus_ring"],
                    },
                },
            ),
            rx.text(
                f"{value:.2f}{unit}" if isinstance(value, (int, float)) else str(value),
                size=BODY_MD["size"],
                weight="medium",
                color=COLORS["neutral-900"],
                font_variant_numeric="tabular-nums",
            ),
        ),
        spacing="2",
        align="start",
    )


def salary_elements_tab() -> rx.Component:
    """Premium salary elements editing tab."""
    return rx.vstack(
        # Hours section
        rx.vstack(
            rx.heading(
                "Heures",
                size=HEADING_SM["size"],
                weight=HEADING_SM["weight"],
                color=COLORS["primary-900"],
            ),
            rx.grid(
                form_field("Heures de base", "base_heures", ValidationState.selected_employee.get("base_heures", 0), 0.5),
                form_field("Heures payées", "heures_payees", ValidationState.selected_employee.get("heures_payees", 0), 0.5),
                form_field("Heures d'absence", "heures_absence", ValidationState.selected_employee.get("heures_absence", 0), 0.5),
                form_field("Heures CP", "heures_conges_payes", ValidationState.selected_employee.get("heures_conges_payes", 0), 0.5),
                columns="4",
                spacing=COMPONENT_SPACING["grid_gap"],
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),

        rx.box(height="1px", bg=COLORS["neutral-200"], width="100%"),

        # Overtime section
        rx.vstack(
            rx.heading(
                "Heures supplémentaires",
                size=HEADING_SM["size"],
                weight=HEADING_SM["weight"],
                color=COLORS["primary-900"],
            ),
            rx.grid(
                form_field("HS 125%", "heures_sup_125", ValidationState.selected_employee.get("heures_sup_125", 0), 0.5),
                form_field("HS 150%", "heures_sup_150", ValidationState.selected_employee.get("heures_sup_150", 0), 0.5),
                form_field("Heures fériées", "heures_jours_feries", ValidationState.selected_employee.get("heures_jours_feries", 0), 0.5),
                form_field("Heures dimanche", "heures_dimanche", ValidationState.selected_employee.get("heures_dimanche", 0), 0.5),
                columns="4",
                spacing=COMPONENT_SPACING["grid_gap"],
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),

        rx.box(height="1px", bg=COLORS["neutral-200"], width="100%"),

        # Salary & Primes section
        rx.vstack(
            rx.heading(
                "Salaire & Primes",
                size=HEADING_SM["size"],
                weight=HEADING_SM["weight"],
                color=COLORS["primary-900"],
            ),
            rx.grid(
                form_field("Salaire de base", "salaire_base", ValidationState.selected_employee.get("salaire_base", 0), 10, " €"),
                form_field("Taux horaire", "taux_horaire", ValidationState.selected_employee.get("taux_horaire", 0), 0.1, " €"),
                form_field("Prime", "prime", ValidationState.selected_employee.get("prime", 0), 10, " €"),
                form_field("Tickets restaurant", "tickets_restaurant", ValidationState.selected_employee.get("tickets_restaurant", 0), 1),
                columns="4",
                spacing=COMPONENT_SPACING["grid_gap"],
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),

        rx.box(height="1px", bg=COLORS["neutral-200"], width="100%"),

        # Additional Rubrics section
        rx.vstack(
            rx.heading(
                "Rubriques additionnelles",
                size=HEADING_SM["size"],
                weight=HEADING_SM["weight"],
                color=COLORS["primary-900"],
            ),

            # Show currently added rubrics
            rx.cond(
                ValidationState.added_rubrics.length() > 0,
                rx.vstack(
                    rx.foreach(
                        ValidationState.added_rubrics,
                        added_rubric_item,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.text(
                    "Aucune rubrique additionnelle ajoutée",
                    size=BODY_SM["size"],
                    color=COLORS["neutral-500"],
                ),
            ),

            # Add new rubric controls
            rx.cond(
                ValidationState.edit_mode,
                rx.hstack(
                    rx.select(
                        ValidationState.available_rubrics_for_dropdown,
                        placeholder="Sélectionner une rubrique",
                        value=ValidationState.selected_rubric_to_add,
                        on_change=ValidationState.set_selected_rubric,
                        size="2",
                        style={
                            "width": "300px",
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
                    rx.button(
                        rx.hstack(
                            rx.icon("plus", size=16),
                            rx.text("Ajouter"),
                            spacing="2",
                        ),
                        on_click=ValidationState.add_rubric,
                        disabled=ValidationState.selected_rubric_to_add == "",
                        size="2",
                        style={
                            "bg": COLORS["primary-600"],
                            "color": COLORS["white"],
                            "border_radius": RADIUS["lg"],
                            "padding": "0.625rem 1rem",
                            "_hover": {"bg": COLORS["primary-700"]},
                            "_disabled": {
                                "bg": COLORS["neutral-300"],
                                "cursor": "not-allowed",
                            },
                        },
                    ),
                    spacing="3",
                ),
                rx.fragment(),
            ),

            spacing="3",
            width="100%",
        ),

        spacing="6",
        width="100%",
    )


def charges_tab() -> rx.Component:
    """Premium social charges tab."""
    return rx.vstack(
        rx.box(
            rx.hstack(
                rx.icon("info", size=20, color=COLORS["info-600"]),
                rx.text(
                    "L'édition des charges sociales arrive bientôt. Les charges sont calculées automatiquement lors du traitement.",
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
        spacing="4",
        width="100%",
    )


def edit_modal() -> rx.Component:
    """Premium employee edit modal."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.vstack(
                        rx.heading(
                            f"{ValidationState.selected_employee.get('nom', '')} {ValidationState.selected_employee.get('prenom', '')}",
                            size=HEADING_MD["size"],
                            weight=HEADING_MD["weight"],
                            color=COLORS["primary-900"],
                        ),
                        rx.text(
                            f"Matricule: {ValidationState.selected_employee.get('matricule', '')}",
                            size=BODY_SM["size"],
                            color=COLORS["neutral-600"],
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.dialog.close(
                        rx.button(
                            rx.icon("x", size=20),
                            on_click=ValidationState.close_edit_modal,
                            variant="ghost",
                            size="2",
                            style={
                                "color": COLORS["neutral-600"],
                                "_hover": {"bg": COLORS["neutral-100"]},
                            },
                        ),
                    ),
                    justify="between",
                    width="100%",
                    align="start",
                ),

                # Error message
                rx.cond(
                    ValidationState.error_message != "",
                    rx.box(
                        rx.hstack(
                            rx.icon("circle-alert", size=20, color=COLORS["error-600"]),
                            rx.text(
                                ValidationState.error_message,
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
                    rx.fragment(),
                ),

                # Summary stats
                rx.grid(
                    rx.box(
                        rx.vstack(
                            rx.icon("euro", size=24, color=COLORS["primary-600"], stroke_width=2),
                            rx.text(
                                "Brut",
                                size=LABEL["size"],
                                weight=LABEL["weight"],
                                color=COLORS["neutral-500"],
                                text_transform=LABEL["text_transform"],
                                letter_spacing=LABEL["letter_spacing"],
                            ),
                            rx.text(
                                f"{ValidationState.selected_employee.get('salaire_brut', 0):,.2f} €",
                                size=HEADING_SM["size"],
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
                    rx.box(
                        rx.vstack(
                            rx.icon("wallet", size=24, color=COLORS["success-600"], stroke_width=2),
                            rx.text(
                                "Net",
                                size=LABEL["size"],
                                weight=LABEL["weight"],
                                color=COLORS["neutral-500"],
                                text_transform=LABEL["text_transform"],
                                letter_spacing=LABEL["letter_spacing"],
                            ),
                            rx.text(
                                f"{ValidationState.selected_employee.get('salaire_net', 0):,.2f} €",
                                size=HEADING_SM["size"],
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
                    rx.box(
                        rx.vstack(
                            rx.icon("receipt", size=24, color=COLORS["info-600"], stroke_width=2),
                            rx.text(
                                "Coût total",
                                size=LABEL["size"],
                                weight=LABEL["weight"],
                                color=COLORS["neutral-500"],
                                text_transform=LABEL["text_transform"],
                                letter_spacing=LABEL["letter_spacing"],
                            ),
                            rx.text(
                                f"{ValidationState.selected_employee.get('cout_total_employeur', 0):,.2f} €",
                                size=HEADING_SM["size"],
                                weight="bold",
                                color=COLORS["info-600"],
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

                # Tabs
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger(
                            "Éléments de salaire",
                            value="salary",
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
                            "Charges sociales",
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
                        style={
                            "border_bottom": f"1px solid {COLORS['neutral-200']}",
                        },
                    ),
                    rx.tabs.content(
                        salary_elements_tab(),
                        value="salary",
                        style={"padding_top": "1.5rem"},
                    ),
                    rx.tabs.content(
                        charges_tab(),
                        value="charges",
                        style={"padding_top": "1.5rem"},
                    ),
                    default_value="salary",
                    value=ValidationState.active_tab,
                    on_change=ValidationState.set_active_tab,
                ),

                rx.box(height="1px", bg=COLORS["neutral-200"], width="100%"),

                # Modification reason
                rx.vstack(
                    rx.text(
                        "Raison de modification (requise)",
                        size=BODY_SM["size"],
                        weight="medium",
                        color=COLORS["neutral-700"],
                    ),
                    rx.text_area(
                        placeholder="Expliquez pourquoi ces modifications sont apportées...",
                        value=ValidationState.modification_reason,
                        on_change=ValidationState.set_modification_reason,
                        size="2",
                        style={
                            "width": "100%",
                            "min_height": "100px",
                            "bg": COLORS["white"],
                            "border": f"1px solid {COLORS['neutral-300']}",
                            "border_radius": RADIUS["lg"],
                            "padding": "0.75rem",
                            "_focus": {
                                "border_color": COLORS["primary-500"],
                                "box_shadow": SHADOWS["focus_ring"],
                            },
                        },
                    ),
                    spacing="2",
                    width="100%",
                ),

                # Action buttons
                rx.hstack(
                    rx.cond(
                        ValidationState.edit_mode,
                        rx.button(
                            "Annuler les modifications",
                            on_click=ValidationState.toggle_edit,
                            size="2",
                            style={
                                "bg": COLORS["white"],
                                "color": COLORS["neutral-700"],
                                "border": f"1px solid {COLORS['neutral-300']}",
                                "border_radius": RADIUS["lg"],
                                "padding": "0.625rem 1rem",
                                "_hover": {"bg": COLORS["neutral-50"]},
                            },
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon("pencil", size=16),
                                rx.text("Modifier"),
                                spacing="2",
                            ),
                            on_click=ValidationState.toggle_edit,
                            size="2",
                            style={
                                "bg": COLORS["primary-600"],
                                "color": COLORS["white"],
                                "border_radius": RADIUS["lg"],
                                "padding": "0.625rem 1rem",
                                "_hover": {"bg": COLORS["primary-700"]},
                            },
                        ),
                    ),
                    rx.cond(
                        ValidationState.edit_mode,
                        rx.button(
                            rx.cond(
                                ValidationState.is_loading,
                                rx.spinner(size="2"),
                                rx.hstack(
                                    rx.icon("calculator", size=16),
                                    rx.text("Recalculer"),
                                    spacing="2",
                                ),
                            ),
                            on_click=ValidationState.recalculate_payslip,
                            disabled=ValidationState.is_loading,
                            size="2",
                            style={
                                "bg": COLORS["white"],
                                "color": COLORS["primary-600"],
                                "border": f"1px solid {COLORS['primary-300']}",
                                "border_radius": RADIUS["lg"],
                                "padding": "0.625rem 1rem",
                                "_hover": {"bg": COLORS["primary-50"]},
                                "_disabled": {
                                    "bg": COLORS["neutral-100"],
                                    "cursor": "not-allowed",
                                },
                            },
                        ),
                        rx.fragment(),
                    ),
                    rx.button(
                        rx.cond(
                            ValidationState.is_loading,
                            rx.spinner(size="2"),
                            rx.hstack(
                                rx.icon("save", size=16),
                                rx.text("Enregistrer"),
                                spacing="2",
                            ),
                        ),
                        on_click=ValidationState.save_modifications,
                        disabled=ValidationState.is_loading,
                        size="2",
                        style={
                            "bg": COLORS["success-600"],
                            "color": COLORS["white"],
                            "border_radius": RADIUS["lg"],
                            "padding": "0.625rem 1rem",
                            "box_shadow": SHADOWS["button"],
                            "_hover": {
                                "bg": COLORS["success-500"],
                                "box_shadow": SHADOWS["button_hover"],
                            },
                            "_disabled": {
                                "bg": COLORS["neutral-300"],
                                "cursor": "not-allowed",
                            },
                        },
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),

                spacing="5",
                width="100%",
            ),
            max_width="1000px",
            max_height="85vh",
            overflow_y="auto",
            style={
                "padding": "2rem",
                "bg": COLORS["neutral-50"],
                "border_radius": RADIUS["2xl"],
            },
        ),
        open=ValidationState.show_edit_modal,
    )


def employee_card(emp: Dict) -> rx.Component:
    """Premium employee card."""
    # Determine status and styling (use Vars for conditionals)
    is_edge_case = emp.get("edge_case_flag", False)
    is_validated = emp.get("statut_validation", False)

    return rx.box(
        rx.vstack(
            # Header with name and status
            rx.hstack(
                rx.hstack(
                    rx.icon("user", size=20, color=COLORS["primary-600"], stroke_width=2),
                    rx.vstack(
                        rx.heading(
                            f"{emp['nom']} {emp['prenom']}",
                            size=HEADING_SM["size"],
                            weight=HEADING_SM["weight"],
                            color=COLORS["primary-900"],
                        ),
                        rx.text(
                            f"Matricule: {emp['matricule']}",
                            size=BODY_SM["size"],
                            color=COLORS["neutral-600"],
                        ),
                        spacing="1",
                        align="start",
                    ),
                    spacing="3",
                ),
                # Status badge
                rx.cond(
                    is_edge_case,
                    rx.box(
                        rx.hstack(
                            rx.icon("triangle-alert", size=16, color=COLORS["warning-600"]),
                            rx.text("À vérifier", size="1", weight="medium"),
                            spacing="1",
                        ),
                        bg=COLORS["warning-100"],
                        color=COLORS["warning-600"],
                        border=f"1px solid {COLORS['warning-300']}",
                        border_radius=RADIUS["badge"],
                        padding="0.375rem 0.75rem",
                    ),
                    rx.cond(
                        is_validated,
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-check", size=16, color=COLORS["success-600"]),
                                rx.text("Validé", size="1", weight="medium"),
                                spacing="1",
                            ),
                            bg=COLORS["success-100"],
                            color=COLORS["success-600"],
                            border=f"1px solid {COLORS['success-300']}",
                            border_radius=RADIUS["badge"],
                            padding="0.375rem 0.75rem",
                        ),
                        rx.box(
                            rx.hstack(
                                rx.icon("clock", size=16, color=COLORS["neutral-500"]),
                                rx.text("En attente", size="1", weight="medium"),
                                spacing="1",
                            ),
                            bg=COLORS["neutral-100"],
                            color=COLORS["neutral-600"],
                            border=f"1px solid {COLORS['neutral-300']}",
                            border_radius=RADIUS["badge"],
                            padding="0.375rem 0.75rem",
                        ),
                    ),
                ),
                justify="between",
                width="100%",
                align="center",
            ),

            # Edge case reason
            rx.cond(
                is_edge_case,
                rx.box(
                    rx.hstack(
                        rx.icon("info", size=16, color=COLORS["warning-600"]),
                        rx.text(
                            emp.get("edge_case_reason", ""),
                            size=BODY_SM["size"],
                            color=COLORS["warning-600"],
                        ),
                        spacing="2",
                    ),
                    bg=COLORS["warning-100"],
                    border=f"1px solid {COLORS['warning-600']}",
                    border_radius=RADIUS["lg"],
                    padding="0.75rem",
                ),
                rx.fragment(),
            ),

            # Metrics grid
            rx.grid(
                rx.vstack(
                    rx.text(
                        "Salaire brut",
                        size=LABEL["size"],
                        weight=LABEL["weight"],
                        color=COLORS["neutral-500"],
                        text_transform=LABEL["text_transform"],
                        letter_spacing=LABEL["letter_spacing"],
                    ),
                    rx.text(
                        f"{emp.get('salaire_brut', 0):,.2f} €",
                        size=HEADING_SM["size"],
                        weight="bold",
                        color=COLORS["primary-900"],
                        font_variant_numeric="tabular-nums",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.vstack(
                    rx.text(
                        "Charges salariales",
                        size=LABEL["size"],
                        weight=LABEL["weight"],
                        color=COLORS["neutral-500"],
                        text_transform=LABEL["text_transform"],
                        letter_spacing=LABEL["letter_spacing"],
                    ),
                    rx.text(
                        f"{emp.get('total_charges_salariales', 0):,.2f} €",
                        size=HEADING_SM["size"],
                        weight="bold",
                        color=COLORS["neutral-700"],
                        font_variant_numeric="tabular-nums",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.vstack(
                    rx.text(
                        "Salaire net",
                        size=LABEL["size"],
                        weight=LABEL["weight"],
                        color=COLORS["neutral-500"],
                        text_transform=LABEL["text_transform"],
                        letter_spacing=LABEL["letter_spacing"],
                    ),
                    rx.text(
                        f"{emp.get('salaire_net', 0):,.2f} €",
                        size=HEADING_SM["size"],
                        weight="bold",
                        color=COLORS["success-600"],
                        font_variant_numeric="tabular-nums",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.vstack(
                    rx.text(
                        "Coût total",
                        size=LABEL["size"],
                        weight=LABEL["weight"],
                        color=COLORS["neutral-500"],
                        text_transform=LABEL["text_transform"],
                        letter_spacing=LABEL["letter_spacing"],
                    ),
                    rx.text(
                        f"{emp.get('cout_total_employeur', 0):,.2f} €",
                        size=HEADING_SM["size"],
                        weight="bold",
                        color=COLORS["info-600"],
                        font_variant_numeric="tabular-nums",
                    ),
                    spacing="1",
                    align="start",
                ),
                columns="4",
                spacing=COMPONENT_SPACING["grid_gap"],
                width="100%",
            ),

            # Action buttons
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("pencil", size=16),
                        rx.text("Modifier"),
                        spacing="2",
                    ),
                    on_click=ValidationState.select_employee(emp["matricule"]),
                    size="2",
                    style={
                        "bg": COLORS["white"],
                        "color": COLORS["primary-600"],
                        "border": f"1px solid {COLORS['primary-300']}",
                        "border_radius": RADIUS["lg"],
                        "padding": "0.625rem 1rem",
                        "_hover": {
                            "bg": COLORS["primary-50"],
                            "border_color": COLORS["primary-400"],
                        },
                    },
                ),
                rx.cond(
                    ~is_validated,
                    rx.button(
                        rx.hstack(
                            rx.icon("circle-check", size=16),
                            rx.text("Valider"),
                            spacing="2",
                        ),
                        on_click=ValidationState.validate_employee(emp["matricule"]),
                        size="2",
                        style={
                            "bg": COLORS["success-600"],
                            "color": COLORS["white"],
                            "border_radius": RADIUS["lg"],
                            "padding": "0.625rem 1rem",
                            "_hover": {"bg": COLORS["success-500"]},
                        },
                    ),
                    rx.fragment(),
                ),
                spacing="3",
            ),

            spacing="4",
            width="100%",
        ),
        bg=COLORS["white"],
        border=rx.cond(
            is_edge_case,
            f"2px solid {COLORS['error-300']}",
            f"2px solid {COLORS['neutral-200']}",
        ),
        border_radius=RADIUS["card"],
        padding=COMPONENT_SPACING["card_padding_lg"],
        box_shadow=SHADOWS["card"],
        transition="all 0.25s ease",
        _hover={
            "box_shadow": SHADOWS["card_hover"],
            "transform": rx.cond(is_edge_case, "none", "translateY(-2px)"),
        },
    )


def index() -> rx.Component:
    """Premium validation page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    # Page header
                    rx.vstack(
                        rx.heading(
                            "Validation des bulletins",
                            size=HEADING_XL["size"],
                            weight=HEADING_XL["weight"],
                            letter_spacing=HEADING_XL["letter_spacing"],
                            color=COLORS["primary-900"],
                        ),
                        rx.text(
                            "Vérifiez et validez les bulletins de paie calculés",
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

                    # Error message
                    rx.cond(
                        ValidationState.error_message != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("circle-alert", size=20, color=COLORS["error-600"]),
                                rx.text(
                                    ValidationState.error_message,
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
                        rx.fragment(),
                    ),

                    # Filters bar
                    rx.box(
                        rx.hstack(
                            rx.input(
                                placeholder="Rechercher par nom ou matricule...",
                                value=ValidationState.search_query,
                                on_change=ValidationState.set_search,
                                size="2",
                                style={
                                    "flex": "1",
                                    "bg": COLORS["white"],
                                    "border": f"1px solid {COLORS['neutral-300']}",
                                    "border_radius": RADIUS["lg"],
                                    "padding": "0.625rem 1rem",
                                    "_focus": {
                                        "border_color": COLORS["primary-500"],
                                        "box_shadow": SHADOWS["focus_ring"],
                                    },
                                },
                            ),
                            rx.select(
                                ["Tous", "À vérifier", "Validés"],
                                value=ValidationState.status_filter,
                                on_change=ValidationState.set_filter,
                                size="2",
                                style={
                                    "width": "180px",
                                    "bg": COLORS["white"],
                                    "border": f"1px solid {COLORS['neutral-300']}",
                                    "border_radius": RADIUS["lg"],
                                    "_hover": {"border_color": COLORS["primary-300"]},
                                },
                            ),
                            rx.box(
                                rx.hstack(
                                    rx.icon("triangle-alert", size=20, color=COLORS["error-600"], stroke_width=2),
                                    rx.text(
                                        "Cas particuliers:",
                                        size=BODY_SM["size"],
                                        weight="medium",
                                        color=COLORS["neutral-700"],
                                    ),
                                    rx.box(
                                        rx.text(
                                            ValidationState.edge_case_count,
                                            size="1",
                                            weight="bold",
                                        ),
                                        bg=COLORS["error-100"],
                                        color=COLORS["error-600"],
                                        border=f"1px solid {COLORS['error-300']}",
                                        border_radius=RADIUS["badge"],
                                        padding="0.25rem 0.625rem",
                                    ),
                                    spacing="2",
                                ),
                                padding="0.625rem 1rem",
                                bg=COLORS["neutral-50"],
                                border=f"1px solid {COLORS['neutral-200']}",
                                border_radius=RADIUS["lg"],
                            ),
                            spacing="3",
                            width="100%",
                            align="center",
                        ),
                        bg=COLORS["white"],
                        border=f"1px solid {COLORS['neutral-200']}",
                        border_radius=RADIUS["card"],
                        padding=COMPONENT_SPACING["card_padding"],
                        box_shadow=SHADOWS["card"],
                    ),

                    # Loading indicator or employee list
                    rx.cond(
                        ValidationState.is_loading,
                        rx.center(
                            rx.vstack(
                                rx.spinner(size="3", color=COLORS["primary-600"]),
                                rx.text(
                                    "Chargement des employés...",
                                    size=BODY_SM["size"],
                                    color=COLORS["neutral-600"],
                                ),
                                spacing="3",
                            ),
                            padding="4rem",
                        ),
                        rx.vstack(
                            rx.foreach(
                                ValidationState.filtered_employees,
                                employee_card,
                            ),
                            spacing=COMPONENT_SPACING["section_gap"],
                            width="100%",
                        ),
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
        # Edit modal
        edit_modal(),
        on_mount=ValidationState.load_employees,
    )
