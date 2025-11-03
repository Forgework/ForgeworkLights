# omarchy-argb

C++20 daemon to sync Framework Desktop JARGB1 WS2812B strip with Omarchy theme.

## Build

```
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

## Run

- Probe: `build/omarchy-argb probe`
- Once: `build/omarchy-argb once`
- Daemon: `build/omarchy-argb daemon`

User config: `~/.config/omarchy-argb/config.toml` (see config/config.toml.sample)
