cmake_minimum_required(VERSION 3.16)
project(forgeworklights VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Main user daemon
add_executable(forgeworklights
  src/main.cpp
  src/cli.cpp
  src/framework_tool.cpp
  src/config.cpp
  src/argb_daemon.cpp
  src/theme_database.cpp
  src/theme.cpp
  src/palette_loader.cpp
  src/color_utils.cpp
)

target_include_directories(forgeworklights PRIVATE include)

# Linux specific libs
if(UNIX AND NOT APPLE)
  target_link_libraries(forgeworklights PRIVATE pthread)
endif()

# Root helper binary (privileged hardware access only)
add_executable(fw_root_helper
  src/fw_root_helper.cpp
)

# Install targets
install(TARGETS forgeworklights RUNTIME DESTINATION bin)

# Install root helper to libexec with setuid-root
# Note: CMAKE cannot set ownership or setuid bit, must be done by install script (4755)
install(TARGETS fw_root_helper 
        RUNTIME DESTINATION libexec
        PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE)

install(FILES config/config.toml.sample DESTINATION share/forgeworklights)
install(FILES systemd/forgeworklights.service DESTINATION lib/systemd/user)
