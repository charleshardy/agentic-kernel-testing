#!/bin/bash

# Script to organize and clean up root directory files
# Moves test, verification, debug, and runner scripts to appropriate subdirectories

echo "=== Root Directory Cleanup Script ==="
echo ""

# Create target directories if they don't exist
mkdir -p dev-scripts/test-scripts
mkdir -p dev-scripts/verification-scripts
mkdir -p dev-scripts/debug-scripts
mkdir -p dev-scripts/runners
mkdir -p dev-scripts/validation
mkdir -p archive/old-scripts

# Function to move files if they exist
move_if_exists() {
    local pattern=$1
    local target_dir=$2
    local count=0
    
    for file in $pattern; do
        if [ -f "$file" ]; then
            echo "Moving: $file -> $target_dir/"
            mv "$file" "$target_dir/"
            ((count++))
        fi
    done
    
    return $count
}

echo "Moving test scripts..."
move_if_exists "test_*.py" "dev-scripts/test-scripts"
move_if_exists "simple_test*.py" "dev-scripts/test-scripts"
move_if_exists "*_test.py" "dev-scripts/test-scripts"

echo ""
echo "Moving verification scripts..."
move_if_exists "verify_*.py" "dev-scripts/verification-scripts"
move_if_exists "*_verification.py" "dev-scripts/verification-scripts"

echo ""
echo "Moving debug scripts..."
move_if_exists "debug_*.py" "dev-scripts/debug-scripts"

echo ""
echo "Moving runner scripts..."
move_if_exists "run_*.py" "dev-scripts/runners"
move_if_exists "*_runner.py" "dev-scripts/runners"

echo ""
echo "Moving validation scripts..."
move_if_exists "comprehensive_*.py" "dev-scripts/validation"
move_if_exists "final_*.py" "dev-scripts/validation"
move_if_exists "quick_*.py" "dev-scripts/validation"

echo ""
echo "Moving old commit scripts..."
move_if_exists "commit_*.sh" "archive/old-scripts"
move_if_exists "push_*.sh" "archive/old-scripts"

echo ""
echo "=== Cleanup Complete ==="
echo ""
echo "File organization:"
echo "  - Test scripts: dev-scripts/test-scripts/"
echo "  - Verification scripts: dev-scripts/verification-scripts/"
echo "  - Debug scripts: dev-scripts/debug-scripts/"
echo "  - Runner scripts: dev-scripts/runners/"
echo "  - Validation scripts: dev-scripts/validation/"
echo "  - Archived scripts: archive/old-scripts/"
echo ""

# List remaining Python files in root
echo "Remaining Python files in root directory:"
ls -1 *.py 2>/dev/null | head -20 || echo "  (none)"