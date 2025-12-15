"""Validation page for reviewing and editing payslips."""
import reflex as rx
from typing import List, Dict
from ..state import GlobalState
from ..components import navbar, sidebar_nav


class ValidationState(GlobalState):
    """State for validation page."""
    
    employees: List[Dict] = []
    search_query: str = ""
    status_filter: str = "All"
    selected_employee: Dict = {}
    edit_mode: bool = False
    modifications: Dict = {}
    
    def load_employees(self):
        """Load employees for current period."""
        # Implement loading from DataManager
        # Mock data for MVP
        self.employees = [
            {
                "matricule": "001",
                "nom": "Dupont",
                "prenom": "Jean",
                "salaire_brut": 3500.00,
                "salaire_net": 2800.00,
                "total_charges_salariales": 516.25,
                "cout_total_employeur": 4200.00,
                "statut_validation": False,
                "edge_case_flag": True,
                "edge_case_reason": "Absent days not declared",
            },
            {
                "matricule": "002",
                "nom": "Martin",
                "prenom": "Marie",
                "salaire_brut": 4200.00,
                "salaire_net": 3360.00,
                "total_charges_salariales": 619.50,
                "cout_total_employeur": 5040.00,
                "statut_validation": True,
                "edge_case_flag": False,
                "edge_case_reason": "",
            },
        ]
    
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
                self.selected_employee = emp
                self.edit_mode = False
                self.modifications = {}
                break
    
    def toggle_edit(self):
        """Toggle edit mode."""
        self.edit_mode = not self.edit_mode
        if not self.edit_mode:
            self.modifications = {}
    
    def save_modifications(self, reason: str):
        """Save modifications to employee."""
        if not reason:
            return
        
        # Apply modifications and save to DB
        # Log modifications using DataAuditLogger
        
        self.edit_mode = False
        self.modifications = {}
    
    def validate_employee(self, matricule: str):
        """Validate an employee's payslip."""
        for emp in self.employees:
            if emp["matricule"] == matricule:
                emp["statut_validation"] = True
                emp["edge_case_flag"] = False
                break
    
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
                    
                    # Employee list
                    rx.foreach(
                        ValidationState.filtered_employees,
                        employee_card,
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
        on_mount=ValidationState.load_employees,
    )
