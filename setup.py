from setuptools import setup, find_packages
import os

print("Current directory:", os.getcwd())
print("Contents of src:", os.listdir("src"))
packages = find_packages(where="src")
print("Found packages:", packages)

setup(
    name="ignition-lint",
    version="0.1.0",
    packages=packages,
    package_dir={"": "src"},
    install_requires=[],
    entry_points={
        "console_scripts": [
            "ignition-lint = ignition_lint:main",
        ],
    },
    author="Eric Knorr",
    description="A linter for Ignition JSON files",
    license="MIT",
    url="https://github.com/design-group/ignition-lint",
)
