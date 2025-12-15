"""Monaco Payroll Management System - Reflex Version"""

import reflex as rx
from .pages import (
    auth_page,
    import_page,
    processing_page,
    validation_page,
    dashboard_page,
    pdf_page,
    export_page,
    config_page,
)
from .state import AuthState

# App configuration
app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="blue",
    ),
)

# Public routes
app.add_page(auth_page.login, route="/", title="Login")

# Protected routes - require authentication
app.add_page(import_page.page, route="/import", title="Import", on_load=AuthState.check_auth)
app.add_page(processing_page.page, route="/processing", title="Traitement", on_load=AuthState.check_auth)
app.add_page(validation_page.page, route="/validation", title="Validation", on_load=AuthState.check_auth)
app.add_page(dashboard_page.page, route="/dashboard", title="Tableau", on_load=AuthState.check_auth)
app.add_page(pdf_page.page, route="/pdf", title="PDFs", on_load=AuthState.check_auth)
app.add_page(export_page.page, route="/export", title="Export", on_load=AuthState.check_auth)
app.add_page(config_page.page, route="/config", title="Config", on_load=AuthState.check_auth)
