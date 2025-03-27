from setuptools import setup, find_packages

setup(
    name="ignition-lint",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[],  # Add dependencies if needed
    entry_points={
        "console_scripts": [
            "ignition-lint = ignition_lint.ignition_lint:main",  # Updated path
        ],
    },
    author="Eric Knorr",
    description="A linter for Ignition JSON files",
    license="MIT",
    url="https://github.com/design-group/ignition-lint",
)