#!/bin/bash
# Test script for fw_root_helper validation
# Tests input validation and error handling (does not actually execute framework_tool)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

HELPER="${1:-./build/fw_root_helper}"
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper function
test_case() {
    local name="$1"
    local expected_exit="$2"
    shift 2
    local args=("$@")
    
    echo -n "Testing: $name ... "
    
    if [ "$expected_exit" -eq 0 ]; then
        # Should succeed - but we can't actually test success without root
        if [ "$(id -u)" -ne 0 ]; then
            echo -e "${YELLOW}SKIP${NC} (requires root)"
            return
        fi
        if "$HELPER" "${args[@]}" &> /dev/null; then
            echo -e "${GREEN}PASS${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}FAIL${NC}"
            ((TESTS_FAILED++))
        fi
    else
        # Should fail
        if ! "$HELPER" "${args[@]}" &> /dev/null; then
            echo -e "${GREEN}PASS${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}FAIL${NC} (expected failure but succeeded)"
            ((TESTS_FAILED++))
        fi
    fi
}

echo "========================================"
echo "  fw_root_helper Validation Tests"
echo "========================================"
echo ""

if [ ! -f "$HELPER" ]; then
    echo -e "${RED}Error: Helper binary not found at $HELPER${NC}"
    echo "Build it first with: cmake --build build"
    exit 1
fi

echo "Testing input validation..."
echo ""

# Test: No arguments
test_case "No arguments" 1

# Test: Empty string
test_case "Empty string" 1 ""

# Test: Invalid hex (odd length)
test_case "Odd length hex" 1 "00FF0"

# Test: Invalid hex characters
test_case "Invalid hex chars" 1 "GGHHII"

# Test: Too small (less than 1 LED = 6 hex chars)
test_case "Too small" 1 "0000"

# Test: Too large (more than 100 LEDs = 600 hex chars)
LARGE_HEX=$(printf '%0600d' 0 | sed 's/0/FF/g')
test_case "Too large" 1 "$LARGE_HEX"

# Test: Not a multiple of 6 (RGB = 3 bytes = 6 hex chars)
test_case "Not RGB triplets" 1 "FF00FF00"

# Test: Valid 1 LED (minimum)
test_case "Valid 1 LED" 0 "FF0000"

# Test: Valid 3 LEDs
test_case "Valid 3 LEDs" 0 "FF000000FF000000FF"

# Test: Valid 22 LEDs (standard JARGB1)
VALID_22=$(printf '000000%.0s' {1..22})
test_case "Valid 22 LEDs" 0 "$VALID_22"

# Test: Mixed case hex (should work)
test_case "Mixed case hex" 0 "fF00Aa"

# Test: Special chars injection attempt
test_case "Shell injection attempt" 1 "\$(whoami)"
test_case "Command injection" 1 "FF0000; rm -rf /"
test_case "Pipe injection" 1 "FF0000 | cat /etc/passwd"

echo ""
echo "========================================"
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All $TESTS_PASSED tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$TESTS_FAILED tests failed, $TESTS_PASSED passed${NC}"
    exit 1
fi
