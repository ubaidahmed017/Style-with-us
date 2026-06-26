#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Running Style With Us Test Suite ===${NC}"

# Part 1: Run Backend Tests
echo -e "\n${GREEN}Step 1: Running Backend Tests (pytest)...${NC}"
cd D:/ubaid/app/backend

# Verify virtual environment or python packages
if [ -f "requirements.txt" ]; then
    echo "Verifying backend dependencies..."
    pip install -q -r requirements.txt
fi

# Run pytest with coverage
pytest -v tests/

# Part 2: Run Flutter Tests
echo -e "\n${GREEN}Step 2: Running Flutter Frontend Tests (flutter test)...${NC}"
cd D:/ubaid/app/FYP

# Run flutter test
flutter test test/auth_test.dart

echo -e "\n${GREEN}=== All Tests Passed Successfully! ===${NC}"
