#!/bin/bash
#
# Local GitHub Actions Testing Script
# 
# This script allows developers to test GitHub Actions workflows locally
# before committing changes, preventing CI failures.
#
# Prerequisites:
# - Docker must be running
# - act must be installed (run: curl -q https://raw.githubusercontent.com/nektos/act/master/install.sh | bash)
#
# Usage:
#   ./test-actions.sh [workflow-name] [event]
#
# Examples:
#   ./test-actions.sh                    # Run all workflows on push event
#   ./test-actions.sh ci                 # Run CI workflow  
#   ./test-actions.sh unittest pull_request  # Run unittest workflow on PR event
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure act is available
if ! command -v act &> /dev/null; then
    if [ -f "./bin/act" ]; then
        export PATH=$PWD/bin:$PATH
        echo -e "${YELLOW}Using local act installation${NC}"
    else
        echo -e "${RED}Error: act is not installed.${NC}"
        echo "Install it with: curl -q https://raw.githubusercontent.com/nektos/act/master/install.sh | bash"
        exit 1
    fi
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Parse arguments
WORKFLOW=${1:-""}
EVENT=${2:-"push"}

echo -e "${BLUE}🧪 Testing GitHub Actions locally...${NC}"
echo -e "${BLUE}Workflow: ${WORKFLOW:-"all"}, Event: $EVENT${NC}"
echo

# Function to run a specific workflow
run_workflow() {
    local workflow_file=$1
    local event_type=$2
    
    echo -e "${YELLOW}Running workflow: $workflow_file${NC}"
    
    if [ -n "$workflow_file" ]; then
        act "$event_type" -W ".github/workflows/$workflow_file"
    else
        act "$event_type"
    fi
}

# Function to list available workflows
list_workflows() {
    echo -e "${BLUE}Available workflows:${NC}"
    for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
        if [ -f "$workflow" ]; then
            basename "$workflow"
        fi
    done
    echo
}

# Main execution
case "$WORKFLOW" in
    "")
        echo -e "${YELLOW}Running all workflows...${NC}"
        act "$EVENT"
        ;;
    "list"|"-l"|"--list")
        list_workflows
        exit 0
        ;;
    "ci")
        run_workflow "ci.yml" "$EVENT"
        ;;
    "unittest")
        run_workflow "unittest.yml" "$EVENT"
        ;;
    "integration-test")
        run_workflow "integration-test.yml" "$EVENT"
        ;;
    "example-ci")
        run_workflow "example-ci.yaml" "$EVENT"
        ;;
    *)
        if [ -f ".github/workflows/$WORKFLOW" ]; then
            run_workflow "$WORKFLOW" "$EVENT"
        elif [ -f ".github/workflows/$WORKFLOW.yml" ]; then
            run_workflow "$WORKFLOW.yml" "$EVENT"
        elif [ -f ".github/workflows/$WORKFLOW.yaml" ]; then
            run_workflow "$WORKFLOW.yaml" "$EVENT"
        else
            echo -e "${RED}Error: Workflow '$WORKFLOW' not found.${NC}"
            echo
            list_workflows
            exit 1
        fi
        ;;
esac

echo
echo -e "${GREEN}✅ Local GitHub Actions testing completed!${NC}"