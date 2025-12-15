"""Home and login pages."""
import reflex as rx
from ..state import GlobalState
from ..components import navbar, sidebar_nav


def login() -> rx.Component:
    """Login page."""
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Monaco Payroll", size="8", weight="bold"),
                rx.text("Sign in to continue", size="3", color="#6c757d"),
                
                rx.form(
                    rx.vstack(
                        rx.input(
                            placeholder="Username",
                            name="username",
                            required=True,
                        ),
                        rx.input(
                            placeholder="Password",
                            name="password",
                            type="password",
                            required=True,
                        ),
                        rx.button(
                            "Sign In",
                            type="submit",
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    on_submit=GlobalState.login,
                    width="100%",
                ),
                
                rx.cond(
                    GlobalState.login_error,
                    rx.callout(
                        GlobalState.login_error,
                        icon="alert-circle",
                        color_scheme="red",
                    ),
                    rx.fragment(),
                ),
                
                spacing="5",
                width="100%",
            ),
            size="4",
            max_width="400px",
        ),
        height="100vh",
        bg="#f8f9fa",
    )


def index() -> rx.Component:
    """Home page."""
    return rx.fragment(
        navbar(),
        rx.hstack(
            sidebar_nav(),
            rx.box(
                rx.vstack(
                    rx.heading("Monaco Payroll System", size="8"),
                    rx.text(
                        "Modern payroll processing for Monaco businesses",
                        size="4",
                        color="#6c757d",
                    ),
                    
                    rx.divider(),
                    
                    rx.cond(
                        GlobalState.has_selection,
                        rx.vstack(
                            rx.heading("Current Selection", size="6"),
                            rx.grid(
                                rx.box(
                                    rx.vstack(
                                        rx.text("Company", size="2", color="#6c757d"),
                                        rx.text(GlobalState.current_company, size="5", weight="bold"),
                                        spacing="2",
                                    ),
                                    bg="white",
                                    padding="1.5rem",
                                    border_radius="8px",
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.text("Period", size="2", color="#6c757d"),
                                        rx.text(GlobalState.current_period, size="5", weight="bold"),
                                        spacing="2",
                                    ),
                                    bg="white",
                                    padding="1.5rem",
                                    border_radius="8px",
                                ),
                                columns="2",
                                spacing="4",
                            ),
                            spacing="4",
                        ),
                        rx.callout(
                            "Please select a company and period to continue",
                            icon="info",
                            color_scheme="blue",
                        ),
                    ),
                    
                    rx.divider(),
                    
                    rx.heading("Quick Actions", size="6"),
                    rx.grid(
                        rx.link(
                            rx.card(
                                rx.vstack(
                                    rx.icon("upload", size=32),
                                    rx.heading("Import Data", size="4"),
                                    rx.text("Upload Excel/CSV files", size="2"),
                                    spacing="3",
                                ),
                            ),
                            href="/import",
                        ),
                        rx.link(
                            rx.card(
                                rx.vstack(
                                    rx.icon("settings", size=32),
                                    rx.heading("Process Payroll", size="4"),
                                    rx.text("Calculate salaries", size="2"),
                                    spacing="3",
                                ),
                            ),
                            href="/processing",
                        ),
                        rx.link(
                            rx.card(
                                rx.vstack(
                                    rx.icon("bar-chart-2", size=32),
                                    rx.heading("Dashboard", size="4"),
                                    rx.text("View reports", size="2"),
                                    spacing="3",
                                ),
                            ),
                            href="/dashboard",
                        ),
                        columns="3",
                        spacing="4",
                    ),
                    
                    spacing="5",
                    padding="2rem",
                    width="100%",
                ),
                flex="1",
            ),
            spacing="0",
            width="100%",
            align_items="start",
        ),
        on_mount=GlobalState.load_companies,
    )
