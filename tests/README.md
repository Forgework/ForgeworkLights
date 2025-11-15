# ForgeworkLights Tests

## Root Helper Validation Tests

The `test_root_helper.sh` script validates the security hardening of the `fw_root_helper` binary.

### Running Tests

```bash
# Build the project first
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build

# Run validation tests
./tests/test_root_helper.sh

# Or specify custom helper path
./tests/test_root_helper.sh /path/to/fw_root_helper
```

### What Gets Tested

**Input Validation:**
- Rejects empty input
- Rejects odd-length hex strings
- Rejects invalid hex characters
- Rejects too-small payloads (< 1 LED)
- Rejects too-large payloads (> 100 LEDs)
- Rejects non-RGB-triplet data
- Accepts valid 1-22 LED payloads
- Handles mixed case hex

**Security:**
- Rejects shell injection attempts
- Rejects command injection attempts
- Rejects pipe injection attempts

### Test Output

```
Testing: No arguments ... PASS
Testing: Empty string ... PASS
Testing: Odd length hex ... PASS
Testing: Invalid hex chars ... PASS
...
```

Green PASS = test succeeded  
Red FAIL = test failed  
Yellow SKIP = test requires root (can't fully execute)

### Notes

- Most tests verify the helper rejects malformed input (exit code != 0)
- Valid payload tests require root to actually execute framework_tool
- These tests run the helper but don't actually write to LEDs
