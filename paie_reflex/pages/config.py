"""Configuration page (admin only)."""
import reflex as rx
from typing import List, Dict
from ..state import GlobalState
from ..components import navbar, sidebar_nav
from ..services.pdf_storage import StorageConfig, StorageConfigManager
from pathlib import Path

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

    # Setter methods for all fields
    def set_address(self, value):
        self.address = value
    def set_company_name(self, value):
        self.company_name = value
    def set_email(self, value):
        self.email = value
    def set_employer_number(self, value):
        self.employer_number = value
    def set_filename_pattern(self, value):
        self.filename_pattern = value
    def set_folder_pattern(self, value):
        self.folder_pattern = value
    def set_local_base_path(self, value):
        self.local_base_path = value
    def set_new_name(self, value):
        self.new_name = value
    def set_new_password(self, value):
        self.new_password = value
    def set_new_role(self, value):
        self.new_role = value
    def set_new_username(self, value):
        self.new_username = value
    def set_phone(self, value):
        self.phone = value
    def set_sftp_host(self, value):
        self.sftp_host = value
    def set_sftp_password(self, value):
        self.sftp_password = value
    def set_sftp_port(self, value):
        self.sftp_port = value
    def set_sftp_private_key_path(self, value):
        self.sftp_private_key_path = value
    def set_sftp_remote_base_path(self, value):
        self.sftp_remote_base_path = value
    def set_sftp_username(self, value):
        self.sftp_username = value
    def set_siret(self, value):
        self.siret = value
    def set_storage_enabled(self, value):
        self.storage_enabled = value
    def set_storage_type(self, value):
        self.storage_type = value

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
        self.config_status = "Informations société enregistrées"

    def add_user(self):
        """Add new user."""
        if not self.new_username or not self.new_password:
            self.config_status = "Nom d'utilisateur et mot de passe requis"
            return

        self.users.append({
            "username": self.new_username,
            "name": self.new_name,
            "role": self.new_role,
        })
        self.config_status = f"Utilisateur {self.new_username} ajouté"
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
                self.config_status = "Configuration de stockage enregistrée avec succès"
            else:
                self.config_status = "Échec de l'enregistrement de la configuration de stockage"
        except Exception as e:
            self.config_status = f"Erreur lors de l'enregistrement de la config de stockage: {str(e)}"


def storage_tab_content() -> rx.Component:
    """Storage configuration tab content."""
    return rx.vstack(
        rx.heading("Configuration stockage PDF", size="6"),
        rx.text("Configurer l'emplacement de sauvegarde des PDF générés", size="2", color="#6c757d"),

        # Enable storage toggle
        rx.hstack(
            rx.switch(
                checked=ConfigState.storage_enabled,
                on_change=ConfigState.set_storage_enabled,
            ),
            rx.text("Activer le stockage automatique des PDF", weight="bold"),
            spacing="3",
        ),

        # Storage type selection
        rx.vstack(
            rx.text("Type de stockage", weight="bold"),
            rx.select(
                ["local", "sftp"],
                value=ConfigState.storage_type,
                on_change=ConfigState.set_storage_type,
            ),
            spacing="2",
        ),

        # Path patterns
        rx.vstack(
            rx.text("Modèle de dossier", weight="bold"),
            rx.text("Variables: {company_name}, {company_id}, {year}, {month}", size="1", color="#6c757d"),
            rx.input(
                value=ConfigState.folder_pattern,
                on_change=ConfigState.set_folder_pattern,
            ),
            spacing="1",
        ),

        rx.vstack(
            rx.text("Modèle de nom de fichier", weight="bold"),
            rx.text("Variables: {type}, {matricule}, {nom}, {prenom}, {year}, {month}, {timestamp}", size="1", color="#6c757d"),
            rx.input(
                value=ConfigState.filename_pattern,
                on_change=ConfigState.set_filename_pattern,
            ),
            spacing="1",
        ),

        # Local storage config
        rx.cond(
            ConfigState.storage_type == "local",
            rx.vstack(
                rx.divider(),
                rx.heading("Stockage local", size="5"),
                rx.input(
                    placeholder="Chemin de base (ex: data/pdfs)",
                    value=ConfigState.local_base_path,
                    on_change=ConfigState.set_local_base_path,
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
                rx.heading("Configuration SFTP", size="5"),
                rx.vstack(
                    rx.input(placeholder="Hôte (ex: sftp.example.com)", value=ConfigState.sftp_host, on_change=ConfigState.set_sftp_host),
                    rx.input(placeholder="Port (défaut: 22)", type="number", value=ConfigState.sftp_port, on_change=ConfigState.set_sftp_port),
                    rx.input(placeholder="Nom d'utilisateur", value=ConfigState.sftp_username, on_change=ConfigState.set_sftp_username),
                    rx.input(placeholder="Mot de passe", type="password", value=ConfigState.sftp_password, on_change=ConfigState.set_sftp_password),
                    rx.input(placeholder="Chemin clé privée (optionnel)", value=ConfigState.sftp_private_key_path, on_change=ConfigState.set_sftp_private_key_path),
                    rx.input(placeholder="Chemin distant de base (ex: /uploads/pdfs)", value=ConfigState.sftp_remote_base_path, on_change=ConfigState.set_sftp_remote_base_path),
                    spacing="3",
                ),
                spacing="3",
            ),
            rx.fragment(),
        ),

        rx.button("Enregistrer la configuration de stockage", on_click=ConfigState.save_storage_config, size="3"),

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
                        "Accès administrateur requis",
                        icon="lock",
                        color_scheme="red",
                    ),
                    rx.vstack(
                        rx.heading("Configuration", size="8", margin_bottom="1rem"),

                        rx.tabs.root(
                            rx.tabs.list(
                                rx.tabs.trigger("Société", value="company"),
                                rx.tabs.trigger("Utilisateurs", value="users"),
                                rx.tabs.trigger("Stockage PDF", value="storage"),
                            ),

                            rx.tabs.content(
                                rx.vstack(
                                    rx.heading("Informations société", size="6"),

                                    rx.form(
                                        rx.vstack(
                                            rx.input(
                                                placeholder="Nom de la société",
                                                value=ConfigState.company_name,
                                                on_change=ConfigState.set_company_name,
                                            ),
                                            rx.input(
                                                placeholder="SIRET",
                                                value=ConfigState.siret,
                                                on_change=ConfigState.set_siret,
                                            ),
                                            rx.text_area(
                                                placeholder="Adresse",
                                                value=ConfigState.address,
                                                on_change=ConfigState.set_address,
                                            ),
                                            rx.input(
                                                placeholder="Téléphone",
                                                value=ConfigState.phone,
                                                on_change=ConfigState.set_phone,
                                            ),
                                            rx.input(
                                                placeholder="Email",
                                                value=ConfigState.email,
                                                on_change=ConfigState.set_email,
                                            ),
                                            rx.input(
                                                placeholder="Numéro employeur Monaco",
                                                value=ConfigState.employer_number,
                                                on_change=ConfigState.set_employer_number,
                                            ),
                                            rx.button("Enregistrer", on_click=ConfigState.save_company_info),
                                            spacing="4",
                                        ),
                                    ),

                                    spacing="4",
                                ),
                                value="company",
                            ),

                            rx.tabs.content(
                                rx.vstack(
                                    rx.heading("Gestion des utilisateurs", size="6"),

                                    rx.heading("Utilisateurs actuels", size="5"),
                                    rx.data_table(
                                        data=ConfigState.users,
                                        columns=["username", "name", "role"],
                                    ),

                                    rx.divider(),

                                    rx.heading("Ajouter un utilisateur", size="5"),
                                    rx.form(
                                        rx.vstack(
                                            rx.input(
                                                placeholder="Nom d'utilisateur",
                                                value=ConfigState.new_username,
                                                on_change=ConfigState.set_new_username,
                                            ),
                                            rx.input(
                                                placeholder="Nom",
                                                value=ConfigState.new_name,
                                                on_change=ConfigState.set_new_name,
                                            ),
                                            rx.input(
                                                placeholder="Mot de passe",
                                                type="password",
                                                value=ConfigState.new_password,
                                                on_change=ConfigState.set_new_password,
                                            ),
                                            rx.select(
                                                ["comptable", "admin"],
                                                value=ConfigState.new_role,
                                                on_change=ConfigState.set_new_role,
                                            ),
                                            rx.button("Ajouter utilisateur", on_click=ConfigState.add_user),
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
                                icon="circle-check",
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
