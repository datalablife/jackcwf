"""
Port Management Module for Backend Startup
Handles port conflicts intelligently for dev and production environments
"""

import os
import socket
import subprocess
import signal
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PortManager:
    """Manages port availability and cleanup."""

    # Environment detection
    IS_DEVELOPMENT = os.getenv("ENVIRONMENT") != "production"
    AUTO_KILL_TIMEOUT = 5  # seconds

    def __init__(self, port: int = 8000, host: str = "0.0.0.0"):
        """Initialize port manager.

        Args:
            port: Port number to check
            host: Host address
        """
        self.port = port
        self.host = host

    @staticmethod
    def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
        """Check if port is in use.

        Args:
            port: Port number to check
            host: Host to check against

        Returns:
            True if port is in use, False otherwise
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                result = sock.connect_ex((host, port))
                return result == 0
            except Exception:
                return False

    @staticmethod
    def get_process_using_port(port: int) -> Optional[int]:
        """Get PID of process using the port.

        Args:
            port: Port number

        Returns:
            PID if found, None otherwise
        """
        try:
            # Try lsof (Linux/Mac)
            result = subprocess.run(
                f"lsof -i :{port} 2>/dev/null | grep LISTEN | awk '{{print $2}}' | head -1",
                shell=True,
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.stdout.strip():
                try:
                    return int(result.stdout.strip())
                except ValueError:
                    pass

            # Fallback: try netstat
            result = subprocess.run(
                f"netstat -tlnp 2>/dev/null | grep :{port} | awk '{{print $NF}}' | cut -d'/' -f1",
                shell=True,
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.stdout.strip():
                try:
                    return int(result.stdout.strip())
                except ValueError:
                    pass

        except subprocess.TimeoutExpired:
            logger.warning("Timeout while checking for process on port")
        except Exception as e:
            logger.debug(f"Error getting process: {e}")

        return None

    @staticmethod
    def kill_process(pid: int) -> bool:
        """Kill a process by PID.

        Args:
            pid: Process ID to kill

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Attempting to kill process {pid}...")

            # Try SIGTERM first
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)

            # Check if still running
            try:
                os.kill(pid, 0)
                # Still running, force kill
                logger.warning(f"Process {pid} still running, force killing...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
            except ProcessLookupError:
                # Already terminated
                pass

            logger.info(f"✅ Successfully killed process {pid}")
            return True

        except ProcessLookupError:
            logger.debug(f"Process {pid} already terminated")
            return True
        except PermissionError:
            logger.error(f"Permission denied: cannot kill process {pid}")
            return False
        except Exception as e:
            logger.error(f"Error killing process: {e}")
            return False

    def check_and_clean_port(self) -> bool:
        """Check port availability and clean if necessary.

        For development: automatically kill conflicting processes
        For production: raise error

        Returns:
            True if port is available (after cleanup if needed), False otherwise
        """
        if not self.is_port_in_use(self.port):
            logger.info(f"✅ Port {self.port} is available")
            return True

        logger.warning(f"⚠️  Port {self.port} is already in use")

        if self.IS_DEVELOPMENT:
            logger.info("💡 Development environment detected")
            logger.info("Attempting to free up port...")

            pid = self.get_process_using_port(self.port)
            if pid is None:
                logger.warning("Could not determine process ID, port may be stuck")
                return False

            logger.info(f"Process using port: {pid}")

            if self.kill_process(pid):
                time.sleep(2)
                if not self.is_port_in_use(self.port):
                    logger.info(f"✅ Port {self.port} is now available")
                    return True

            logger.error(f"Failed to free port {self.port}")
            return False

        else:
            # Production environment
            logger.error("🚨 Port conflict in PRODUCTION environment!")
            logger.error(f"Port {self.port} is already in use")
            logger.error("")
            logger.error("⚠️  IMPORTANT: Do NOT auto-kill processes in production!")
            logger.error("")
            logger.error("Please:")
            logger.error(f"  1. Find the process: lsof -i :{self.port}")
            logger.error(f"  2. Investigate if it should be running")
            logger.error(f"  3. Kill manually if safe: kill -9 <PID>")
            logger.error(f"  4. Or use a different port: --port 8001")
            logger.error("")

            return False


def ensure_port_available(port: int = 8000, host: str = "0.0.0.0") -> bool:
    """Convenience function to ensure port is available.

    Args:
        port: Port number
        host: Host address

    Returns:
        True if port is available, False otherwise
    """
    manager = PortManager(port=port, host=host)
    return manager.check_and_clean_port()
