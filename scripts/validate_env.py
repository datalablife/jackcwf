#!/usr/bin/env python3
"""
Environment Variable Validation Script

This script validates that all required environment variables are properly set
before running the application. It ensures no sensitive information is exposed
and provides clear error messages when configuration is incomplete.

Usage:
    python scripts/validate_env.py                  # Check all required vars
    python scripts/validate_env.py --strict         # Also check optional vars
    python scripts/validate_env.py --environment=production  # Check prod config
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Define required environment variables by environment
REQUIRED_VARS = {
    "development": {
        "database": [
            "DATABASE_URL",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_USER",
            "POSTGRES_DB",
        ],
        "security": [
            "ENCRYPTION_KEY",
        ],
        "app": [
            "APP_NAME",
            "DEBUG",
            "LOG_LEVEL",
        ],
    },
    "staging": {
        "database": [
            "DATABASE_URL",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_USER",
            "POSTGRES_DB",
        ],
        "security": [
            "ENCRYPTION_KEY",
        ],
        "app": [
            "APP_NAME",
            "DEBUG",
            "LOG_LEVEL",
        ],
    },
    "production": {
        "database": [
            "DATABASE_URL",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_USER",
            "POSTGRES_DB",
        ],
        "security": [
            "ENCRYPTION_KEY",
        ],
        "app": [
            "APP_NAME",
            "LOG_LEVEL",
        ],
    },
}

# Optional variables (warnings if not set)
OPTIONAL_VARS = {
    "development": [
        "SENTRY_DSN",
        "ANALYTICS_ID",
    ],
    "staging": [
        "SENTRY_DSN",
        "ANALYTICS_ID",
    ],
    "production": [
        "SENTRY_DSN",
        "ANALYTICS_ID",
    ],
}

# Variables that should NEVER appear in code (they must come from environment)
SENSITIVE_VARS = {
    "DATABASE_URL",
    "ENCRYPTION_KEY",
    "SECRET_KEY",
    "JWT_SECRET_KEY",
    "API_KEY",
    "PASSWORD",
}

# Patterns to avoid in environment variable values (signs of hardcoded defaults)
SUSPICIOUS_PATTERNS = [
    "localhost",
    "127.0.0.1",
    "example.com",
    "your-",
    "placeholder",
    "changeme",
    "replace",
    "TODO",
]


class EnvironmentValidator:
    """Validates environment configuration."""

    def __init__(self, environment: str = "development", strict: bool = False):
        """
        Initialize validator.

        Args:
            environment: Current environment (development, staging, production)
            strict: If True, also validate optional variables
        """
        self.environment = environment
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """
        Validate all environment variables.

        Returns:
            True if validation passed, False otherwise
        """
        self._validate_required()
        self._validate_optional()
        self._validate_sensitive()

        return self._report_results()

    def _validate_required(self) -> None:
        """Check that all required variables are set."""
        env_vars = REQUIRED_VARS.get(self.environment, {})

        for category, vars_list in env_vars.items():
            for var in vars_list:
                value = os.getenv(var)

                if not value:
                    self.errors.append(
                        f"[REQUIRED] {var} is not set. "
                        f"This is required for {category} configuration.\n"
                        f"         Set it in your .env file: {var}=<value>"
                    )
                else:
                    # Check for suspicious patterns in development
                    if self.environment == "development":
                        for pattern in SUSPICIOUS_PATTERNS:
                            if pattern.lower() in value.lower():
                                self.warnings.append(
                                    f"[WARNING] {var} contains '{pattern}' - "
                                    f"ensure this is not a default/example value"
                                )

    def _validate_optional(self) -> None:
        """Check optional variables (only if strict mode)."""
        if not self.strict:
            return

        optional_vars = OPTIONAL_VARS.get(self.environment, [])

        for var in optional_vars:
            if not os.getenv(var):
                self.warnings.append(
                    f"[OPTIONAL] {var} is not set. "
                    f"This is optional but recommended for better functionality."
                )

    def _validate_sensitive(self) -> None:
        """Validate that sensitive variables are properly configured."""
        for var in SENSITIVE_VARS:
            # Check if variable starts with expected patterns
            value = os.getenv(var)

            if var == "DATABASE_URL" and value:
                # DATABASE_URL should use environment variables or secure sources
                if any(
                    pattern in value
                    for pattern in ["localhost", "127.0.0.1", "example"]
                ):
                    if self.environment == "production":
                        self.errors.append(
                            f"[CRITICAL] {var} appears to use development settings in production!"
                        )
                    else:
                        self.warnings.append(
                            f"[WARNING] {var} appears to use development settings"
                        )

    def _report_results(self) -> bool:
        """Report validation results."""
        # Print errors
        if self.errors:
            print("\n" + "=" * 70)
            print("CONFIGURATION ERRORS (Action Required)")
            print("=" * 70)
            for error in self.errors:
                print(f"\n{error}")

        # Print warnings
        if self.warnings:
            print("\n" + "=" * 70)
            print("CONFIGURATION WARNINGS")
            print("=" * 70)
            for warning in self.warnings:
                print(f"\n{warning}")

        # Print success
        if not self.errors:
            print("\n" + "=" * 70)
            print(f"Environment Configuration Valid ({self.environment})")
            print("=" * 70)
            print("\nAll required environment variables are properly configured.")
            if self.strict and not self.warnings:
                print("All optional variables are also configured.")

            # Show summary of loaded variables (without values)
            print("\nConfigured Variables (by category):")
            env_vars = REQUIRED_VARS.get(self.environment, {})
            for category, vars_list in env_vars.items():
                print(f"\n  {category.upper()}:")
                for var in vars_list:
                    status = "OK" if os.getenv(var) else "MISSING"
                    print(f"    - {var}: {status}")

        return len(self.errors) == 0


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate environment configuration for secure database setup"
    )
    parser.add_argument(
        "--environment",
        choices=["development", "staging", "production"],
        default="development",
        help="Environment to validate for",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also validate optional variables",
    )

    args = parser.parse_args()

    validator = EnvironmentValidator(
        environment=args.environment, strict=args.strict
    )

    if validator.validate():
        print("\n✅ Environment validation passed!\n")
        return 0
    else:
        print(
            "\n❌ Environment validation failed. Please fix the errors above.\n"
        )
        print("For detailed setup instructions, see:")
        print("  docs/SECURE_DATABASE_SETUP.md\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
