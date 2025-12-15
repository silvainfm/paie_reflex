"""Reflex configuration"""

import reflex as rx

config = rx.Config(
    app_name="paie_monaco",
    db_url="sqlite:///reflex.db",
    env=rx.Env.DEV,
)
