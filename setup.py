import os
import shutil
import subprocess
from pathlib import Path
from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


REPO_ROOT = Path(__file__).parent
DESKTOP_SRC = REPO_ROOT / "CommandCore" / "commandcore-launcher.desktop"
ICON_SRC = REPO_ROOT / "icons" / "commandcore.png"

APPS_DIR = Path.home() / ".local" / "share" / "applications"
ICON_DIR = Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps"


def install_desktop_entry():
    APPS_DIR.mkdir(parents=True, exist_ok=True)
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DESKTOP_SRC, APPS_DIR / "commandcore-launcher.desktop")
    shutil.copy2(ICON_SRC, ICON_DIR / "commandcore.png")
    try:
        subprocess.run(["update-desktop-database", str(APPS_DIR)], check=False)
        subprocess.run(["gtk-update-icon-cache", "-f", "-t",
                        str(Path.home() / ".local" / "share" / "icons" / "hicolor")],
                       check=False)
    except FileNotFoundError:
        pass
    print(f"Installed desktop entry to {APPS_DIR}")


class DevelopWithDesktop(develop):
    def run(self):
        super().run()
        install_desktop_entry()


class InstallWithDesktop(install):
    def run(self):
        super().run()
        install_desktop_entry()


setup(
    cmdclass={
        "develop": DevelopWithDesktop,
        "install": InstallWithDesktop,
    }
)
