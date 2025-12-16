"""Configuration page (admin only)."""
import reflex as rx
from typing import List, Dict
from ..state import GlobalState
from ..components import navbar, sidebar_nav


class ConfigState(GlobalState):
    """State for configuration page."""
    
    # Company info
    company_name: str = ""
    siret: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    employer_number: str = ""
    
    # User management
    users: List[Dict] = []
    new_username: str = ""
    new_password: str = ""
    new_role: str = "comptable"
    new_name: str = ""
    
    config_status: str = ""
    
    def load_config(self):
        """Load configuration."""
        # Load company info and users
        self.company_name = "Example Company"
        self.users = [
            {"username": "admin", "name": "Admin User", "role": "admin"},
            {"username": "comptable", "name": "Comptable User", "role": "comptable"},
        ]
    
    def save_company_info(self):
        """Save company information."""
        self.config_status = "Company info saved"
    
    def add_user(self):
        """Add new user."""
        if not self.new_username or not self.new_password:
            self.config_status = "Username and password required"
            return
        
        self.users.append({
            "username": self.new_username,
            "name": self.new_name,
            "role": self.new_role,
        })
        self.config_status = f"User {self.new_username} added"
        self.new_username = ""
        self.new_password = ""
        self.new_name = ""


def index() -> rx.Component:
    """Config page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.cond(
                    ~GlobalState.is_admin,
                    rx.callout(
                        "Admin access required",
                        icon="lock",
                        color_scheme="red",
                    ),
                    rx.vstack(
                        rx.heading("Configuration", size="8", margin_bottom="1rem"),
                        
                        rx.tabs.root(
                            rx.tabs.list(
                                rx.tabs.trigger("Company", value="company"),
                                rx.tabs.trigger("Users", value="users"),
                            ),
                            
                            rx.tabs.content(
                                rx.vstack(
                                    rx.heading("Company Information", size="6"),
                                    
                                    rx.form(
                                        rx.vstack(
                                            rx.input(
                                                placeholder="Company Name",
                                                value=ConfigState.company_name,
                                                on_change=ConfigState.company_name.set,
                                            ),
                                            rx.input(
                                                placeholder="SIRET",
                                                value=ConfigState.siret,
                                                on_change=ConfigState.siret.set,
                                            ),
                                            rx.text_area(
                                                placeholder="Address",
                                                value=ConfigState.address,
                                                on_change=ConfigState.address.set,
                                            ),
                                            rx.input(
                                                placeholder="Phone",
                                                value=ConfigState.phone,
                                                on_change=ConfigState.phone.set,
                                            ),
                                            rx.input(
                                                placeholder="Email",
                                                value=ConfigState.email,
                                                on_change=ConfigState.email.set,
                                            ),
                                            rx.input(
                                                placeholder="Monaco Employer Number",
                                                value=ConfigState.employer_number,
                                                on_change=ConfigState.employer_number.set,
                                            ),
                                            rx.button("Save", on_click=ConfigState.save_company_info),
                                            spacing="4",
                                        ),
                                    ),
                                    
                                    spacing="4",
                                ),
                                value="company",
                            ),
                            
                            rx.tabs.content(
                                rx.vstack(
                                    rx.heading("User Management", size="6"),
                                    
                                    rx.heading("Current Users", size="5"),
                                    rx.data_table(
                                        data=ConfigState.users,
                                        columns=["username", "name", "role"],
                                    ),
                                    
                                    rx.divider(),
                                    
                                    rx.heading("Add User", size="5"),
                                    rx.form(
                                        rx.vstack(
                                            rx.input(
                                                placeholder="Username",
                                                value=ConfigState.new_username,
                                                on_change=ConfigState.new_username.set,
                                            ),
                                            rx.input(
                                                placeholder="Name",
                                                value=ConfigState.new_name,
                                                on_change=ConfigState.new_name.set,
                                            ),
                                            rx.input(
                                                placeholder="Password",
                                                type="password",
                                                value=ConfigState.new_password,
                                                on_change=ConfigState.new_password.set,
                                            ),
                                            rx.select(
                                                ["comptable", "admin"],
                                                value=ConfigState.new_role,
                                                on_change=ConfigState.new_role.set,
                                            ),
                                            rx.button("Add User", on_click=ConfigState.add_user),
                                            spacing="4",
                                        ),
                                    ),
                                    
                                    spacing="4",
                                ),
                                value="users",
                            ),
                            
                            default_value="company",
                        ),
                        
                        rx.cond(
                            ConfigState.config_status,
                            rx.callout(
                                ConfigState.config_status,
                                icon="check-circle",
                                color_scheme="green",
                            ),
                            rx.fragment(),
                        ),
                        
                        spacing="5",
                        padding="2rem",
                        width="100%",
                    ),
                ),
                flex="1",
            ),
            spacing="0",
            width="100%",
            align_items="start",
        ),
        on_mount=ConfigState.load_config,
    )
