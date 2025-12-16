"""
PDF Storage Service - Handles saving PDFs to various destinations
Supports: Local filesystem, SFTP, S3, Azure Blob, Google Cloud Storage
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, BinaryIO, Literal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """Storage configuration - supports local and SFTP"""
    storage_type: Literal["local", "sftp"] = "local"
    enabled: bool = False
    # Pattern placeholders: {company_id}, {company_name}, {year}, {month}, {type}
    folder_pattern: str = "{company_name}/{year}/{month}"
    # Pattern placeholders: {type}, {matricule}, {nom}, {prenom}, {year}, {month}, {timestamp}
    filename_pattern: str = "{type}_{matricule}_{year}_{month}.pdf"

    # Local storage
    local_base_path: str = "data/pdfs"

    # SFTP
    sftp_host: str = ""
    sftp_port: int = 22
    sftp_username: str = ""
    sftp_password: str = ""
    sftp_private_key_path: str = ""
    sftp_remote_base_path: str = "/"


@dataclass
class SFTPConfig:
    """SFTP configuration (legacy compatibility)"""
    host: str
    port: int = 22
    username: str = ""
    password: str = ""
    private_key_path: Optional[str] = None
    remote_base_path: str = "/"
    enabled: bool = False
    folder_pattern: str = "{company_name}/{year}/{month}"
    filename_pattern: str = "{type}_{matricule}_{year}_{month}.pdf"


class SFTPConfigManager:
    """Manage SFTP configuration storage"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def save_config(self, config: SFTPConfig) -> bool:
        """Save SFTP config to JSON"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2)
            logger.info(f"SFTP config saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save SFTP config: {e}")
            return False

    def load_config(self) -> Optional[SFTPConfig]:
        """Load SFTP config from JSON"""
        if not self.config_path.exists():
            return None

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SFTPConfig(**data)
        except Exception as e:
            logger.error(f"Failed to load SFTP config: {e}")
            return None


class StorageConfigManager:
    """Manage storage configuration"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def save_config(self, config: StorageConfig) -> bool:
        """Save storage config to JSON"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2)
            logger.info(f"Storage config saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save storage config: {e}")
            return False

    def load_config(self) -> Optional[StorageConfig]:
        """Load storage config from JSON"""
        if not self.config_path.exists():
            return StorageConfig()  # Return default config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return StorageConfig(**data)
        except Exception as e:
            logger.error(f"Failed to load storage config: {e}")
            return StorageConfig()


class PDFStorageService:
    """Service to handle PDF storage to various destinations"""

    def __init__(self, config: Optional[StorageConfig] = None, sftp_config: Optional[SFTPConfig] = None):
        self.config = config or StorageConfig()
        self.sftp_config = sftp_config  # Legacy compatibility

    def save_to_local(self, pdf_buffer: BinaryIO, output_path: Path) -> bool:
        """Save PDF to local filesystem"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                pdf_buffer.seek(0)
                f.write(pdf_buffer.read())

            logger.info(f"PDF saved locally: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save PDF locally: {e}")
            return False

    def save_to_sftp(
        self,
        pdf_buffer: BinaryIO,
        remote_path: str,
        sftp_config: Optional[SFTPConfig] = None
    ) -> bool:
        """Save PDF to SFTP server"""
        config = sftp_config or self.sftp_config

        if not config or not config.enabled:
            logger.warning("SFTP not configured or not enabled")
            return False

        try:
            import paramiko

            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect with password or key
            if config.private_key_path and Path(config.private_key_path).exists():
                key = paramiko.RSAKey.from_private_key_file(config.private_key_path)
                ssh.connect(
                    hostname=config.host,
                    port=config.port,
                    username=config.username,
                    pkey=key
                )
            else:
                ssh.connect(
                    hostname=config.host,
                    port=config.port,
                    username=config.username,
                    password=config.password
                )

            # Open SFTP session
            sftp = ssh.open_sftp()

            # Create remote directories if needed
            remote_dir = str(Path(remote_path).parent)
            self._create_remote_dirs(sftp, remote_dir)

            # Upload file
            pdf_buffer.seek(0)
            sftp.putfo(pdf_buffer, remote_path)

            sftp.close()
            ssh.close()

            logger.info(f"PDF uploaded to SFTP: {remote_path}")
            return True

        except ImportError:
            logger.error("paramiko not installed. Install with: pip install paramiko")
            return False
        except Exception as e:
            logger.error(f"Failed to upload PDF to SFTP: {e}")
            return False

    def save_pdf(
        self,
        pdf_buffer: BinaryIO,
        pdf_type: str,
        company_id: str,
        company_name: str,
        year: int,
        month: int,
        matricule: str = "",
        nom: str = "",
        prenom: str = ""
    ) -> tuple[bool, str]:
        """Save PDF to configured destination"""

        if not self.config.enabled:
            logger.warning("Storage not enabled")
            return False, "Storage not enabled"

        # Build path/key
        path_key = self.build_path(
            pdf_type, company_id, company_name, year, month,
            matricule, nom, prenom
        )

        try:
            if self.config.storage_type == "local":
                output_path = Path(self.config.local_base_path) / path_key
                success = self.save_to_local(pdf_buffer, output_path)
                return success, str(output_path) if success else "Failed to save locally"

            elif self.config.storage_type == "sftp":
                # Build legacy SFTP config
                sftp_cfg = SFTPConfig(
                    host=self.config.sftp_host,
                    port=self.config.sftp_port,
                    username=self.config.sftp_username,
                    password=self.config.sftp_password,
                    private_key_path=self.config.sftp_private_key_path or None,
                    remote_base_path=self.config.sftp_remote_base_path,
                    enabled=True
                )
                remote_path = f"{self.config.sftp_remote_base_path.rstrip('/')}/{path_key}"
                success = self.save_to_sftp(pdf_buffer, remote_path, sftp_cfg)
                return success, remote_path if success else "Failed to upload to SFTP"

            else:
                return False, f"Unknown storage type: {self.config.storage_type}"

        except Exception as e:
            logger.error(f"Failed to save PDF: {e}")
            return False, str(e)

    def _create_remote_dirs(self, sftp, remote_path: str):
        """Recursively create remote directories"""
        if remote_path == '/' or remote_path == '.':
            return

        try:
            sftp.stat(remote_path)
        except FileNotFoundError:
            # Directory doesn't exist, create parent first
            parent = str(Path(remote_path).parent)
            if parent != remote_path:
                self._create_remote_dirs(sftp, parent)

            try:
                sftp.mkdir(remote_path)
            except Exception as e:
                logger.warning(f"Could not create remote dir {remote_path}: {e}")

    def build_path(
        self,
        pdf_type: str,
        company_id: str,
        company_name: str,
        year: int,
        month: int,
        matricule: str = "",
        nom: str = "",
        prenom: str = ""
    ) -> str:
        """Build storage path/key from patterns"""

        # Clean company name for filesystem
        clean_company = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in company_name)

        # Build folder path
        folder = self.config.folder_pattern.format(
            company_id=company_id,
            company_name=clean_company,
            year=year,
            month=f"{month:02d}"
        )

        # Build filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config.filename_pattern.format(
            type=pdf_type,
            matricule=matricule,
            nom=nom,
            prenom=prenom,
            year=year,
            month=f"{month:02d}",
            timestamp=timestamp
        )

        # Combine folder and filename
        full_path = f"{folder}/{filename}"

        # Normalize path separators
        full_path = full_path.replace('//', '/')

        return full_path

    def build_remote_path(
        self,
        config: SFTPConfig,
        pdf_type: str,
        company_id: str,
        company_name: str,
        year: int,
        month: int,
        matricule: str = "",
        nom: str = "",
        prenom: str = ""
    ) -> str:
        """Build remote path from patterns (legacy compatibility)"""

        # Clean company name for filesystem
        clean_company = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in company_name)

        # Build folder path
        folder = config.folder_pattern.format(
            company_id=company_id,
            company_name=clean_company,
            year=year,
            month=f"{month:02d}"
        )

        # Build filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = config.filename_pattern.format(
            type=pdf_type,
            matricule=matricule,
            nom=nom,
            prenom=prenom,
            year=year,
            month=f"{month:02d}",
            timestamp=timestamp
        )

        # Combine base path, folder, and filename
        base = config.remote_base_path.rstrip('/')
        full_path = f"{base}/{folder}/{filename}"

        # Normalize path separators
        full_path = full_path.replace('//', '/')

        return full_path

    def test_sftp_connection(self, config: SFTPConfig) -> tuple[bool, str]:
        """Test SFTP connection and return (success, message)"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if config.private_key_path and Path(config.private_key_path).exists():
                key = paramiko.RSAKey.from_private_key_file(config.private_key_path)
                ssh.connect(
                    hostname=config.host,
                    port=config.port,
                    username=config.username,
                    pkey=key,
                    timeout=10
                )
            else:
                ssh.connect(
                    hostname=config.host,
                    port=config.port,
                    username=config.username,
                    password=config.password,
                    timeout=10
                )

            sftp = ssh.open_sftp()

            # Try to list remote base path
            try:
                sftp.listdir(config.remote_base_path)
            except:
                pass  # Directory might not exist yet

            sftp.close()
            ssh.close()

            return True, "Connexion SFTP réussie"

        except paramiko.AuthenticationException:
            return False, "Échec d'authentification"
        except paramiko.SSHException as e:
            return False, f"Erreur SSH: {str(e)}"
        except Exception as e:
            return False, f"Erreur de connexion: {str(e)}"
