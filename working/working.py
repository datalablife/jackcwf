"""Login page application using Reflex."""

import reflex as rx

# Import health check page
from working.health import health_page


class LoginState(rx.State):
    """The login page state."""

    username: str = ""
    password: str = ""
    is_loading: bool = False
    error_message: str = ""
    is_logged_in: bool = False

    def handle_login(self):
        """Handle login action."""
        # Reset error message
        self.error_message = ""

        # Simple validation
        if not self.username or not self.password:
            self.error_message = "Username and password are required"
            return

        if len(self.password) < 6:
            self.error_message = "Password must be at least 6 characters"
            return

        # Simulate login process
        self.is_loading = True

        # In a real app, you would make an API call here
        # For now, we'll just check if username/password match
        if self.username.lower() == "admin" and self.password == "password":
            self.is_logged_in = True
            self.error_message = ""
        else:
            self.error_message = "Invalid username or password"

        self.is_loading = False

    def handle_logout(self):
        """Handle logout action."""
        self.is_logged_in = False
        self.username = ""
        self.password = ""
        self.error_message = ""

    def update_username(self, value: str):
        """Update username."""
        self.username = value

    def update_password(self, value: str):
        """Update password."""
        self.password = value


def login_form() -> rx.Component:
    """Login form component."""
    return rx.card(
        rx.vstack(
            rx.heading("Login", size="8", text_align="center"),
            rx.text(
                "Welcome back! Please login to your account.",
                size="3",
                color="gray",
                text_align="center",
            ),
            rx.divider(),
            # Username input
            rx.vstack(
                rx.text("Username", size="3", weight="medium"),
                rx.input(
                    placeholder="Enter your username",
                    value=LoginState.username,
                    on_change=LoginState.update_username,
                    size="3",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            # Password input
            rx.vstack(
                rx.text("Password", size="3", weight="medium"),
                rx.input(
                    placeholder="Enter your password",
                    type_="password",
                    value=LoginState.password,
                    on_change=LoginState.update_password,
                    size="3",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            # Error message
            rx.cond(
                LoginState.error_message != "",
                rx.callout(
                    LoginState.error_message,
                    icon="circle_help",
                    color_scheme="red",
                    width="100%",
                ),
            ),
            # Remember me & Forgot password
            rx.hstack(
                rx.checkbox("Remember me"),
                rx.spacer(),
                rx.link("Forgot password?", href="#", size="2", color="blue"),
                width="100%",
                justify="between",
            ),
            # Login button
            rx.button(
                rx.cond(
                    LoginState.is_loading,
                    rx.hstack(
                        rx.spinner(size="1"),
                        rx.text("Logging in..."),
                    ),
                    "Login",
                ),
                on_click=LoginState.handle_login,
                size="3",
                width="100%",
                is_disabled=LoginState.is_loading,
            ),
            # Sign up link
            rx.hstack(
                rx.text("Don't have an account?", size="3"),
                rx.link("Sign up here", href="#", size="3", color="blue"),
                justify="center",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        width="400px",
        max_width="100%",
    )


def login_page() -> rx.Component:
    """Login page component."""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.center(
            login_form(),
            min_height="100vh",
            padding="4",
        ),
    )


def dashboard_page() -> rx.Component:
    """Dashboard page shown after login."""
    return rx.container(
        rx.vstack(
            rx.hstack(
                rx.heading("Dashboard", size="8"),
                rx.spacer(),
                rx.button(
                    "Logout",
                    on_click=LoginState.handle_logout,
                    color_scheme="red",
                ),
                width="100%",
                align="center",
            ),
            rx.divider(),
            rx.card(
                rx.vstack(
                    rx.heading("Welcome!", size="6"),
                    rx.text(f"You are logged in as: {LoginState.username}", size="4"),
                    rx.text(
                        "This is your dashboard. You can add more content here.",
                        size="3",
                        color="gray",
                    ),
                    spacing="4",
                ),
                width="100%",
            ),
            spacing="4",
            padding="4",
        ),
    )


def index() -> rx.Component:
    """Main page that shows either login or dashboard."""
    return rx.cond(
        LoginState.is_logged_in,
        dashboard_page(),
        login_page(),
    )


app = rx.App()
app.add_page(index)

# Register health check page for monitoring
# This is used by Docker HEALTHCHECK and Coolify
app.add_page(health_page)
