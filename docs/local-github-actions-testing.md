# Local GitHub Actions Testing

This guide explains how to test GitHub Actions workflows locally before committing, preventing CI failures and speeding up development.

## Prerequisites

1. **Docker**: Must be running on your system
2. **act**: Local GitHub Actions runner (automatically installed by setup script)

## Quick Start

### 1. Install act (if not already installed)

```bash
# Install act
curl -q https://raw.githubusercontent.com/nektos/act/master/install.sh | bash

# Add to PATH (or move to /usr/local/bin)
export PATH=$PWD/bin:$PATH
```

### 2. Test Local Setup

```bash
# Validate your setup
./validate-local-actions.sh
```

### 3. Run Workflows Locally

```bash
# Run all workflows (push event)
./test-actions.sh

# Run specific workflow
./test-actions.sh ci

# Run workflow with specific event
./test-actions.sh unittest pull_request

# List available workflows
./test-actions.sh list
```

## Available Workflows

| Workflow | File | Description |
|----------|------|-------------|
| `ci` | `ci.yml` | Full CI pipeline with multi-Python testing |
| `unittest` | `unittest.yml` | Unit tests only |
| `integration-test` | `integration-test.yml` | Integration tests |
| `example-ci` | `example-ci.yaml` | Example CI with pre-commit hooks |

## Common Usage Patterns

### Before Committing Changes

```bash
# Test the main CI pipeline
./test-actions.sh ci

# If successful, commit with confidence
git add .
git commit -m "Your changes"
git push
```

### Testing Specific Components

```bash
# Test only unit tests (fastest)
./test-actions.sh unittest

# Test only integration tests  
./test-actions.sh integration-test

# Test pre-commit hooks
./test-actions.sh example-ci
```

### Debugging Workflow Issues

```bash
# Run with verbose output
act --verbose

# Run specific job within workflow
act -j test  # runs 'test' job only

# Dry run (parse only, don't execute)
act --dry-run
```

## Configuration Files

- `.actrc`: Basic act configuration
- `.github/.actrc`: Advanced project-specific configuration  
- `.github/act-secrets.env`: Local testing secrets (placeholders only)

## Platform Compatibility

The setup uses `catthehacker/ubuntu:act-22.04` for consistency with GitHub's `ubuntu-latest` runners.

**Apple Silicon (M1/M2) users**: If you encounter issues, run:
```bash
act --container-architecture linux/amd64
```

## Troubleshooting

### Docker Issues
```bash
# Ensure Docker is running
docker info

# If Docker daemon issues, restart Docker Desktop
```

### Permission Issues
```bash
# Make sure scripts are executable
chmod +x test-actions.sh validate-local-actions.sh
```

### Workflow Parsing Errors
```bash
# Validate workflow syntax
act --dry-run

# Check specific workflow file
act --dry-run -W .github/workflows/ci.yml
```

### Large Docker Images
```bash
# Use smaller base images (add to .actrc)
-P ubuntu-latest=catthehacker/ubuntu:act-22.04-slim
```

## Integration with Development Workflow

### Pre-commit Hook (Optional)

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
echo "Testing workflows locally before commit..."
./test-actions.sh ci
if [ $? -ne 0 ]; then
    echo "Local workflow test failed. Commit aborted."
    exit 1
fi
```

### VS Code Integration

Add to `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Test GitHub Actions",
            "type": "shell",
            "command": "./test-actions.sh",
            "args": ["ci"],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "panel": "new"
            }
        }
    ]
}
```

## Performance Tips

1. **Cache Docker images**: act downloads images once and reuses them
2. **Use dry-run for syntax checking**: `act --dry-run` is fast
3. **Test specific jobs**: Use `-j job-name` to run individual jobs
4. **Skip large workflows**: Test unit tests locally, full CI in GitHub

## Security Notes

- Local secrets in `.github/act-secrets.env` are placeholders only
- Never commit real secrets to version control  
- Local testing uses isolated Docker containers
- GitHub tokens in local testing are not functional

## Advanced Usage

### Custom Event Data

```bash
# Test with custom event payload
act push -e event.json
```

### Environment Variables

```bash
# Set environment variables
act -e PYTHON_VERSION=3.11

# Use environment file
act --env-file .env.test
```

### Matrix Testing

```bash
# Test specific matrix combination  
act -j test --matrix python-version:3.11
```

This local testing setup ensures your GitHub Actions workflows work correctly before pushing to remote, saving time and preventing CI failures.