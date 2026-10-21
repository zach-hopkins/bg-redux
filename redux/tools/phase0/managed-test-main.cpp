// Phase 0 external test entry point; engine and assertion sources are unchanged.
// Shut logging down while DLL worker threads can still run, before CRT teardown.
#include "Logging/Logging.h"
#include <gtest/gtest.h>
#include <cstdio>

int main(int argc, char** argv)
{
    testing::InitGoogleTest(&argc, argv);
    const int result = RUN_ALL_TESTS();
    std::fputs("[Redux harness] Explicit logger shutdown before process exit\n", stderr);
    GemRB::ToggleLogging(false, true);
    return result;
}
