"""Validation page"""

import reflex as rx
from ..state import AuthState, CompanyState, DataState
from ..components import layout, metric_card
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from services.data_mgt import DataManager


class ValidationState(rx.State):
    """Validation page state"""
    
    search_query: str = ""
    status_filter: str = "Tous"
    selected_employee: dict = {}
    edit_mode: bool = False
    
    @rx.var
    def filtered_employees(self) -> list[dict]:
        """Get filtered employees"""
        data_state = self.get_state(DataState)
        employees = data_state.processed_data
        
        if not employees:
            return []
        
        # Apply search filter
        if self.search_query:
            query = self.search_query.lower()
            employees = [
                e for e in employees
                if query in str(e.get('matricule', '')).lower()
                or query in str(e.get('nom', '')).lower()
                or query in str(e.get('prenom', '')).lower()
            ]
        
        # Apply status filter
        if self.status_filter == "À vérifier":
            employees = [e for e in employees if e.get('edge_case_flag')]
        elif self.status_filter == "Validés":
            employees = [e for e in employees if e.get('statut_validation')]
        
        return employees
    
    def select_employee(self, matricule: str):
        """Select employee for editing"""
        data_state = self.get_state(DataState)
        employee = next(
            (e for e in data_state.processed_data if e.get('matricule') == matricule),
            None
        )
        if employee:
            self.selected_employee = employee
            self.edit_mode = True
    
    def validate_employee(self, matricule: str):
        """Validate an employee"""
        import polars as pl
        
        company_state = self.get_state(CompanyState)
        data_state = self.get_state(DataState)
        
        month, year = map(int, company_state.current_period.split('-'))
        df = DataManager.load_period_data(company_state.current_company, month, year)
        
        # Update validation status
        df = df.with_columns([
            pl.when(pl.col('matricule') == matricule)
            .then(pl.lit(True))
            .otherwise(pl.col('statut_validation'))
            .alias('statut_validation'),
            pl.when(pl.col('matricule') == matricule)
            .then(pl.lit(False))
            .otherwise(pl.col('edge_case_flag'))
            .alias('edge_case_flag')
        ])
        
        # Save
        DataManager.save_period_data(df, company_state.current_company, month, year)
        
        # Reload
        data_state.load_period_data()
    
    def close_edit(self):
        """Close edit mode"""
        self.edit_mode = False
        self.selected_employee = {}


def employee_row(employee: dict) -> rx.Component:
    """Employee row component"""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.heading(
                    f"{employee.get('nom', '')} {employee.get('prenom', '')}",
                    size="4",
                ),
                rx.text(employee.get('matricule', ''), size="2", color="gray"),
                align_items="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.box(
                    rx.vstack(
                        rx.text("Brut", size="1", color="gray"),
                        rx.text(f"{employee.get('salaire_brut', 0):,.2f} €", size="2"),
                        spacing="1",
                    ),
                    padding="0.5rem",
                ),
                rx.box(
                    rx.vstack(
                        rx.text("Net", size="1", color="gray"),
                        rx.text(f"{employee.get('salaire_net', 0):,.2f} €", size="2"),
                        spacing="1",
                    ),
                    padding="0.5rem",
                ),
                rx.button(
                    "Edit",
                    on_click=lambda: ValidationState.select_employee(employee.get('matricule')),
                    variant="outline",
                    size="2",
                ),
                rx.button(
                    "✓",
                    on_click=lambda: ValidationState.validate_employee(employee.get('matricule')),
                    color_scheme="green",
                    size="2",
                ),
                spacing="2",
            ),
            width="100%",
            align_items="center",
        ),
        padding="1rem",
        bg="white",
        border_radius="0.5rem",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.1)",
        margin_bottom="0.5rem",
    )


def page() -> rx.Component:
    """Validation page layout"""
    return layout(
        rx.vstack(
            rx.heading("✅ Validation et Modification", size="7"),
            
            rx.hstack(
                rx.input(
                    placeholder="Search (matricule, nom, prénom)",
                    value=ValidationState.search_query,
                    on_change=ValidationState.set_search_query,
                    width="300px",
                ),
                rx.select(
                    ["Tous", "À vérifier", "Validés"],
                    value=ValidationState.status_filter,
                    on_change=ValidationState.set_status_filter,
                ),
                rx.spacer(),
                metric_card(
                    "Cases to verify",
                    str(len([e for e in DataState.processed_data if e.get('edge_case_flag')])),
                ),
                width="100%",
                align_items="center",
            ),
            
            rx.divider(),
            
            rx.cond(
                len(ValidationState.filtered_employees) == 0,
                rx.text("No employees found", color="gray"),
                rx.foreach(
                    ValidationState.filtered_employees,
                    employee_row,
                ),
            ),
            
            # Edit modal
            rx.cond(
                ValidationState.edit_mode,
                rx.dialog(
                    rx.dialog_content(
                        rx.dialog_title(
                            f"Edit {ValidationState.selected_employee.get('nom', '')} "
                            f"{ValidationState.selected_employee.get('prenom', '')}"
                        ),
                        rx.dialog_description(
                            f"Matricule: {ValidationState.selected_employee.get('matricule', '')}"
                        ),
                        rx.vstack(
                            rx.text("Editing functionality - simplified for MVP"),
                            rx.button(
                                "Close",
                                on_click=ValidationState.close_edit,
                            ),
                            spacing="4",
                        ),
                    ),
                    open=ValidationState.edit_mode,
                ),
            ),
            
            spacing="6",
            width="100%",
        ),
        AuthState,
    )
