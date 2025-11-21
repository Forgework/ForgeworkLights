# ForgeworkLights Security Architecture

## Two-Tier Privilege Separation

ForgeworkLights uses a secure two-tier architecture to minimize privilege escalation risks while providing hardware access to the Framework Desktop ARGB LEDs.

### Components

#### 1. User Daemon (`forgeworklights`)
- **Location**: `/usr/local/bin/forgeworklights`
- **Permissions**: `755` (user-executable)
- **Owner**: User
- **Runs as**: Logged-in Omarchy user
- **Service**: User-level systemd (`~/.config/systemd/user/forgeworklights.service`)

**Responsibilities:**
- Monitor theme changes via inotify
- Read theme files from `~/.config/omarchy/`
- Calculate LED colors and gradients
- Manage animations and brightness
- Call root helper for hardware writes

**Security:**
- Never runs as root
- Never directly accesses hardware
- No sudo permissions required
- Handles all user-configurable logic

#### 2. Root Helper (`fw_root_helper`)
- **Location**: `/usr/local/libexec/fw_root_helper`
- **Permissions**: `4755` (setuid-root)
- **Owner**: `root:root`
- **Runs as**: Root (via setuid bit)
- **Service**: Called by daemon, not a service

**Responsibilities:**
- Accept validated LED data from daemon
- Decode hex-encoded RGB payload
- Execute `framework_tool --rgbkbd` with validated args
- Exit immediately after execution

**Security Hardening:**
- `clearenv()` - Clear all environment variables
- `umask(0077)` - Restrictive file creation mask
- `setuid(0)` and `setgid(0)` - Ensure root privileges
- Strict input validation:
  - Hex format only
  - Length checks (1-22 LEDs)
  - RGB triplet validation
  - No shell metacharacters
- No configuration files
- No file I/O except exec
- No user-controllable logic
- Direct `execv()` - no shell interpretation

### Communication Protocol

```
User Daemon                     Root Helper
    |                                |
    |-- Calculate LED colors         |
    |                                |
    |-- Encode to hex string ------->|
    |                                |
    |                                |-- Validate input
    |                                |-- Decode hex to bytes
    |                                |-- Build argv for framework_tool
    |                                |-- execv(/usr/bin/framework_tool)
    |                                |
    |<----- Return exit code --------|
    |                                |
```

**Protocol Details:**
- Single argument: hex-encoded LED data
- Format: `RRGGBBRRGGBB...` (2 hex chars per byte)
- Example: `FF0000` = 1 red LED, `FF000000FF00` = red + green LEDs
- Helper decodes and transforms to: `framework_tool --rgbkbd 0 0xRRGGBB 0xRRGGBB ...`

### Installation

The installer (`install.sh`) handles proper installation:

```bash
# User daemon - standard binary installation
sudo install -Dm755 build/forgeworklights /usr/local/bin/forgeworklights

# Root helper - setuid-root permissions
sudo install -Dm755 -o root -g root build/fw_root_helper /usr/local/libexec/fw_root_helper
sudo chmod 4755 /usr/local/libexec/fw_root_helper
```

### Verification

Check installation:
```bash
# Verify helper permissions (setuid bit)
ls -l /usr/local/libexec/fw_root_helper
# Should show: -rwsr-xr-x 1 root root ... fw_root_helper
# The 's' in permissions indicates setuid bit is set

# Verify daemon is user-owned
ls -l /usr/local/bin/forgeworklights
# Should show: -rwxr-xr-x 1 root root ... forgeworklights

# Check service runs as user
systemctl --user status forgeworklights
```

### Current Limiting and Safety

**Hardware Constraints:**
- Framework JARGB1 header: 5V rail with 2.4A maximum safe draw
- WS2812B LEDs: 60mA worst-case current per LED at full white
- 22 LEDs at full brightness × 60mA = 1.32A (within limits)
- Safety mode prevents invalid configurations or future LED count changes from exceeding rail capacity

**Physical Model:**
```
I_estimated = led_count × 0.060A × brightness_scalar
```

Where:
- `led_count` = actual number of LEDs in the frame
- `brightness_scalar` = brightness value in [0.0, 1.0] (always clamped)
- 0.060A = WS2812B full-white maximum current per LED

**Safety Mode (default: ON):**
1. Brightness is clamped to [0.0, 1.0]
2. Estimated current is calculated using physical model
3. If `I_estimated > 2.4A`, uniform scale factor is applied to all RGB channels
4. Scale factor: `scale = 2.4A / I_estimated`
5. Final values are clamped to [0, 255]
6. One-time log message indicates limiting engaged

**Safety Mode OFF:**
- Brightness clamping still occurs
- No current limiting applied
- Use only if you understand your hardware limits

**CLI Flag:**
```bash
forgeworklights daemon --safety=on    # Default
forgeworklights daemon --safety=off   # Disable limiting
forgeworklights once --safety=on      # Also works for test pattern
```

### Security Considerations

**Attack Vectors Mitigated:**
1. **Shell injection**: Helper uses `execv()`, not `system()`
2. **Path traversal**: No file operations in helper
3. **Environment manipulation**: `clearenv()` clears all env vars
4. **Argument injection**: Strict hex validation rejects metacharacters
5. **Buffer overflow**: Fixed-size buffers with length checks
6. **Integer overflow**: LED count limits (1-22)

**Remaining Trust Requirements:**
- User must trust `framework_tool` (from Framework vendor)
- Root helper must be installed correctly (root:root 4755)
- System must be configured correctly (no modified helper)

### Testing

Run validation tests:
```bash
./tests/test_root_helper.sh
```

Tests verify:
- Input validation (empty, malformed, oversized)
- Hex decoding correctness
- Rejection of injection attempts
- Proper error codes

### References

- Framework Desktop JARGB1 header specification
- Linux capability(7) - Privilege management
- execve(2) - Secure program execution
- systemd.service(5) - User-level services
