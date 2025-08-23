#!/bin/bash
#
# Validation Script for Local GitHub Actions Testing
#
# This script validates that local GitHub Actions testing is working correctly
# by running a subset of the workflow in dry-run mode.
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔍 Validating Local GitHub Actions Setup...${NC}"

# Ensure act is available
if ! command -v act &> /dev/null; then
    if [ -f "./bin/act" ]; then
        export PATH=$PWD/bin:$PATH
        echo -e "${GREEN}✓ Using local act installation${NC}"
    else
        echo -e "${RED}✗ act not found${NC}"
        exit 1
    fi
fi

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# List available workflows
echo -e "${YELLOW}Available workflows:${NC}"
act --list 2>/dev/null | head -10

# Test workflow parsing (dry run)
echo
echo -e "${YELLOW}Testing workflow parsing...${NC}"
if act --dry-run > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Workflows parse successfully${NC}"
else
    echo -e "${RED}✗ Workflow parsing failed${NC}"
    exit 1
fi

# Validate specific workflow files
echo
echo -e "${YELLOW}Validating individual workflows...${NC}"

for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
    if [ -f "$workflow" ]; then
        workflow_name=$(basename "$workflow")
        echo -n "  $workflow_name: "
        
        # Test if the workflow file is valid
        if act --dry-run -W "$workflow" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
        fi
    fi
done

echo
echo -e "${GREEN}🎉 Local GitHub Actions setup validation complete!${NC}"
echo
echo "Usage examples:"
echo "  ./test-actions.sh                    # Run all workflows"
echo "  ./test-actions.sh ci                 # Run CI workflow only"  
echo "  ./test-actions.sh unittest           # Run unittest workflow only"
echo "  ./test-actions.sh list               # List available workflows"