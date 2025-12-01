# ForgeworkLights Dependencies

Complete list of all dependencies required to build and run ForgeworkLights. Handled by install.sh script.

## Build Dependencies

Required to compile the daemon from source:

- **CMake** `>= 3.16`
  - Build system generator
  - Install: `sudo pacman -S cmake`

- **C++ Compiler** (one of):
  - **GCC** `>= 11.0` with C++20 support
    - Install: `sudo pacman -S gcc`
  - **Clang** `>= 14.0` with C++20 support
    - Install: `sudo pacman -S clang`

- **pthread** (Linux)
  - POSIX threads library
  - Usually included with glibc

## Runtime Dependencies

### Required

- **framework_tool**
  - Framework Desktop hardware control utility
  - Package: `framework-system` (Arch AUR)
  - Install: `sudo pacman -S framework-system`
  - Purpose: LED hardware control

### Optional (for TUI control panel)

- **Python** `>= 3.11`
  - Required for TUI interface
  - Install: `sudo pacman -S python`

- **Textual** `>= 6.5.0, < 7.0.0`
  - Python TUI framework
  - Installed via: `pip install --user -r requirements.txt`
  - Tested version: 6.5.0

- **bc**
  - Command-line calculator
  - Install: `sudo pacman -S bc`
  - Purpose: Brightness calculations

## Python Dependencies

Defined in `requirements.txt`:

```
textual>=6.5.0,<7.0.0
```

Install with:
```bash
pip install --user -r requirements.txt
```

## System Requirements

- **Operating System**: Linux
- **Hardware**: Framework Desktop with RGB LED strips
  - Framework Laptops are NOT supported (different LED controller)
- **Architecture**: x86_64, ARM64 (untested)

## Tested Versions

This project has been tested with:

- **OS**: Arch Linux (Omarchy)
- **Chipset**: AMD Ryzen AI MAX+ 395 APU
- **CMake**: 3.16+
- **GCC**: 11.0+
- **Python**: 3.13
- **Textual**: 6.5.0
- **framework-system**: Latest from AUR

## Version Constraints Explained

### Python Dependencies

- `textual>=6.5.0,<7.0.0`: Allows minor/patch updates (6.5.x, 6.6.x) but blocks major version 7.x which may have breaking API changes

### System Dependencies

System packages are managed by pacman and follow Arch Linux's rolling release model. The install script verifies their presence but does not enforce specific versions.

## Compatibility Notes

- **Python 3.11+** required for `tomllib` (TOML parsing)
- **C++20** required for modern language features
- **Framework Desktop** specific - will not work on Framework Laptops or other hardware
