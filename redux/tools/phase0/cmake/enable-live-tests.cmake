# The pinned Windows source guards these tests on a renderer-private define.
# Enable the existing guarded code on the test target only, after it exists.
cmake_language(DEFER CALL target_compile_definitions Test_gemrb_core PRIVATE USE_OPENGL_BACKEND=1)
