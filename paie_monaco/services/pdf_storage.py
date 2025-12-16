"""
PDF Storage Service - Handles saving PDFs to various destinations
Supports: Local filesystem, SFTP
"""

import json
import paramiko
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, BinaryIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SFTPConfig:
    """SFTP configuration"""
    host: str
    port: int = 22
    username: str = ""
    password: str = ""
    private_key_path: Optional[str] = None
    remote_base_path: str = "/"
    enabled: bool = False
    # Pattern placeholders: {company_id}, {company_name}, {year}, {month}, {type}
    folder_pattern: str = "{company_name}/{year}/{month}"
    # Pattern placeholders: {type}, {matricule}, {nom}, {prenom}, {year}, {month}, {timestamp}
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


class PDFStorageService:
    """Service to handle PDF storage to various destinations"""

    def __init__(self, sftp_config: Optional[SFTPConfig] = None):
        self.sftp_config = sftp_config

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

        except Exception as e:
            logger.error(f"Failed to upload PDF to SFTP: {e}")
            return False

    def _create_remote_dirs(self, sftp: paramiko.SFTPClient, remote_path: str):
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
        """Build remote path from patterns"""

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
