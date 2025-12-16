"""Monaco Payroll Management System - Reflex Version"""

import reflex as rx
from .pages import home, import_page, processing, validation, dashboard, pdf_generation, export, config
from .state import GlobalState
from pathlib import Path
import sys

# Import DataManager for database initialization
from .services.data_mgt import DataManager

# Initialize DuckDB database on startup
try:
    DataManager.init_database()
    print("✓ DuckDB database initialized at data/payroll.duckdb")
except Exception as e:
    print(f"Warning: Could not initialize database: {e}")

# App configuration
app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="blue",
    ),
)

# Public routes
app.add_page(home.login, route="/", title="Login")

# Protected routes - require authentication
app.add_page(import_page.index, route="/import", title="Import", on_load=GlobalState.check_auth)
app.add_page(processing.index, route="/processing", title="Traitement", on_load=GlobalState.check_auth)
app.add_page(validation.index, route="/validation", title="Validation", on_load=GlobalState.check_auth)
app.add_page(dashboard.index, route="/dashboard", title="Tableau", on_load=GlobalState.check_auth)
app.add_page(pdf_generation.index, route="/pdf", title="PDFs", on_load=GlobalState.check_auth)
app.add_page(export.index, route="/export", title="Export", on_load=GlobalState.check_auth)
app.add_page(config.index, route="/config", title="Config", on_load=GlobalState.check_auth)
