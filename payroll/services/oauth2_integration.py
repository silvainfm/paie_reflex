"""
OAuth2 Integration Module for Monaco Payroll System
====================================================
Provides OAuth2 authentication for Office 365
"""

import os
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Optional, Union, List
from datetime import datetime, timedelta
import pickle

# OAuth2 and email libraries
#import msal
import requests

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)


class OAuth2Config:
    """OAuth2 Configuration Manager"""
    
    MICROSOFT_AUTHORITY = 'https://login.microsoftonline.com/{tenant}'
    MICROSOFT_SCOPES = [
        'https://graph.microsoft.com/Mail.Send',
        'https://graph.microsoft.com/Mail.ReadWrite'
    ]
    
    def __init__(self, config_dir: Path = Path("data/config")):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.microsoft_config_file = self.config_dir / "microsoft_oauth.json"
        self.token_dir = self.config_dir / "tokens"
        self.token_dir.mkdir(parents=True, exist_ok=True)
    
    
    def save_microsoft_config(self, tenant_id: str, client_id: str, 
                            client_secret: str) -> bool:
        """Save Microsoft OAuth2 configuration"""
        try:
            config = {
                "tenant_id": tenant_id,
                "client_id": client_id,
                "client_secret": client_secret,
                "authority": self.MICROSOFT_AUTHORITY.format(tenant=tenant_id)
            }
            
            with open(self.microsoft_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("Microsoft OAuth2 configuration saved")
            return True
            
        except Exception as e:
            logger.error(f"Error saving Microsoft config: {e}")
            return False
    
    def load_microsoft_config(self) -> Optional[Dict]:
        """Load Microsoft OAuth2 configuration"""
        if self.microsoft_config_file.exists():
            with open(self.microsoft_config_file, 'r') as f:
                return json.load(f)
        return None
                    


class MicrosoftOAuth2Service:
    """Microsoft OAuth2 Service for Office 365"""
    
    def __init__(self, config: OAuth2Config):
        self.config = config
        self.app = None
        self.token = None
        self.token_file = config.token_dir / "microsoft_token.json"
    
    def initialize_app(self) -> bool:
        """Initialize MSAL application"""
        try:
            config_data = self.config.load_microsoft_config()
            if not config_data:
                logger.error("Microsoft OAuth2 configuration not found")
                return False
            
            self.app = msal.ConfidentialClientApplication(
                config_data['client_id'],
                authority=config_data['authority'],
                client_credential=config_data['client_secret']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing MSAL app: {e}")
            return False
    
    def get_auth_url(self, state: Optional[str] = None) -> Optional[str]:
        """Get Microsoft OAuth2 authorization URL"""
        try:
            if not self.app:
                if not self.initialize_app():
                    return None
            
            auth_url = self.app.get_authorization_request_url(
                scopes=OAuth2Config.MICROSOFT_SCOPES,
                state=state,
                redirect_uri="http://localhost:8501"
            )
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating Microsoft auth URL: {e}")
            return None
    
    def handle_callback(self, authorization_code: str) -> bool:
        """Handle OAuth2 callback and save tokens"""
        try:
            if not self.app:
                if not self.initialize_app():
                    return False
            
            # Exchange code for token
            result = self.app.acquire_token_by_authorization_code(
                authorization_code,
                scopes=OAuth2Config.MICROSOFT_SCOPES,
                redirect_uri="http://localhost:8501"
            )
            
            if "access_token" in result:
                self.token = result
                
                # Save token to file
                with open(self.token_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                logger.info("Microsoft OAuth2 tokens saved successfully")
                return True
            else:
                logger.error(f"Failed to acquire token: {result.get('error_description')}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling Microsoft OAuth callback: {e}")
            return False
    
    def load_token(self) -> bool:
        """Load saved token"""
        try:
            if self.token_file.exists():
                with open(self.token_file, 'r') as f:
                    self.token = json.load(f)
                
                # Check if token needs refresh
                if self.is_token_expired():
                    return self.refresh_token()
                
                return True
                
        except Exception as e:
            logger.error(f"Error loading Microsoft token: {e}")
        
        return False
    
    def is_token_expired(self) -> bool:
        """Check if token is expired"""
        if not self.token or 'expires_in' not in self.token:
            return True
        
        # Simple expiration check (should track actual expiry time)
        return False
    
    def refresh_token(self) -> bool:
        """Refresh access token"""
        try:
            if not self.app:
                if not self.initialize_app():
                    return False
            
            if not self.token or 'refresh_token' not in self.token:
                return False
            
            result = self.app.acquire_token_by_refresh_token(
                self.token['refresh_token'],
                scopes=OAuth2Config.MICROSOFT_SCOPES
            )
            
            if "access_token" in result:
                self.token = result
                
                # Save refreshed token
                with open(self.token_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                return True
                
        except Exception as e:
            logger.error(f"Error refreshing Microsoft token: {e}")
        
        return False
    
    def send_email(self, to_email: str, subject: str, body_html: str,
                  attachments: Optional[List[tuple]] = None) -> bool:
        """
        Send email via Microsoft Graph API
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body_html: HTML body
            attachments: List of (filename, content_bytes) tuples
        """
        try:
            if not self.token:
                if not self.load_token():
                    logger.error("No valid token available")
                    return False
            
            # Prepare message
            message = {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body_html
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email
                        }
                    }
                ]
            }
            
            # Add attachments
            if attachments:
                message["attachments"] = []
                for filename, content in attachments:
                    attachment = {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": filename,
                        "contentType": "application/octet-stream",
                        "contentBytes": base64.b64encode(content).decode()
                    }
                    message["attachments"].append(attachment)
            
            # Send email
            headers = {
                'Authorization': f'Bearer {self.token["access_token"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                'https://graph.microsoft.com/v1.0/me/sendMail',
                headers=headers,
                json={"message": message}
            )
            
            if response.status_code == 202:
                logger.info("Email sent successfully via Microsoft Graph")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email via Microsoft: {e}")
            return False
    
    def revoke_access(self) -> bool:
        """Revoke OAuth2 access"""
        try:
            # Delete token file
            if self.token_file.exists():
                self.token_file.unlink()
            
            self.token = None
            logger.info("Microsoft OAuth2 access revoked")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking Microsoft access: {e}")
            return False


class OAuth2EmailManager:
    """Unified OAuth2 Email Manager"""
    
    def __init__(self, config_dir: Path = Path("data/config")):
        self.config = OAuth2Config(config_dir)
        self.microsoft_service = MicrosoftOAuth2Service(self.config)
        self.active_service = None
    
    def configure_microsoft(self, tenant_id: str, client_id: str, 
                          client_secret: str) -> bool:
        """Configure Microsoft OAuth2"""
        return self.config.save_microsoft_config(tenant_id, client_id, client_secret)
    
    def get_auth_url(self, provider: str) -> Optional[str]:
        """Get authorization URL for provider"""
        if provider == 'microsoft':
            return self.microsoft_service.get_auth_url()
        return None
    
    def handle_callback(self, provider: str, auth_response: str) -> bool:
        """Handle OAuth2 callback"""
        if provider == 'microsoft':
            # Extract code from response
            import urllib.parse
            parsed = urllib.parse.urlparse(auth_response)
            params = urllib.parse.parse_qs(parsed.query)
            code = params.get('code', [None])[0]
            
            if code:
                success = self.microsoft_service.handle_callback(code)
                if success:
                    self.active_service = 'microsoft'
                return success
        return False
    
    def send_email(self, to_email: str, subject: str, body_html: str,
                  attachments: Optional[List[tuple]] = None,
                  provider: Optional[str] = None) -> bool:
        """
        Send email using OAuth2
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body_html: HTML body
            attachments: List of (filename, content_bytes) tuples
            provider: Force specific provider (optional)
        """
        # Use specified provider or active service
        service = provider or self.active_service

        if service == 'microsoft':
            return self.microsoft_service.send_email(to_email, subject, body_html, attachments)
        else:
            logger.error("No active OAuth2 service")
            return False
    
    def check_authentication(self) -> Dict[str, bool]:
        """Check authentication status for each provider"""
        return {
            'microsoft': self.microsoft_service.load_token()
        }
    
    def revoke_access(self, provider: str) -> bool:
        """Revoke OAuth2 access for provider"""
        if provider == 'microsoft':
            return self.microsoft_service.revoke_access()
        return False


def send_paystub_with_oauth2(employee_data: Dict, pdf_buffer: bytes,
                            period: str, provider: str = 'microsoft') -> bool:
    """
    Send paystub using OAuth2 authentication
    
    Args:
        employee_data: Employee data dictionary
        pdf_buffer: PDF content as bytes
        period: Period (YYYY-MM)
        provider: 'microsoft'
    """
    
    oauth_manager = OAuth2EmailManager()
    
    # Prepare email content
    period_date = datetime.strptime(period, "%Y-%m")
    month_year = period_date.strftime("%B %Y")
    
    subject = f"Votre bulletin de paie - {month_year}"
    
    body_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Bulletin de Paie - {month_year}</h2>
            
            <p>Bonjour {employee_data.get('prenom', '')} {employee_data.get('nom', '')},</p>
            
            <p>Veuillez trouver ci-joint votre bulletin de paie pour la période de {month_year}.</p>
            
            <div style="background: #f5f5f5; padding: 15px; margin: 20px 0;">
                <strong>Récapitulatif:</strong><br>
                Salaire brut: {employee_data.get('salaire_brut', 0):,.2f} €<br>
                Salaire net: {employee_data.get('salaire_net', 0):,.2f} €
            </div>
            
            <p>Ce document est à conserver sans limitation de durée.</p>
            
            <p>Cordialement,<br>
            Service Paie</p>
        </body>
    </html>
    """
    
    # Prepare attachment
    filename = f"bulletin_{employee_data.get('matricule', '')}_{period}.pdf"
    attachments = [(filename, pdf_buffer)]
    
    # Send email
    return oauth_manager.send_email(
        employee_data.get('email', ''),
        subject,
        body_html,
        attachments,
        provider
    )


# Test function
def test_oauth2_email():
    """Test OAuth2 email functionality"""
    
    oauth_manager = OAuth2EmailManager()
    
    # Check authentication
    auth_status = oauth_manager.check_authentication()
    print(f"Authentication status: {auth_status}")

    if auth_status['microsoft']:
        # Test email
        test_email = "test@example.com"
        subject = "Test OAuth2 Email"
        body = "<h1>Test</h1><p>This is a test email sent via OAuth2.</p>"
        
        # Use whichever service is authenticated
        provider = 'microsoft'
        
        success = oauth_manager.send_email(
            test_email,
            subject,
            body,
            provider=provider
        )
        
        if success:
            print(f"Test email sent successfully via {provider}")
        else:
            print(f"Failed to send test email via {provider}")
    else:
        print("No OAuth2 service authenticated")


if __name__ == "__main__":
    # Run test
    test_oauth2_email()