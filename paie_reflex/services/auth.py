"""Authentication state and utilities."""
import reflex as rx
import sys
from pathlib import Path
import hashlib
import json
from typing import Optional, Dict, List
from datetime import datetime

# Import auth service
sys.path.insert(0, str(Path(__file__).parent.parent))

class AuthManager:
    """User authentication and management."""
    
    USERS_FILE = Path("data/config/users.json")
    
    @classmethod
    def _ensure_config_dir(cls):
        """Ensure config directory exists."""
        cls.USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not cls.USERS_FILE.exists():
            # Create default admin user
            default_users = {
                "admin": {
                    "username": "admin",
                    "password_hash": cls._hash_password("admin"),
                    "role": "admin",
                    "name": "Administrator",
                    "created_at": datetime.now().isoformat()
                }
            }
            with open(cls.USERS_FILE, 'w') as f:
                json.dump(default_users, f, indent=2)
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @classmethod
    def verify_login(cls, username: str, password: str) -> bool:
        """Verify login credentials."""
        cls._ensure_config_dir()
        
        try:
            with open(cls.USERS_FILE, 'r') as f:
                users = json.load(f)
            
            if username not in users:
                return False
            
            user = users[username]
            password_hash = cls._hash_password(password)
            
            return user.get("password_hash") == password_hash
        except:
            return False
    
    @classmethod
    def get_user(cls, username: str) -> Optional[Dict]:
        """Get user data."""
        cls._ensure_config_dir()
        
        try:
            with open(cls.USERS_FILE, 'r') as f:
                users = json.load(f)
            return users.get(username)
        except:
            return None
    
    @classmethod
    def list_users(cls) -> List[Dict]:
        """List all users."""
        cls._ensure_config_dir()
        
        try:
            with open(cls.USERS_FILE, 'r') as f:
                users = json.load(f)
            return list(users.values())
        except:
            return []
    
    @classmethod
    def add_or_update_user(cls, username: str, password: str, role: str = "comptable", name: str = ""):
        """Add or update user."""
        cls._ensure_config_dir()
        
        try:
            with open(cls.USERS_FILE, 'r') as f:
                users = json.load(f)
        except:
            users = {}
        
        users[username] = {
            "username": username,
            "password_hash": cls._hash_password(password),
            "role": role,
            "name": name or username,
            "created_at": datetime.now().isoformat()
        }
        
        with open(cls.USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    
    @classmethod
    def remove_users(cls, usernames: List[str]):
        """Remove users."""
        cls._ensure_config_dir()
        
        try:
            with open(cls.USERS_FILE, 'r') as f:
                users = json.load(f)
            
            for username in usernames:
                users.pop(username, None)
            
            with open(cls.USERS_FILE, 'w') as f:
                json.dump(users, f, indent=2)
        except:
            pass
    
    @classmethod
    def is_admin(cls, username: str) -> bool:
        """Check if user is admin."""
        user = cls.get_user(username)
        return user and user.get("role") == "admin"
    
    @classmethod
    def get_stats(cls) -> Dict:
        """Get user statistics."""
        users = cls.list_users()
        return {
            "total_users": len(users),
            "admin_users": sum(1 for u in users if u.get("role") == "admin"),
            "comptable_users": sum(1 for u in users if u.get("role") == "comptable"),
        }
    
    @classmethod
    def is_new_company(cls, company_id: str) -> bool:
        """Check if company is new (< 6 months)."""
        # Stub for MVP
        return False
    
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
