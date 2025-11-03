from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hack-attack",
    version="0.1.0",
    author="Hack Attack Team",
    author_email="security@hackattack.example",
    description="Enterprise-Grade Security Testing and Ethical Hacking Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hack-attack/security-platform",
    project_urls={
        "Bug Tracker": "https://github.com/hack-attack/security-platform/issues",
        "Documentation": "https://hack-attack.readthedocs.io/",
        "Source Code": "https://github.com/hack-attack/security-platform",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        # Dependencies will be installed from requirements.txt
    ],
    entry_points={
        "console_scripts": [
            "hack-attack=hack_attack.main:main",
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
