"""Configuration page (admin only)"""

import reflex as rx
from ..state import AuthState
from ..components import layout
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from services.auth import AuthManager


class ConfigState(rx.State):
    """Configuration state"""
    
    # Company info
    company_name: str = ""
    company_siret: str = ""
    company_address: str = ""
    company_phone: str = ""
    company_email: str = ""
    employer_number_monaco: str = ""
    
    # User management
    new_username: str = ""
    new_name: str = ""
    new_role: str = "comptable"
    new_password: str = ""
    users_list: list[dict] = []
    
    config_status: str = ""
    
    def load_config(self):
        """Load current configuration"""
        from services.shared_utils import get_payroll_system
        
        system = get_payroll_system()
        self.company_name = system.company_info.get('name', '')
        self.company_siret = system.company_info.get('siret', '')
        self.company_address = system.company_info.get('address', '')
        self.company_phone = system.company_info.get('phone', '')
        self.company_email = system.company_info.get('email', '')
        self.employer_number_monaco = system.company_info.get('employer_number_monaco', '')
        
        # Load users
        self.users_list = AuthManager.list_users()
    
    def save_company_info(self):
        """Save company information"""
        if self.employer_number_monaco and (
            not self.employer_number_monaco.isdigit() or len(self.employer_number_monaco) != 5
        ):
            self.config_status = "❌ Employer number must be exactly 5 digits"
            return
        
        config_dir = Path("data/config")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        updated_info = {
            'name': self.company_name,
            'siret': self.company_siret,
            'address': self.company_address,
            'phone': self.company_phone,
            'email': self.company_email,
            'employer_number_monaco': self.employer_number_monaco,
        }
        
        config_file = config_dir / "company_info.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(updated_info, f, indent=2)
        
        self.config_status = "✅ Company information saved"
    
    def add_user(self):
        """Add or update user"""
        if not self.new_username or not self.new_password:
            self.config_status = "❌ Username and password required"
            return
        
        try:
            AuthManager.add_or_update_user(
                self.new_username,
                self.new_password,
                self.new_role,
                self.new_name
            )
            self.config_status = f"✅ User '{self.new_username}' saved"
            self.load_config()
            
            # Clear form
            self.new_username = ""
            self.new_name = ""
            self.new_password = ""
            
        except Exception as e:
            self.config_status = f"❌ Error: {str(e)}"


def page() -> rx.Component:
    """Config page layout"""
    
    auth_state = AuthState()
    
    # Check if admin
    if not auth_state.is_admin:
        return layout(
            rx.vstack(
                rx.heading("⚙️ Configuration", size="7"),
                rx.callout(
                    "Access restricted to administrators",
                    icon="shield",
                    color_scheme="red",
                ),
            ),
            auth_state,
        )
    
    return layout(
        rx.vstack(
            rx.heading("⚙️ Configuration", size="7"),
            
            rx.tabs(
                rx.tabs_list(
                    rx.tabs_trigger("Company", value="company"),
                    rx.tabs_trigger("Users", value="users"),
                ),
                rx.tabs_content(
                    rx.vstack(
                        rx.heading("Company Information", size="4"),
                        rx.form(
                            rx.vstack(
                                rx.input(
                                    placeholder="Company name",
                                    value=ConfigState.company_name,
                                    on_change=ConfigState.set_company_name,
                                ),
                                rx.input(
                                    placeholder="SIRET",
                                    value=ConfigState.company_siret,
                                    on_change=ConfigState.set_company_siret,
                                ),
                                rx.text_area(
                                    placeholder="Address",
                                    value=ConfigState.company_address,
                                    on_change=ConfigState.set_company_address,
                                ),
                                rx.input(
                                    placeholder="Phone",
                                    value=ConfigState.company_phone,
                                    on_change=ConfigState.set_company_phone,
                                ),
                                rx.input(
                                    placeholder="Email",
                                    value=ConfigState.company_email,
                                    on_change=ConfigState.set_company_email,
                                ),
                                rx.input(
                                    placeholder="Monaco Employer Number (5 digits)",
                                    value=ConfigState.employer_number_monaco,
                                    on_change=ConfigState.set_employer_number_monaco,
                                ),
                                rx.button(
                                    "💾 Save",
                                    type="submit",
                                    size="3",
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            on_submit=ConfigState.save_company_info,
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    value="company",
                ),
                rx.tabs_content(
                    rx.vstack(
                        rx.heading("User Management", size="4"),
                        
                        # Users list
                        rx.box(
                            rx.foreach(
                                ConfigState.users_list,
                                lambda u: rx.box(
                                    rx.hstack(
                                        rx.text(u.get('username', ''), weight="bold"),
                                        rx.text(u.get('name', ''), color="gray"),
                                        rx.badge(u.get('role', 'comptable')),
                                        spacing="3",
                                    ),
                                    padding="1rem",
                                    bg="white",
                                    border_radius="0.5rem",
                                    margin_bottom="0.5rem",
                                ),
                            ),
                            width="100%",
                        ),
                        
                        rx.divider(),
                        
                        # Add user form
                        rx.heading("Add/Update User", size="4"),
                        rx.form(
                            rx.vstack(
                                rx.input(
                                    placeholder="Username",
                                    value=ConfigState.new_username,
                                    on_change=ConfigState.set_new_username,
                                ),
                                rx.input(
                                    placeholder="Name (optional)",
                                    value=ConfigState.new_name,
                                    on_change=ConfigState.set_new_name,
                                ),
                                rx.select(
                                    ["comptable", "admin"],
                                    value=ConfigState.new_role,
                                    on_change=ConfigState.set_new_role,
                                ),
                                rx.input(
                                    placeholder="Password",
                                    type="password",
                                    value=ConfigState.new_password,
                                    on_change=ConfigState.set_new_password,
                                ),
                                rx.button(
                                    "Add User",
                                    type="submit",
                                    size="3",
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            on_submit=ConfigState.add_user,
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    value="users",
                ),
                default_value="company",
            ),
            
            rx.cond(
                ConfigState.config_status != "",
                rx.callout(ConfigState.config_status, icon="info", size="2"),
            ),
            
            spacing="6",
            width="100%",
            on_mount=ConfigState.load_config,
        ),
        auth_state,
    )
