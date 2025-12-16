"""Configuration page (admin only)."""
import reflex as rx
from typing import List, Dict
from ..state import GlobalState
from ..components import navbar, sidebar_nav
from ..services.pdf_storage import StorageConfig, StorageConfigManager


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

    # PDF Storage config
    storage_enabled: bool = False
    storage_type: str = "local"
    local_base_path: str = "data/pdfs"
    sftp_host: str = ""
    sftp_port: int = 22
    sftp_username: str = ""
    sftp_password: str = ""
    sftp_remote_base_path: str = "/"
    sftp_private_key_path: str = ""
    folder_pattern: str = "{company_name}/{year}/{month}"
    filename_pattern: str = "{type}_{matricule}_{year}_{month}.pdf"

    config_status: str = ""
    
    def load_config(self):
        """Load configuration."""
        # Load company info and users
        self.company_name = "Example Company"
        self.users = [
            {"username": "admin", "name": "Admin User", "role": "admin"},
            {"username": "comptable", "name": "Comptable User", "role": "comptable"},
        ]

        # Load storage config
        config_mgr = StorageConfigManager(Path("data/config/storage_config.json"))
        storage_config = config_mgr.load_config()
        if storage_config:
            self.storage_enabled = storage_config.enabled
            self.storage_type = storage_config.storage_type
            self.local_base_path = storage_config.local_base_path
            self.sftp_host = storage_config.sftp_host
            self.sftp_port = storage_config.sftp_port
            self.sftp_username = storage_config.sftp_username
            self.sftp_password = storage_config.sftp_password
            self.sftp_remote_base_path = storage_config.sftp_remote_base_path
            self.sftp_private_key_path = storage_config.sftp_private_key_path
            self.folder_pattern = storage_config.folder_pattern
            self.filename_pattern = storage_config.filename_pattern
    
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

    def save_storage_config(self):
        """Save storage configuration."""
        try:
            storage_config = StorageConfig(
                storage_type=self.storage_type,
                enabled=self.storage_enabled,
                folder_pattern=self.folder_pattern,
                filename_pattern=self.filename_pattern,
                local_base_path=self.local_base_path,
                sftp_host=self.sftp_host,
                sftp_port=self.sftp_port,
                sftp_username=self.sftp_username,
                sftp_password=self.sftp_password,
                sftp_remote_base_path=self.sftp_remote_base_path,
                sftp_private_key_path=self.sftp_private_key_path,
            )

            config_mgr = StorageConfigManager(Path("data/config/storage_config.json"))
            if config_mgr.save_config(storage_config):
                self.config_status = "Storage configuration saved successfully"
            else:
                self.config_status = "Failed to save storage configuration"
        except Exception as e:
            self.config_status = f"Error saving storage config: {str(e)}"


def storage_tab_content() -> rx.Component:
    """Storage configuration tab content."""
    return rx.vstack(
        rx.heading("PDF Storage Configuration", size="6"),
        rx.text("Configure where generated PDFs will be saved", size="2", color="#6c757d"),

        # Enable storage toggle
        rx.hstack(
            rx.switch(
                checked=ConfigState.storage_enabled,
                on_change=ConfigState.storage_enabled.set,
            ),
            rx.text("Enable automatic PDF storage", weight="bold"),
            spacing="3",
        ),

        # Storage type selection
        rx.vstack(
            rx.text("Storage Type", weight="bold"),
            rx.select(
                ["local", "sftp"],
                value=ConfigState.storage_type,
                on_change=ConfigState.storage_type.set,
            ),
            spacing="2",
        ),

        # Path patterns
        rx.vstack(
            rx.text("Folder Pattern", weight="bold"),
            rx.text("Placeholders: {company_name}, {company_id}, {year}, {month}", size="1", color="#6c757d"),
            rx.input(
                value=ConfigState.folder_pattern,
                on_change=ConfigState.folder_pattern.set,
            ),
            spacing="1",
        ),

        rx.vstack(
            rx.text("Filename Pattern", weight="bold"),
            rx.text("Placeholders: {type}, {matricule}, {nom}, {prenom}, {year}, {month}, {timestamp}", size="1", color="#6c757d"),
            rx.input(
                value=ConfigState.filename_pattern,
                on_change=ConfigState.filename_pattern.set,
            ),
            spacing="1",
        ),

        # Local storage config
        rx.cond(
            ConfigState.storage_type == "local",
            rx.vstack(
                rx.divider(),
                rx.heading("Local Storage", size="5"),
                rx.input(
                    placeholder="Base path (e.g., data/pdfs)",
                    value=ConfigState.local_base_path,
                    on_change=ConfigState.local_base_path.set,
                ),
                spacing="3",
            ),
            rx.fragment(),
        ),

        # SFTP config
        rx.cond(
            ConfigState.storage_type == "sftp",
            rx.vstack(
                rx.divider(),
                rx.heading("SFTP Configuration", size="5"),
                rx.vstack(
                    rx.input(placeholder="Host (e.g., sftp.example.com)", value=ConfigState.sftp_host, on_change=ConfigState.sftp_host.set),
                    rx.input(placeholder="Port (default: 22)", type="number", value=ConfigState.sftp_port, on_change=ConfigState.sftp_port.set),
                    rx.input(placeholder="Username", value=ConfigState.sftp_username, on_change=ConfigState.sftp_username.set),
                    rx.input(placeholder="Password", type="password", value=ConfigState.sftp_password, on_change=ConfigState.sftp_password.set),
                    rx.input(placeholder="Private Key Path (optional)", value=ConfigState.sftp_private_key_path, on_change=ConfigState.sftp_private_key_path.set),
                    rx.input(placeholder="Remote base path (e.g., /uploads/pdfs)", value=ConfigState.sftp_remote_base_path, on_change=ConfigState.sftp_remote_base_path.set),
                    spacing="3",
                ),
                spacing="3",
            ),
            rx.fragment(),
        ),

        rx.button("Save Storage Configuration", on_click=ConfigState.save_storage_config, size="3"),

        spacing="4",
        width="100%",
    )


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
                                rx.tabs.trigger("PDF Storage", value="storage"),
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

                            rx.tabs.content(
                                storage_tab_content(),
                                value="storage",
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
