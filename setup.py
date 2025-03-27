# setup.py
from setuptools import setup, find_packages

setup(
    name="ignition-lint",
    version="0.1.0",
    packages=find_packages(where="src"),  # Automatically find packages in src/
    package_dir={"": "src"},  # Map the root package to src/
    install_requires=[],
    entry_points={
        "console_scripts": [
            "ignition-lint = ignition_lint.ignition_lint:main",  # Updated to package.module:function
        ],
    },
    author="Eric Knorr",
    description="A linter for Ignition JSON files",
    license="MIT",
    url="https://github.com/design-group/ignition-lint",
)