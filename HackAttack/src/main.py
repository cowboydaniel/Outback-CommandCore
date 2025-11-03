"""
Hack Attack - Main Entry Point

This is the main entry point for the Hack Attack security testing platform.
"""
import argparse
import sys
from typing import List, Optional

from . import __version__
from .config import config
from .logger import get_logger

logger = get_logger(__name__)

class HackAttack:
    """Main application class for Hack Attack."""
    
    def __init__(self):
        """Initialize the Hack Attack application."""
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing Hack Attack")
    
    def run(self, args: List[str]) -> int:
        """Run the application with the given command line arguments."""
        try:
            self._parse_args(args)
            self.logger.info("Hack Attack started")
            # Main application logic will go here
            return 0
        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}", exc_info=True)
            return 1
    
    def _parse_args(self, args: List[str]) -> None:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description="Hack Attack - Enterprise Security Testing Platform"
        )
        
        parser.add_argument(
            "-v", "--version",
            action="version",
            version=f"%(prog)s {__version__}"
        )
        
        parser.add_argument(
            "target",
            nargs="?",
            help="Target to scan (IP, hostname, or URL)"
        )
        
        # Add subparsers for different modes
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Scan command
        scan_parser = subparsers.add_parser("scan", help="Run a security scan")
        scan_parser.add_argument(
            "-p", "--ports",
            default="1-1024",
            help="Ports to scan (e.g., 80,443 or 1-1000)"
        )
        
        # Report command
        report_parser = subparsers.add_parser("report", help="Generate reports")
        report_parser.add_argument(
            "-f", "--format",
            choices=["html", "pdf", "json"],
            default="html",
            help="Output format for the report"
        )
        
        # Parse the arguments
        self.args = parser.parse_args(args)

def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the Hack Attack CLI."""
    if args is None:
        args = sys.argv[1:]
    
    app = HackAttack()
    return app.run(args)

if __name__ == "__main__":
    sys.exit(main())
