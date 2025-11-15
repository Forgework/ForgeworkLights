# ForgeworkLights Security Architecture

## Two-Tier Privilege Separation

ForgeworkLights uses a secure two-tier architecture to minimize privilege escalation risks while providing hardware access to the Framework Desktop ARGB LEDs.

### Components

#### 1. User Daemon (`omarchy-argb`)
- **Location**: `/usr/local/bin/omarchy-argb`
- **Permissions**: `755` (user-executable)
- **Owner**: User
- **Runs as**: Logged-in Omarchy user
- **Service**: User-level systemd (`~/.config/systemd/user/omarchy-argb.service`)

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
  - Length checks (1-100 LEDs)
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
sudo install -Dm755 build/omarchy-argb /usr/local/bin/omarchy-argb

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
ls -l /usr/local/bin/omarchy-argb
# Should show: -rwxr-xr-x 1 root root ... omarchy-argb

# Check service runs as user
systemctl --user status omarchy-argb
```

### Advantages Over Previous Approach

**Old Architecture (sudoers wildcard):**
- Required: `your_username ALL=(ALL) NOPASSWD: /usr/bin/framework_tool --rgbkbd *`
- Risks:
  - Wildcard allows any arguments
  - User could craft malicious framework_tool invocations
  - Broad sudo permissions
  - No input validation

**New Architecture (dedicated root helper):**
- No sudoers rules needed
- Minimal attack surface (single-purpose binary)
- Strict input validation
- No shell interpretation
- Root helper is auditable (< 200 lines)
- Follows principle of least privilege

### Security Considerations

**Attack Vectors Mitigated:**
1. **Shell injection**: Helper uses `execv()`, not `system()`
2. **Path traversal**: No file operations in helper
3. **Environment manipulation**: `clearenv()` clears all env vars
4. **Argument injection**: Strict hex validation rejects metacharacters
5. **Buffer overflow**: Fixed-size buffers with length checks
6. **Integer overflow**: LED count limits (1-100)

**Remaining Trust Requirements:**
- User must trust `framework_tool` (from Framework vendor)
- Root helper must be installed correctly (root:root 700)
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

### Migration from Old Version

If upgrading from a version using sudoers:

1. Install new version: `./install.sh`
2. Old sudoers rule is automatically removed by uninstall/install scripts
3. Restart service: `systemctl --user restart omarchy-argb`
4. Verify: Check logs for "sending N LEDs via root helper" message

### References

- Framework Desktop JARGB1 header specification
- Linux capability(7) - Privilege management
- execve(2) - Secure program execution
- systemd.service(5) - User-level services
