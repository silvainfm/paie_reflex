"""Authentication page"""

import reflex as rx
from ..state import AuthState


def login() -> rx.Component:
    """Login page"""
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Monaco Payroll", size="8", margin_bottom="2rem"),
                rx.form(
                    rx.vstack(
                        rx.input(
                            placeholder="Username",
                            name="username",
                            on_change=AuthState.set_username,
                            size="3",
                        ),
                        rx.input(
                            placeholder="Password",
                            type="password",
                            name="password",
                            on_change=AuthState.set_password,
                            size="3",
                        ),
                        rx.button(
                            "Login",
                            type="submit",
                            size="3",
                            width="100%",
                        ),
                        rx.cond(
                            AuthState.error_message != "",
                            rx.text(
                                AuthState.error_message,
                                color="red",
                                size="2",
                            ),
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    on_submit=AuthState.login,
                    width="100%",
                ),
                width="400px",
            ),
            size="4",
        ),
        height="100vh",
        bg="#f9fafb",
    )
