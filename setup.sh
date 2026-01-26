#!/bin/bash
# Quick setup script for Monaco Payroll Reflex app

set -e

echo "🚀 Setting up Monaco Payroll - Reflex Edition"

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$python_version < 3.11" | bc -l) )); then
    echo "❌ Python 3.11+ required (found $python_version)"
    exit 1
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p data/{config,db,consolidated,uploads,exports}

# Check for services directory
if [ ! -d "services" ]; then
    echo "⚠️  services/ directory not found"
    echo "Please copy from original Streamlit app:"
    echo "  cp -r /path/to/streamlit-app/services ./"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create company config if not exists
if [ ! -f "data/config/company_info.json" ]; then
    echo "📝 Creating default company config..."
    cat > data/config/company_info.json << EOF
{
  "name": "Demo Company",
  "siret": "12345678901234",
  "address": "Monaco",
  "phone": "+377...",
  "email": "demo@company.mc",
  "employer_number_monaco": "12345"
}
EOF
fi

# Initialize Reflex
echo "🔧 Initializing Reflex..."
reflex init

# Create default admin user
echo "👤 Creating default admin user (username: admin, password: changeme)..."
python3 << EOF
from services.auth import AuthManager
try:
    AuthManager.add_or_update_user("admin", "changeme", "admin", "Admin User")
    print("✅ Admin user created")
except Exception as e:
    print(f"⚠️  {e}")
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the app:"
echo "  reflex run"
echo ""
echo "Default login:"
echo "  Username: admin"
echo "  Password: changeme"
echo ""
echo "Access at: http://localhost:3000"
