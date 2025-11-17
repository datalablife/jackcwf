#!/usr/bin/env python3
"""
Git Security Audit Script

Scans git history for accidentally committed sensitive information:
- Database credentials
- API keys
- Passwords
- Private keys
- Encryption keys

Usage:
    python scripts/git_security_audit.py            # Scan full history
    python scripts/git_security_audit.py --recent   # Scan last 100 commits
    python scripts/git_security_audit.py --branch main  # Scan specific branch
"""

import os
import subprocess
import sys
import re
from pathlib import Path
from typing import List, Tuple

# Patterns to search for (regex)
SENSITIVE_PATTERNS = {
    "database_url": r"(database[_-]?url|postgresql|mysql|mongodb)(\s*[=:]\s*|://)",
    "password": r"(password|passwd|pwd|secret)(\s*[=:]\s*)['\"]?([a-zA-Z0-9@!#$%^&*._-]+)['\"]?",
    "api_key": r"(api[_-]?key|apikey|api_secret|access[_-]?token)(\s*[=:]\s*)['\"]?([a-zA-Z0-9]+)['\"]?",
    "private_key": r"(-----BEGIN.*PRIVATE KEY-----|PRIVATE KEY|private[_-]?key)",
    "aws_credential": r"(aws_access_key_id|aws_secret_access_key|AKIA[0-9A-Z]{16})",
    "encryption_key": r"(encryption[_-]?key|encrypt_key|secret[_-]?key)(\s*[=:]\s*)",
    "jwt_token": r"(jwt[_-]?secret|jwt[_-]?key|bearer\s+[a-zA-Z0-9._-]+)",
}

# File patterns to always check
FILE_PATTERNS = [
    "*.env",
    "*.pem",
    "*.key",
    "*credentials*",
    "*secrets*",
]


class GitSecurityAuditor:
    """Audits git repository for security issues."""

    def __init__(self, recent_only: bool = False, branch: str = None):
        """
        Initialize auditor.

        Args:
            recent_only: Only scan last 100 commits
            branch: Specific branch to scan (default: all branches)
        """
        self.recent_only = recent_only
        self.branch = branch
        self.findings: List[Tuple[str, str, str]] = []  # (commit, file, pattern)

    def scan(self) -> bool:
        """
        Scan git history for sensitive information.

        Returns:
            True if no sensitive information found, False otherwise
        """
        print("=" * 70)
        print("Git Security Audit")
        print("=" * 70)

        self._scan_for_secrets()
        self._scan_for_sensitive_files()

        return self._report_results()

    def _scan_for_secrets(self) -> None:
        """Scan commit history for secret patterns."""
        print("\nScanning for sensitive data patterns...")

        try:
            # Build git command
            cmd = ["git", "log", "-p", "--all"]

            if self.recent_only:
                cmd.extend(["-100"])  # Last 100 commits
            elif self.branch:
                cmd = ["git", "log", "-p", self.branch]

            # Run git log with grep
            for pattern_name, pattern in SENSITIVE_PATTERNS.items():
                try:
                    result = subprocess.run(
                        cmd + ["-S", pattern, "--oneline"],
                        capture_output=True,
                        text=True,
                        cwd=Path.cwd(),
                    )

                    if result.stdout and result.returncode == 0:
                        for line in result.stdout.split("\n"):
                            if line.strip():
                                self.findings.append(
                                    (line, "history", pattern_name)
                                )
                except Exception as e:
                    print(f"  Warning: Could not scan for {pattern_name}: {e}")

        except Exception as e:
            print(f"Error during secret scan: {e}")

    def _scan_for_sensitive_files(self) -> None:
        """Scan git history for sensitive file patterns."""
        print("Scanning for sensitive files in history...")

        try:
            # Get list of all files ever tracked
            result = subprocess.run(
                ["git", "log", "--all", "--pretty=format:%H", "--name-only"],
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
            )

            if result.returncode == 0:
                files = set(result.stdout.split("\n"))

                for file_pattern in FILE_PATTERNS:
                    for file_path in files:
                        if file_path and self._matches_pattern(
                            file_path, file_pattern
                        ):
                            self.findings.append(
                                ("git history", file_path, "sensitive file")
                            )

        except Exception as e:
            print(f"Error during file scan: {e}")

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if file path matches a pattern."""
        import fnmatch

        return fnmatch.fnmatch(path.lower(), pattern.lower())

    def _report_results(self) -> bool:
        """Report audit results."""
        if not self.findings:
            print("\n" + "=" * 70)
            print("✅ Audit Complete - No Sensitive Data Found")
            print("=" * 70)
            print("\nNo suspicious patterns detected in git history.")
            print("Your repository appears to be clean.")
            return True

        print("\n" + "=" * 70)
        print("⚠️  SECURITY FINDINGS")
        print("=" * 70)

        for commit, location, pattern_type in self.findings:
            print(f"\n  Commit:  {commit}")
            print(f"  Pattern: {pattern_type}")
            print(f"  Location: {location}")

        print("\n" + "=" * 70)
        print("REMEDIATION STEPS:")
        print("=" * 70)
        print("\n1. Review the findings above")
        print("2. If false positives, update SENSITIVE_PATTERNS in this script")
        print("3. If real findings:")
        print("   a) Immediately revoke/rotate the credentials")
        print("   b) Use git-filter-branch or BFG to remove from history")
        print("   c) Force-push to remote (if safe)")
        print("4. Verify findings are removed from all branches")
        print()

        return False


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Audit git repository for security issues"
    )
    parser.add_argument(
        "--recent",
        action="store_true",
        help="Only scan last 100 commits (faster)",
    )
    parser.add_argument(
        "--branch",
        help="Specific branch to scan",
    )

    args = parser.parse_args()

    auditor = GitSecurityAuditor(
        recent_only=args.recent,
        branch=args.branch,
    )

    if auditor.scan():
        print("✅ Security audit passed!\n")
        return 0
    else:
        print("❌ Security issues found. See details above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
