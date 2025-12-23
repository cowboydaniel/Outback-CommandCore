#!/usr/bin/env python3
"""
Dependency Installer for CommandCore

Automatically discovers and installs missing dependencies from all module
requirements.txt files in the Outback-CommandCore project.
"""
import subprocess
import sys
import os
import re
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional
import importlib.metadata


def get_project_root() -> Path:
    """Get the root directory of the Outback-CommandCore project."""
    # Navigate up from CommandCore/app to project root
    return Path(__file__).parent.parent.parent


def discover_requirements_files() -> List[Path]:
    """Discover all requirements.txt files in the project."""
    project_root = get_project_root()
    requirements_files = []

    # Look for requirements.txt in each top-level module directory
    for item in project_root.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            req_file = item / 'requirements.txt'
            if req_file.exists():
                requirements_files.append(req_file)

    return requirements_files


def parse_requirement_line(line: str) -> Optional[Tuple[str, str]]:
    """
    Parse a requirement line and return (package_name, full_requirement).
    Returns None for comments or empty lines.
    """
    line = line.strip()

    # Skip empty lines and comments
    if not line or line.startswith('#'):
        return None

    # Handle inline comments
    if '#' in line:
        line = line.split('#')[0].strip()

    if not line:
        return None

    # Extract package name (before any version specifiers)
    # Handles: package, package>=1.0, package[extra]>=1.0, package==1.0
    match = re.match(r'^([a-zA-Z0-9_-]+)', line.replace('_', '-'))
    if match:
        package_name = match.group(1).lower().replace('_', '-')
        return (package_name, line)

    return None


def gather_all_dependencies() -> Dict[str, str]:
    """
    Gather all unique dependencies from all requirements.txt files.
    Returns a dict mapping package_name -> full_requirement_string
    """
    dependencies = {}
    requirements_files = discover_requirements_files()

    for req_file in requirements_files:
        try:
            with open(req_file, 'r') as f:
                for line in f:
                    parsed = parse_requirement_line(line)
                    if parsed:
                        pkg_name, requirement = parsed
                        # Keep the first occurrence (or could merge version specs)
                        if pkg_name not in dependencies:
                            dependencies[pkg_name] = requirement
        except Exception as e:
            print(f"Warning: Could not read {req_file}: {e}")

    return dependencies


def normalize_package_name(name: str) -> str:
    """Normalize package name for comparison."""
    return name.lower().replace('_', '-').replace('.', '-')


def get_installed_packages() -> Set[str]:
    """Get set of installed package names (normalized)."""
    installed = set()
    try:
        for dist in importlib.metadata.distributions():
            installed.add(normalize_package_name(dist.metadata['Name']))
    except Exception:
        # Fallback: use pip list
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
                capture_output=True,
                text=True
            )
            for line in result.stdout.strip().split('\n'):
                if '==' in line:
                    pkg_name = line.split('==')[0]
                    installed.add(normalize_package_name(pkg_name))
        except Exception:
            pass

    return installed


def find_missing_dependencies(dependencies: Dict[str, str]) -> List[str]:
    """Find which dependencies are not installed."""
    installed = get_installed_packages()
    missing = []

    for pkg_name, requirement in dependencies.items():
        normalized_name = normalize_package_name(pkg_name)
        if normalized_name not in installed:
            missing.append(requirement)

    return missing


def install_dependencies(dependencies: List[str], verbose: bool = True) -> Tuple[bool, List[str]]:
    """
    Install the given dependencies using pip with real-time output.
    Returns (success, list_of_failed_packages)
    """
    if not dependencies:
        return True, []

    failed = []

    # Install packages one by one to show progress and catch individual failures
    total = len(dependencies)
    for i, dep in enumerate(dependencies, 1):
        if verbose:
            print(f"\n[{i}/{total}] Installing {dep}...")
            sys.stdout.flush()

        try:
            cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade', dep]

            # Stream output directly to terminal
            result = subprocess.run(
                cmd,
                stdout=sys.stdout if verbose else subprocess.DEVNULL,
                stderr=sys.stderr if verbose else subprocess.DEVNULL,
            )

            if result.returncode != 0:
                if verbose:
                    print(f"  ✗ Failed to install {dep}")
                failed.append(dep)
            else:
                if verbose:
                    print(f"  ✓ Installed {dep}")

        except Exception as e:
            if verbose:
                print(f"  ✗ Error installing {dep}: {e}", file=sys.stderr)
            failed.append(dep)

    return len(failed) == 0, failed


def check_and_install_dependencies(verbose: bool = True) -> bool:
    """
    Main function to check and install all missing dependencies.
    Returns True if all dependencies are satisfied.
    """
    if verbose:
        print("=" * 60)
        print("CommandCore Dependency Checker")
        print("=" * 60)

    # Discover requirements files
    requirements_files = discover_requirements_files()
    if verbose:
        print(f"\nDiscovered {len(requirements_files)} requirements.txt files:")
        for rf in requirements_files:
            print(f"  - {rf.parent.name}/requirements.txt")

    # Gather all dependencies
    if verbose:
        print("\nGathering dependencies...")
    dependencies = gather_all_dependencies()
    if verbose:
        print(f"Found {len(dependencies)} unique dependencies")

    # Find missing dependencies
    if verbose:
        print("\nChecking installed packages...")
    missing = find_missing_dependencies(dependencies)

    if not missing:
        if verbose:
            print("\n✓ All dependencies are already installed!")
            print("=" * 60)
        return True

    if verbose:
        print(f"\nFound {len(missing)} missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")

    # Install missing dependencies
    if verbose:
        print("\nInstalling missing dependencies...")

    success, failed = install_dependencies(missing, verbose=verbose)

    if success:
        if verbose:
            print("\n✓ All dependencies installed successfully!")
            print("=" * 60)
        return True
    else:
        if verbose:
            print(f"\n✗ Failed to install {len(failed)} dependencies:")
            for dep in failed:
                print(f"  - {dep}")
            print("\nYou may need to install these manually.")
            print("Some packages may require system-level dependencies.")
            print("\nSee CommandCore/requirements-optional.txt for installation")
            print("instructions for packages with special requirements.")
            print("=" * 60)
        return False


def main():
    """CLI entry point for dependency installer."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Check and install dependencies for CommandCore modules'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress output (only show errors)'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check for missing dependencies, do not install'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all discovered dependencies'
    )

    args = parser.parse_args()

    if args.list:
        dependencies = gather_all_dependencies()
        print("All discovered dependencies:")
        for pkg, req in sorted(dependencies.items()):
            print(f"  {req}")
        return

    if args.check_only:
        dependencies = gather_all_dependencies()
        missing = find_missing_dependencies(dependencies)
        if missing:
            print(f"Missing {len(missing)} dependencies:")
            for dep in missing:
                print(f"  {dep}")
            sys.exit(1)
        else:
            print("All dependencies are installed.")
            sys.exit(0)

    success = check_and_install_dependencies(verbose=not args.quiet)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
