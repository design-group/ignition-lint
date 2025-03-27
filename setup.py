from setuptools import setup

setup(
    name="ignition-lint",
    version="0.1.0",
    py_modules=["ignition_lint", "checker"],  # Treat as standalone modules
    install_requires=[],
    entry_points={
        "console_scripts": [
            "ignition-lint = ignition_lint:main",  # No package prefix
        ],
    },
    author="Eric Knorr",
    description="A linter for Ignition JSON files",
    license="MIT",
    url="https://github.com/design-group/ignition-lint",
)