"""Configuration page (admin only)."""
import reflex as rx
from typing import List, Dict
from ..state import GlobalState
from ..components import navbar, sidebar_nav
from ..services.pdf_storage import StorageConfig, StorageConfigManager
from ..services.email_archive import EmailConfig, EmailConfigManager
from ..services.payslip_helpers import get_audit_logs, get_time_tracking_summary
from pathlib import Path
import polars as pl
import smtplib
import ssl

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

    # Audit log state
    audit_filter_company: str = "Toutes"
    audit_filter_user: str = ""
    time_tracking_data: List[Dict] = []
    modifications_data: List[Dict] = []

    # Email config
    email_provider: str = "gmail"
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""
    sender_name: str = "Service Paie"
    use_tls: bool = True
    use_ssl: bool = False
    reply_to: str = ""
    bcc_archive: str = ""
    email_test_result: str = ""

    config_status: str = ""

    @rx.var
    def company_filter_options(self) -> List[str]:
        """Get company filter options"""
        return ["Toutes"] + self.available_companies

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
    def set_audit_filter_company(self, value):
        self.audit_filter_company = value
    def set_audit_filter_user(self, value):
        self.audit_filter_user = value
    def set_email_provider(self, value):
        self.email_provider = value
        self._apply_email_provider_defaults(value)
    def set_smtp_server(self, value):
        self.smtp_server = value
    def set_smtp_port(self, value):
        self.smtp_port = value
    def set_sender_email(self, value):
        self.sender_email = value
    def set_sender_password(self, value):
        self.sender_password = value
    def set_sender_name(self, value):
        self.sender_name = value
    def set_use_tls(self, value):
        self.use_tls = value
    def set_use_ssl(self, value):
        self.use_ssl = value
    def set_reply_to(self, value):
        self.reply_to = value
    def set_bcc_archive(self, value):
        self.bcc_archive = value

    def _apply_email_provider_defaults(self, provider: str):
        """Apply default SMTP settings based on provider"""
        defaults = {
            "gmail": {"server": "smtp.gmail.com", "port": 587, "tls": True, "ssl": False},
            "outlook": {"server": "smtp-mail.outlook.com", "port": 587, "tls": True, "ssl": False},
            "office365": {"server": "smtp.office365.com", "port": 587, "tls": True, "ssl": False},
            "custom": {"server": "", "port": 587, "tls": True, "ssl": False}
        }
        if provider in defaults:
            self.smtp_server = defaults[provider]["server"]
            self.smtp_port = defaults[provider]["port"]
            self.use_tls = defaults[provider]["tls"]
            self.use_ssl = defaults[provider]["ssl"]

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

        # Load email config
        email_mgr = EmailConfigManager(Path("data/config/email_config.json"))
        email_config = email_mgr.load_config()
        if email_config:
            self.smtp_server = email_config.smtp_server
            self.smtp_port = email_config.smtp_port
            self.sender_email = email_config.sender_email
            self.sender_password = email_config.sender_password
            self.sender_name = email_config.sender_name
            self.use_tls = email_config.use_tls
            self.use_ssl = email_config.use_ssl
            self.reply_to = email_config.reply_to or ""
            self.bcc_archive = email_config.bcc_archive or ""
    
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

    def load_time_tracking(self):
        """Load time tracking summary"""
        company_filter = None if (not self.audit_filter_company or self.audit_filter_company == "Toutes") else self.audit_filter_company
        user_filter = self.audit_filter_user if self.audit_filter_user else None

        summary_df = get_time_tracking_summary(company=company_filter, user=user_filter)

        if not summary_df.is_empty():
            self.time_tracking_data = summary_df.to_dicts()
        else:
            self.time_tracking_data = []

    def load_modifications(self):
        """Load modification logs"""
        company_filter = None if (not self.audit_filter_company or self.audit_filter_company == "Toutes") else self.audit_filter_company
        user_filter = self.audit_filter_user if self.audit_filter_user else None

        logs_df = get_audit_logs(company=company_filter, user=user_filter)

        if not logs_df.is_empty():
            # Filter for modifications only
            mods_df = logs_df.filter(pl.col('entry_type') == 'modification')
            if not mods_df.is_empty():
                # Select relevant columns
                display_df = mods_df.select([
                    'timestamp', 'user', 'company', 'period',
                    'matricule', 'field', 'old_value', 'new_value', 'reason'
                ])
                self.modifications_data = display_df.to_dicts()
            else:
                self.modifications_data = []
        else:
            self.modifications_data = []

    def save_email_config(self):
        """Save email configuration"""
        try:
            email_config = EmailConfig(
                smtp_server=self.smtp_server,
                smtp_port=self.smtp_port,
                sender_email=self.sender_email,
                sender_password=self.sender_password,
                sender_name=self.sender_name,
                use_tls=self.use_tls,
                use_ssl=self.use_ssl,
                reply_to=self.reply_to if self.reply_to else None,
                bcc_archive=self.bcc_archive if self.bcc_archive else None,
            )

            email_mgr = EmailConfigManager(Path("data/config/email_config.json"))
            if email_mgr.save_config(email_config):
                self.config_status = "Configuration email enregistrée avec succès"
            else:
                self.config_status = "Échec de l'enregistrement de la configuration email"
        except Exception as e:
            self.config_status = f"Erreur lors de l'enregistrement de la config email: {str(e)}"

    def test_email_connection(self):
        """Test email SMTP connection"""
        try:
            context = ssl.create_default_context()

            if self.use_ssl:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context, timeout=10) as server:
                    server.login(self.sender_email, self.sender_password)
                    self.email_test_result = "Connexion réussie! Configuration valide."
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    if self.use_tls:
                        server.starttls(context=context)
                    server.login(self.sender_email, self.sender_password)
                    self.email_test_result = "Connexion réussie! Configuration valide."

        except smtplib.SMTPAuthenticationError:
            self.email_test_result = "Erreur: Échec d'authentification. Vérifiez l'email et le mot de passe."
        except smtplib.SMTPException as e:
            self.email_test_result = f"Erreur SMTP: {str(e)}"
        except Exception as e:
            self.email_test_result = f"Erreur de connexion: {str(e)}"


def email_tab_content() -> rx.Component:
    """Email configuration tab content."""
    return rx.vstack(
        rx.heading("Configuration Email SMTP", size="6"),
        rx.text("Paramétrer le serveur SMTP pour l'envoi automatique des bulletins", size="2", color="#6c757d"),

        # Provider selection
        rx.vstack(
            rx.text("Fournisseur email", weight="bold"),
            rx.select(
                ["gmail", "outlook", "office365", "custom"],
                value=ConfigState.email_provider,
                on_change=ConfigState.set_email_provider,
            ),
            spacing="2",
        ),

        rx.divider(),

        # SMTP Server settings
        rx.heading("Paramètres serveur", size="5"),
        rx.hstack(
            rx.vstack(
                rx.text("Serveur SMTP", weight="bold", size="2"),
                rx.input(
                    placeholder="smtp.example.com",
                    value=ConfigState.smtp_server,
                    on_change=ConfigState.set_smtp_server,
                ),
                spacing="1",
                flex="1",
            ),
            rx.vstack(
                rx.text("Port", weight="bold", size="2"),
                rx.input(
                    type="number",
                    value=ConfigState.smtp_port,
                    on_change=ConfigState.set_smtp_port,
                    width="150px",
                ),
                spacing="1",
            ),
            spacing="3",
            width="100%",
        ),

        # Credentials
        rx.heading("Identifiants", size="5"),
        rx.vstack(
            rx.text("Email expéditeur", weight="bold", size="2"),
            rx.input(
                placeholder="paie@entreprise.com",
                value=ConfigState.sender_email,
                on_change=ConfigState.set_sender_email,
            ),
            spacing="1",
        ),
        rx.vstack(
            rx.text("Mot de passe / App Password", weight="bold", size="2"),
            rx.input(
                type="password",
                placeholder="••••••••",
                value=ConfigState.sender_password,
                on_change=ConfigState.set_sender_password,
            ),
            spacing="1",
        ),
        rx.vstack(
            rx.text("Nom d'affichage", weight="bold", size="2"),
            rx.input(
                placeholder="Service Paie",
                value=ConfigState.sender_name,
                on_change=ConfigState.set_sender_name,
            ),
            spacing="1",
        ),

        rx.divider(),

        # Security options
        rx.heading("Options de sécurité", size="5"),
        rx.hstack(
            rx.hstack(
                rx.switch(
                    checked=ConfigState.use_tls,
                    on_change=ConfigState.set_use_tls,
                ),
                rx.text("TLS (StartTLS)", weight="bold"),
                spacing="2",
            ),
            rx.hstack(
                rx.switch(
                    checked=ConfigState.use_ssl,
                    on_change=ConfigState.set_use_ssl,
                ),
                rx.text("SSL", weight="bold"),
                spacing="2",
            ),
            spacing="5",
        ),

        rx.divider(),

        # Optional fields
        rx.heading("Options avancées (optionnel)", size="5"),
        rx.vstack(
            rx.text("Adresse de réponse", weight="bold", size="2"),
            rx.input(
                placeholder="comptabilite@entreprise.com",
                value=ConfigState.reply_to,
                on_change=ConfigState.set_reply_to,
            ),
            spacing="1",
        ),
        rx.vstack(
            rx.text("BCC pour archivage", weight="bold", size="2"),
            rx.input(
                placeholder="archive@entreprise.com",
                value=ConfigState.bcc_archive,
                on_change=ConfigState.set_bcc_archive,
            ),
            spacing="1",
        ),

        rx.divider(),

        # Action buttons
        rx.hstack(
            rx.button(
                "Enregistrer la configuration",
                on_click=ConfigState.save_email_config,
                size="3",
                color_scheme="blue",
            ),
            rx.button(
                "Tester la connexion",
                on_click=ConfigState.test_email_connection,
                size="3",
                variant="outline",
            ),
            spacing="3",
        ),

        # Test result
        rx.cond(
            ConfigState.email_test_result != "",
            rx.cond(
                ConfigState.email_test_result.to_string().contains("réussie"),
                rx.callout(
                    ConfigState.email_test_result,
                    icon="circle-check",
                    color_scheme="green",
                ),
                rx.callout(
                    ConfigState.email_test_result,
                    icon="circle-alert",
                    color_scheme="red",
                ),
            ),
            rx.fragment(),
        ),

        spacing="4",
        width="100%",
    )


def audit_tab_content() -> rx.Component:
    """Audit log and time tracking tab content."""
    return rx.vstack(
        rx.heading("Suivi du temps", size="6"),
        rx.text("Temps passé par utilisateur et société", size="2", color="#6c757d"),

        # Filters
        rx.hstack(
            rx.vstack(
                rx.text("Filtrer par société", weight="bold", size="2"),
                rx.select(
                    ConfigState.company_filter_options,
                    value=ConfigState.audit_filter_company,
                    on_change=ConfigState.set_audit_filter_company,
                    placeholder="Toutes",
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Filtrer par utilisateur", weight="bold", size="2"),
                rx.input(
                    value=ConfigState.audit_filter_user,
                    on_change=ConfigState.set_audit_filter_user,
                    placeholder="Tous",
                ),
                spacing="1",
            ),
            rx.button("Actualiser", on_click=ConfigState.load_time_tracking, size="2"),
            spacing="3",
        ),

        rx.divider(),

        # Time tracking summary
        rx.heading("Résumé du temps", size="5"),
        rx.cond(
            ConfigState.time_tracking_data.length() > 0,
            rx.data_table(
                data=ConfigState.time_tracking_data,
                columns=["user", "company", "total_hours", "session_count", "avg_minutes_per_session"],
            ),
            rx.text("Aucune donnée. Cliquez sur 'Actualiser' pour charger.", color="#6c757d", size="2"),
        ),

        rx.divider(),

        # Modifications log
        rx.heading("Journal des modifications", size="5"),
        rx.button("Charger les modifications", on_click=ConfigState.load_modifications, size="2"),
        rx.cond(
            ConfigState.modifications_data.length() > 0,
            rx.data_table(
                data=ConfigState.modifications_data,
                columns=["timestamp", "user", "company", "period", "matricule", "field", "old_value", "new_value"],
            ),
            rx.text("Aucune modification. Cliquez sur 'Charger les modifications'.", color="#6c757d", size="2"),
        ),

        spacing="4",
        width="100%",
    )


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
                                rx.tabs.trigger("Email", value="email"),
                                rx.tabs.trigger("Stockage PDF", value="storage"),
                                rx.tabs.trigger("Audit & Temps", value="audit"),
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
                                email_tab_content(),
                                value="email",
                            ),

                            rx.tabs.content(
                                storage_tab_content(),
                                value="storage",
                            ),

                            rx.tabs.content(
                                audit_tab_content(),
                                value="audit",
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
