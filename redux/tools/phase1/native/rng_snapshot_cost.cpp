// External initialized-library API microbenchmark. No game or renderer bootstrap.
#include "RNG.h"
#include "Logging/Logging.h"
#include <chrono>
#include <cstdint>
#include <exception>
#include <fstream>
#include <iostream>
#include <locale>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#ifdef _WIN32
#include <process.h>
#else
#include <unistd.h>
#endif

#ifndef GEMRB_RNG_TRY_SNAPSHOT_STATE
#error This external host requires the existing noninitializing snapshot API
#endif

using namespace GemRB;
using Clock = std::chrono::steady_clock;

static std::string Q(const std::string& value)
{
    std::string result="\"";
    for (char c : value) {
        if (c=='\\' || c=='"') result+='\\';
        if (c=='\n') result+="\\n"; else if (c=='\r') result+="\\r"; else result+=c;
    }
    return result+'"';
}

static std::string State(const std::mt19937_64& value)
{
    std::ostringstream out; out.imbue(std::locale::classic()); out << value; return out.str();
}

static size_t Bounded(const std::string& value, size_t maximum)
{
    if (value.empty() || value.find_first_not_of("0123456789")!=std::string::npos)
        throw std::runtime_error("Invalid numeric argument");
    const auto number=std::stoull(value);
    if (!number || number>maximum) throw std::runtime_error("Numeric argument outside bound");
    return size_t(number);
}

int main(int argc, char** argv)
{
    struct Shutdown { ~Shutdown() { ToggleLogging(false, true); } } shutdown;
    std::string output, nonce;
    size_t iterations=100000, limitMS=30000;
    try {
        for (int i=1; i<argc; i+=2) {
            if (i+1>=argc) throw std::runtime_error("Missing argument value");
            const std::string name=argv[i], value=argv[i+1];
            if (name=="--output") output=value;
            else if (name=="--nonce") nonce=value;
            else if (name=="--iterations") iterations=Bounded(value,1000000);
            else if (name=="--time-limit-ms") limitMS=Bounded(value,60000);
            else throw std::runtime_error("Unknown argument");
        }
        if (output.empty() || nonce.size()!=32 || nonce.find_first_not_of("0123456789abcdef")!=std::string::npos)
            throw std::runtime_error("Output and fresh hexadecimal nonce required");
        std::string payload;
        std::exception_ptr failure;
        // A genuinely fresh thread isolates TLS availability from DLL/main-thread startup.
        std::thread worker([&] {
            try {
                const auto begun=Clock::now();
                auto budget=[&] {
                    if (std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now()-begun).count()>
                        static_cast<long long>(limitMS)) throw std::runtime_error("Phase-boundary time budget exceeded");
                };
                std::mt19937_64 absent;
                const auto sentinel=absent;
                size_t absentTrue=0;
                for (size_t i=0;i<iterations;++i) absentTrue+=RNG::TrySnapshotState(absent) ? 1 : 0;
                const bool absentUnchanged=absent==sentinel;
                const bool initializedAfterAbsent=RNG::TrySnapshotState(absent);
                budget();
                std::ostringstream out; out.imbue(std::locale::classic());
                out << "\"absent\":{\"iterations\":" << iterations << ",\"observed_count\":" << absentTrue
                    << ",\"output_unchanged\":" << (absentUnchanged ? "true":"false")
                    << ",\"initialized_after\":" << (initializedAfterAbsent ? "true":"false")
                    << ",\"before\":" << Q(State(sentinel)) << ",\"after\":" << Q(State(absent)) << "},\"trials\":[";
                (void) RNG::getInstance(); // Normal one-time lazy initialization; no seed/reset API.
                for (unsigned trial=0;trial<3;++trial) {
                    std::mt19937_64 before, after, copy;
                    if (!RNG::TrySnapshotState(before)) throw std::runtime_error("Initialized RNG unavailable");
                    size_t copied=0;
                    const auto begin=Clock::now();
                    for (size_t i=0;i<iterations;++i) copied+=RNG::TrySnapshotState(copy) ? 1 : 0;
                    const auto end=Clock::now();
                    if (!RNG::TrySnapshotState(after)) throw std::runtime_error("RNG disappeared after trial");
                    budget();
                    if (trial) out << ',';
                    out << "{\"trial\":" << trial+1 << ",\"iterations\":" << iterations << ",\"observed_count\":" << copied
                        << ",\"elapsed_ns\":" << std::chrono::duration_cast<std::chrono::nanoseconds>(end-begin).count()
                        << ",\"before\":" << Q(State(before)) << ",\"after\":" << Q(State(after))
                        << ",\"copied\":" << Q(State(copy)) << '}';
                }
                std::mt19937_64 controlBefore, controlAfter;
                if (!RNG::TrySnapshotState(controlBefore)) throw std::runtime_error("Control RNG unavailable");
                (void) RAND<uint64_t>(); // One real live draw, never a draw from a copied engine.
                if (!RNG::TrySnapshotState(controlAfter)) throw std::runtime_error("Control RNG disappeared");
                budget();
                out << "],\"control\":{\"real_live_rand_draws\":1,\"before\":" << Q(State(controlBefore))
                    << ",\"after\":" << Q(State(controlAfter)) << "}";
                payload=out.str();
            } catch (...) { failure=std::current_exception(); }
        });
        worker.join();
        if (failure) std::rethrow_exception(failure);
        std::ofstream file(output, std::ios::out|std::ios::trunc);
        const auto pid=
#ifdef _WIN32
            _getpid();
#else
            getpid();
#endif
        file << "{\"schema\":\"bg-redux-rng-snapshot-cost/1\",\"nonce\":" << Q(nonce)
            << ",\"pid\":" << pid << ",\"completed\":true,\"fresh_thread\":true,\"trials_expected\":3"
            << ",\"clock\":\"std::chrono::steady_clock\",\"clock_is_steady\":" << (Clock::is_steady ? "true":"false")
            << ",\"iterations\":" << iterations << ",\"time_limit_ms\":" << limitMS
            << ",\"copied_engine_bytes\":" << sizeof(std::mt19937_64)
            << ",\"state_words\":" << std::mt19937_64::state_size << ',' << payload << "}\n";
        if (!file) throw std::runtime_error("Cannot write complete benchmark result");
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "RNG snapshot microbenchmark failed: " << error.what() << '\n';
        return 1;
    }
}
