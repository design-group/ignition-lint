# src/ignition_lint.py
import json
import sys
import argparse
import os
import glob
import re
from .checker import StyleChecker  # Assuming you're using the src/ structure

# ... (JsonLinter class unchanged) ...

def main():
    """Main function to lint Ignition view.json files for style inconsistencies."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--files",
        default="**/view.json",
        help="Comma-separated list of ignition files or glob patterns to lint (used when run manually)",
    )
    parser.add_argument(
        "--component-style",
        default="PascalCase",  # Default for pre-commit
        help="Naming convention style for components",
    )
    parser.add_argument(
        "--parameter-style",
        default="camelCase",  # Default for pre-commit
        help="Naming convention style for parameters",
    )
    parser.add_argument(
        "--component-style-rgx",
        help="Regex pattern for naming convention style of components",
    )
    parser.add_argument(
        "--parameter-style-rgx",
        help="Regex pattern for naming convention style of parameters",
    )
    parser.add_argument(
        "input_files",
        nargs="*",  # Accept zero or more positional arguments
        help="Files passed by pre-commit (overrides --files when present)",
    )
    args = parser.parse_args()

    # Use positional arguments (from pre-commit) if provided; otherwise, fall back to --files
    files_to_lint = args.input_files if args.input_files else args.files.split(",")

    if not files_to_lint:
        print("No files specified or found matching the patterns")
        sys.exit(0)

    linter = JsonLinter(
        component_style=args.component_style,
        parameter_style=args.parameter_style,
        component_style_rgx=args.component_style_rgx,
        parameter_style_rgx=args.parameter_style_rgx,
    )
    number_of_errors = 0

    # Handle both direct file paths and glob patterns
    for file_pattern in files_to_lint:
        if re.search(r"[\*\?\[\]]", file_pattern):  # If it's a glob pattern
            matched_files = glob.glob(file_pattern, recursive=True)
            for file_path in matched_files:
                number_of_errors += linter.lint_file(file_path)
        else:  # Direct file path
            number_of_errors += linter.lint_file(file_pattern)

    if not number_of_errors:
        print("No style inconsistencies found")
        sys.exit(0)
    sys.exit(1)

if __name__ == "__main__":
    main()
