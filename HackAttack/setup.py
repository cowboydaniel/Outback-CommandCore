from setuptools import setup, find_packages

from HackAttack.app.config import (
    APP_AUTHOR,
    APP_AUTHOR_EMAIL,
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
    PROJECT_URLS,
)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hack-attack",
    version=APP_VERSION,
    author=APP_AUTHOR,
    author_email=APP_AUTHOR_EMAIL,
    description=APP_DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hack-attack/security-platform",
    project_urls=PROJECT_URLS,
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # Dependencies will be installed from requirements.txt
    ],
    entry_points={
        "console_scripts": [
            "hack-attack=HackAttack.app.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: Security",
        "Topic :: Security :: Cryptography",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Networking",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: System :: Hardware",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "Topic :: System :: Hardware :: Universal Serial Bus (USB)",
        "Topic :: System :: Operating System Kernels",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Testing :: Traffic Generation",
        "Topic :: Security :: Cryptography",
        "Topic :: Security :: Systems Administration",
    ],
    keywords=(
        "security testing ethical-hacking penetration-testing "
        "network-security web-security forensics incident-response "
        "vulnerability-assessment hardware-security embedded-systems "
        "firmware-analysis iot-security mobile-security reverse-engineering"
    ),
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
)
