"""Reflex configuration"""

import reflex as rx

config = rx.Config(
    app_name="paie_reflex",  # cspell: disable-line
    # Note: Payroll data uses DuckDB (data/payroll.duckdb)
    # This db_url is for Reflex internal state only (optional)
    db_url="sqlite:///reflex_state.db",
    env=rx.Env.DEV,
    # Performance optimizations
    backend_port=8000,
    frontend_port=3000,
    # Increase timeout for large file uploads (Excel, PDFs)
    timeout=600,
    # Disable telemetry in development
    telemetry_enabled=False,
    # Disable sitemap plugin (not needed for internal app)
    disable_plugins=['reflex.plugins.sitemap.SitemapPlugin'],
)
