cmake_minimum_required(VERSION 3.16)
project(omarchy-argb VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

add_executable(omarchy-argb
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

target_include_directories(omarchy-argb PRIVATE include)

# Linux specific libs
if(UNIX AND NOT APPLE)
  target_link_libraries(omarchy-argb PRIVATE pthread)
endif()

install(TARGETS omarchy-argb RUNTIME DESTINATION bin)
install(FILES config/config.toml.sample DESTINATION share/omarchy-argb)
install(FILES systemd/omarchy-argb.service DESTINATION lib/systemd/user)
