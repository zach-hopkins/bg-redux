# External test-only adaptation. No engine or assertion source is patched.
function(redux_adapt_test_entry)
  target_compile_definitions(Test_gemrb_core PRIVATE USE_OPENGL_BACKEND=1)
  target_sources(Test_gemrb_core PRIVATE "${CMAKE_SOURCE_DIR}/../tools/phase0/managed-test-main.cpp")
endfunction()
cmake_language(DEFER CALL redux_adapt_test_entry)
