# External lifecycle adaptation; preserve ordinary engine/assertion behavior.
function(redux_phase1_test_entry)
  target_compile_definitions(Test_gemrb_core PRIVATE USE_OPENGL_BACKEND=1)
  target_sources(Test_gemrb_core PRIVATE "${CMAKE_SOURCE_DIR}/redux/tools/phase0/managed-test-main.cpp")
endfunction()
cmake_language(DEFER CALL redux_phase1_test_entry)
