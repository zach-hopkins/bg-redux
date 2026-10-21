#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT=/c/Users/zach/DOCUME~1/ChatGPT/BGMULT~1
cd "$TASK_ROOT"
TASK_TEST_MODE=${1:-stock}
case "$TASK_TEST_MODE" in
  stock) TASK_TEST_INCLUDE="" ;;
  live) TASK_TEST_INCLUDE="$TASK_ROOT/tools/phase0/cmake/enable-live-tests.cmake" ;;
  managed) TASK_TEST_INCLUDE="$TASK_ROOT/tools/phase0/cmake/managed-live-tests.cmake" ;;
  *) echo 'Expected stock, live or managed test mode' >&2; exit 2 ;;
esac
cmake -S gemrb -B phase0-local/build -G Ninja \
  -DCMAKE_PROJECT_TOP_LEVEL_INCLUDES="$TASK_TEST_INCLUDE" \
  -DCMAKE_BUILD_TYPE=Debug -DSDL_BACKEND=SDL2 -DOPENGL_BACKEND=OpenGL \
  -DUSE_TESTS=ON -DUSE_LIBVLC=OFF -DDISABLE_WERROR=ON \
  -DPython_ROOT_DIR="$TASK_ROOT/phase0-local/toolchain/msys64/ucrt64" \
  -DPython_FIND_REGISTRY=NEVER \
  -DPython_INCLUDE_DIR="$TASK_ROOT/phase0-local/toolchain/msys64/ucrt64/include/python3.14" \
  -DPython_LIBRARY="$TASK_ROOT/phase0-local/toolchain/msys64/ucrt64/lib/libpython3.14.dll.a" \
  -DCMAKE_MODULE_PATH="$TASK_ROOT/tools/phase0/cmake" \
  -DCMAKE_RC_FLAGS="--preprocessor=C:/Users/zach/DOCUME~1/ChatGPT/BGMULT~1/phase0-local/toolchain/msys64/ucrt64/bin/gcc.exe --preprocessor-arg=-E --preprocessor-arg=-xc --preprocessor-arg=-DRC_INVOKED" \
  -DCMAKE_INSTALL_PREFIX="$TASK_ROOT/phase0-local/install"
cmake --build phase0-local/build --parallel 6
pacman -Q > phase0-local/logs/msys-package-versions.txt
cmake --version > phase0-local/logs/cmake-version.txt
g++ --version > phase0-local/logs/compiler-version.txt
ctest --test-dir phase0-local/build -N > phase0-local/logs/ctest-list.txt
