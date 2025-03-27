from setuptools import setup, find_packages

setup(
    name="ignition-lint",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[],  # Add dependencies here
    entry_points={
        "console_scripts": [
            "ignition-lint = ignition_lint:main",
        ],
    },
)