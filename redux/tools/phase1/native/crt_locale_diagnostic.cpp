// External diagnostic only: no GemRB headers, DLLs, game data or locale settings.
// Locale changes below affect this short-lived process's LC_CTYPE only.
#include <clocale>
#include <cstdint>
#include <cwctype>
#include <iostream>
#include <string>
#ifdef _WIN32
#include <windows.h>
#endif

namespace {
// Exact UTF-16 input and expected result from StringTest.StringToUpper.
const std::u16string input = u"\u0417\u0430\u043a\u043e\u043d\u0447\u0438\u0442\u044c";
const std::u16string expected = u"\u0417\u0410\u041a\u041e\u041d\u0427\u0418\u0422\u042c";

// Locale names are CRT bytes, whose encoding must not be inferred from console
// encoding. Preserve numeric bytes and an ASCII-only escaped preview.
void WriteBytes(const std::string& value)
{
    const char hex[] = "0123456789ABCDEF";
    std::cout << "{\"bytes\":[";
    bool first = true;
    for (unsigned char c : value) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << unsigned(c);
    }
    std::cout << "],\"escaped_bytes\":\"";
    for (unsigned char c : value) {
        if (c == '\\' || c == '"') std::cout << '\\' << char(c);
        else if (c >= 32 && c <= 126) std::cout << char(c);
        else std::cout << "\\\\x" << hex[c >> 4] << hex[c & 15];
    }
    std::cout << "\"}";
}

void WriteNullable(const char* value)
{
    if (value) WriteBytes(std::string(value));
    else std::cout << "null";
}

void WriteUnits(const std::u16string& value)
{
    std::cout << '[';
    for (std::size_t i = 0; i < value.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << std::uint32_t(value[i]);
    }
    std::cout << ']';
}

void WriteMapping()
{
    std::u16string output = input;
    std::cout << "{\"towupper_wint_results\":[";
    for (std::size_t i = 0; i < input.size(); ++i) {
        if (i) std::cout << ',';
        // Same per-code-unit operation as GemRB String.h; retain the full
        // return value as well as its assignment to a UTF-16 destination.
        const wint_t mapped = std::towupper(input[i]);
        std::cout << std::uint32_t(mapped);
        output[i] = static_cast<char16_t>(mapped);
    }
    std::cout << "],\"output_utf16_units\":";
    WriteUnits(output);
    std::cout << ",\"matches_StringTest_expected\":"
              << (output == expected ? "true" : "false") << '}';
}
}

int main(int argc, char** argv)
{
    if (argc != 3 || std::string(argv[1]) != "--compiler-command") {
        std::cerr << "Usage: crt_locale_diagnostic --compiler-command <exact compiler argv JSON>\n";
        return 2;
    }
    const char* initialPointer = std::setlocale(LC_CTYPE, nullptr);
    const bool initialAvailable = initialPointer != nullptr;
    const std::string initial = initialAvailable ? initialPointer : "";
    std::cout << "{\"schema\":\"bg-redux-crt-locale-diagnostic/1\","
                 "\"scope\":\"standalone process LC_CTYPE; no engine or OS locale settings\","
                 "\"compiler_command_declaration_unverified\":";
    WriteBytes(argv[2]);
    std::cout << ",\"compiler_version\":";
    WriteBytes(__VERSION__);
    std::cout << ",\"cplusplus\":" << __cplusplus
              << ",\"sizeof_wchar_t\":" << sizeof(wchar_t)
              << ",\"sizeof_wint_t\":" << sizeof(wint_t)
              << ",\"initial_effective_LC_CTYPE\":";
    WriteNullable(initialAvailable ? initial.c_str() : nullptr);
    std::cout << ",\"initial_mapping\":";
    WriteMapping();
    std::cout << ",\"input_utf16_units\":";
    WriteUnits(input);
#ifdef _WIN32
    // Read-only provenance from this process, rather than assuming which CRT
    // was selected from the compiler distribution or a system file listing.
    const auto module = GetModuleHandleW(L"ucrtbase.dll");
    wchar_t modulePath[32768] = {};
    const auto length = module ? GetModuleFileNameW(module, modulePath, 32768) : 0;
    std::cout << ",\"loaded_ucrtbase_module_path_utf16_units\":";
    if (length && length < 32768) {
        std::u16string path;
        for (DWORD i = 0; i < length; ++i) path += char16_t(modulePath[i]);
        WriteUnits(path);
    } else {
        std::cout << "null";
    }
#endif
    std::cout << ",\"expected_utf16_units\":";
    WriteUnits(expected);
    std::cout << ",\"cases\":[";
    const char* aliases[] = { "C.utf8", ".UTF8", "", "C" };
    bool infrastructureOkay = initialAvailable;
    for (std::size_t i = 0; i < 4; ++i) {
        if (i) std::cout << ',';
        std::cout << "{\"requested_alias\":";
        WriteBytes(aliases[i]);
        // Copy each returned string before another setlocale can overwrite it.
        const char* resetPointer = std::setlocale(LC_CTYPE, "C");
        const bool resetOkay = resetPointer != nullptr;
        const std::string reset = resetOkay ? resetPointer : "";
        std::cout << ",\"reset_C_return\":";
        WriteNullable(resetOkay ? reset.c_str() : nullptr);
        const char* resetEffectivePointer = std::setlocale(LC_CTYPE, nullptr);
        const bool resetEffectiveAvailable = resetEffectivePointer != nullptr;
        const std::string resetEffective = resetEffectiveAvailable ? resetEffectivePointer : "";
        std::cout << ",\"reset_effective_LC_CTYPE\":";
        WriteNullable(resetEffectiveAvailable ? resetEffective.c_str() : nullptr);
        infrastructureOkay = infrastructureOkay && resetOkay && resetEffective == "C";
        const char* selectedPointer = std::setlocale(LC_CTYPE, aliases[i]);
        const bool selected = selectedPointer != nullptr;
        const std::string selection = selected ? selectedPointer : "";
        std::cout << ",\"setlocale_return\":";
        WriteNullable(selected ? selection.c_str() : nullptr);
        std::cout << ",\"effective_LC_CTYPE\":";
        WriteNullable(std::setlocale(LC_CTYPE, nullptr));
        std::cout << ",\"mapping\":";
        WriteMapping();
        std::cout << '}';
    }
    std::cout << "],\"restore_initial_return\":";
    const char* restored = initialAvailable ? std::setlocale(LC_CTYPE, initial.c_str()) : nullptr;
    const bool restoredOkay = restored != nullptr;
    WriteNullable(restored);
    const char* finalPointer = std::setlocale(LC_CTYPE, nullptr);
    const bool finalAvailable = finalPointer != nullptr;
    const std::string finalLocale = finalAvailable ? finalPointer : "";
    std::cout << ",\"final_effective_LC_CTYPE\":";
    WriteNullable(finalAvailable ? finalLocale.c_str() : nullptr);
    infrastructureOkay = infrastructureOkay && restoredOkay && finalAvailable && finalLocale == initial;
    std::cout << ",\"diagnostic_completed\":" << (infrastructureOkay ? "true" : "false") << "}\n";
    // Alias rejection or a casing mismatch is evidence, not diagnostic failure.
    return infrastructureOkay && std::cout.good() ? 0 : 2;
}
