# Build-only adapter: modern MSYS2 GLEW exports an imported target with a
# configuration layout CMake's legacy FindGLEW variable extraction misses.
find_package(GLEW CONFIG REQUIRED)
get_target_property(GLEW_INCLUDE_DIRS GLEW::GLEW INTERFACE_INCLUDE_DIRECTORIES)
set(GLEW_LIBRARIES GLEW::GLEW)
set(GLEW_FOUND TRUE)
