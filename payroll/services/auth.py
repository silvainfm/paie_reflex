"""Authentication state and utilities."""
import reflex as rx
from typing import Optional
import sys
from pathlib import Path

# Import auth service
sys.path.insert(0, str(Path(__file__).parent.parent))
from .services.auth import AuthManager


class AuthState(rx.State):
    """Authentication state."""
    
    username: str = ""
    is_authenticated: bool = False
    role: str = ""
    name: str = ""
    login_error: str = ""
    
    def check_login(self):
        """Check if user is logged in, redirect if not."""
        if not self.is_authenticated:
            return rx.redirect("/login")
    
    def login(self, form_data: dict):
        """Handle login."""
        username = form_data.get("username", "")
        password = form_data.get("password", "")
        
        if AuthManager.verify_login(username, password):
            user = AuthManager.get_user(username)
            self.username = username
            self.is_authenticated = True
            self.role = user.get("role", "comptable")
            self.name = user.get("name", username)
            self.login_error = ""
            return rx.redirect("/")
        else:
            self.login_error = "Invalid credentials"
    
    def logout(self):
        """Handle logout."""
        self.username = ""
        self.is_authenticated = False
        self.role = ""
        self.name = ""
        return rx.redirect("/login")
    
    @rx.var
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == "admin"


def require_login(state_class):
    """Decorator to require login for a page."""
    return state_class
