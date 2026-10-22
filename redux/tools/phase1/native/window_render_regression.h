// SPDX-License-Identifier: GPL-2.0-or-later
// External synthetic readback fixture. No game/actor/resource mutations.
#pragma once

#include "Streams/FileStream.h"
#include "ImageWriter.h"
#include "Interface.h"
#include "Video/Pixels.h"
#include "PluginMgr.h"
#include "Sprite2D.h"
#include "GUI/View.h"
#include "GUI/Window.h"
#include "GUI/WindowManager.h"
#include "Video/Video.h"

#include <cstdlib>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>

namespace WindowRenderFixture {
using namespace GemRB;

class Rectangle final : public View {
    Color color;
    void DrawSelf(const Region& drawFrame, const Region&) override
    {
        VideoDriver->DrawRect(drawFrame, color, true, BlitFlags::NONE);
    }
public:
    Rectangle(const Region& r, Color c) : View(r), color(c) {}
};

struct RestoreClip {
    Region saved = VideoDriver->GetScreenClip();
    ~RestoreClip() { VideoDriver->SetScreenClip(&saved, false); }
};

static Holder<Sprite2D> Background(unsigned alpha)
{
    constexpr int width = 160, height = 120;
    auto* pixels = static_cast<uint32_t*>(std::malloc(width * height * sizeof(uint32_t)));
    if (!pixels) throw std::runtime_error("Synthetic background allocation failed");
    for (int i = 0; i < width * height; ++i) pixels[i] = (alpha << 24) | 0x00203040;
    // Same malloc-to-CreateSprite ownership convention as MOSImporter.
    auto sprite = VideoDriver->CreateSprite(Region(0, 0, width, height), pixels, PixelFormat::ARGB32Bit());
    if (!sprite) throw std::runtime_error("Synthetic background sprite unavailable");
    return sprite;
}

static std::unique_ptr<Window> Make(unsigned alpha, bool alphaWindow, unsigned scale, bool old)
{
    auto window = std::make_unique<Window>(Region(0, 0, 160, 120), *core->GetWindowManager());
    window->SetFlags(Window::AlphaChannel, alphaWindow ? BitOp::OR : BitOp::NAND);
    window->SetBackground(Background(alpha));
    window->UseScaleBuffer(scale);
    window->AddSubviewInFrontOfView(new Rectangle(Region(130, 90, 15, 15), Color(0, 255, 0, 255)));
    window->AddSubviewInFrontOfView(new Rectangle(old ? Region(12, 30, 112, 36) : Region(12, 30, 24, 8),
        old ? Color(255, 0, 0, 255) : Color(0, 0, 255, 255)));
    return window;
}

static void Capture(Window& window, const std::string& directory, const std::string& name, const Region* clip = nullptr)
{
    VideoDriver->SetScreenClip(clip);
    // Exactly one draw. A second window screenshot could repaint and hide a
    // partial-clear defect, so read the returned buffer directly afterwards.
    const auto& buffer = window.DrawWithoutComposition();
    auto sprite = VideoDriver->GetScreenshot(Region(0, 0, 160, 120), buffer);
    if (!sprite || sprite->Frame.w != 160 || sprite->Frame.h != 120) throw std::runtime_error("Synthetic readback geometry differs");
    PluginHolder<ImageWriter> writer = MakePluginHolder<ImageWriter>(PLUGIN_IMAGE_WRITER_BMP);
    FileStream file;
    if (!writer || !file.Create(directory, name, IE_BMP_CLASS_ID)) throw std::runtime_error("Synthetic BMP creation failed");
    writer->PutImage(&file, sprite);
    std::ofstream rgba(directory + "/" + name + ".rgba", std::ios::binary);
    if (!rgba) throw std::runtime_error("Synthetic RGBA creation failed");
    // Canonical top-to-bottom RGBA avoids BMP padding/orientation/provider
    // differences and retains alpha, which RGB-only screenshots cannot prove.
    for (int y = 0; y < 120; ++y) for (int x = 0; x < 160; ++x) {
        const auto c = sprite->GetPixel(Point(x, y));
        const unsigned char bytes[] = {c.r, c.g, c.b, c.a};
        rgba.write(reinterpret_cast<const char*>(bytes), 4);
    }
    if (!rgba) throw std::runtime_error("Synthetic RGBA write failed");
}
}

static void WindowRenderRegression(const std::string& out)
{
    using namespace WindowRenderFixture;
    if (!core || !core->GetWindowManager() || !VideoDriver) throw std::runtime_error("Loaded engine/video required");
    RestoreClip restore;
    const std::string directory = out + "/window-render-regression";
    if (!std::filesystem::create_directory(directory)) throw std::runtime_error("Synthetic output must be new");
    std::ofstream report(directory + "/fixture.json");
    if (!report) throw std::runtime_error("Synthetic receipt unavailable");
    report << "{\"schema\":\"bg-redux-window-render-fixture/1\",\"width\":160,\"height\":120,"
        "\"rgba_bytes_per_capture\":76800,\"game_mutations_requested\":false,\"cases\":[";
    bool first = true;
    for (unsigned alpha : {202u, 255u}) for (bool alphaWindow : {false, true}) for (unsigned scale : {100u, 75u, 125u}) {
        const std::string name = "bg" + std::to_string(alpha) + "-alpha" + (alphaWindow ? "1" : "0") + "-scale" + std::to_string(scale);
        const std::string folder = directory + "/" + name;
        if (!std::filesystem::create_directory(folder)) throw std::runtime_error("Synthetic case output exists");
        auto window = Make(alpha, alphaWindow, scale, true);
        Capture(*window, folder, "old");
        // Retrieve the old rectangle through the ordinary public hierarchy;
        // pointer retained from the owned view is unnecessary after removal.
        auto* old = window->SubviewAt(Point(20, 40), true, true);
        if (!old || !dynamic_cast<Rectangle*>(old)) throw std::runtime_error("Synthetic old rectangle unreachable");
        if (!old->RemoveFromSuperview()) throw std::runtime_error("Synthetic removal failed");
        delete old;
        window->AddSubviewInFrontOfView(new Rectangle(Region(12, 30, 24, 8), Color(0, 0, 255, 255)));
        Capture(*window, folder, "removed-final");
        auto reference = Make(alpha, alphaWindow, scale, false);
        Capture(*reference, folder, "fresh-final");
        for (int i = 0; i < 3; ++i) {
            window->MarkDirty();
            Capture(*window, folder, "dirty-" + std::to_string(i));
        }
        // Unchanged semantics: a clipped repaint must retain the already
        // correct green sentinel and background outside this rectangle.
        const Region partial(8, 20, 60, 50);
        window->MarkDirty();
        Capture(*window, folder, "partial-dirty", &partial);
        window->MarkDirty();
        Capture(*window, folder, "full-after-partial");
        if (!first) report << ',';
        first = false;
        report << "{\"id\":\"" << name << "\",\"background_alpha\":" << alpha
            << ",\"window_alpha_channel\":" << (alphaWindow ? "true" : "false") << ",\"scale_percent\":" << scale
            << ",\"partial_clip\":[8,20,60,50],\"outside_sentinel\":[130,90,15,15],"
            "\"reference\":\"fresh-final.rgba\",\"must_equal_reference\":[\"removed-final.rgba\",\"dirty-0.rgba\","
            "\"dirty-1.rgba\",\"dirty-2.rgba\",\"partial-dirty.rgba\",\"full-after-partial.rgba\"],"
            "\"old_child_must_differ\":\"old.rgba\",\"comparison_status\":\"external-comparison-required\"}";
    }
    report << "],\"completed\":true,\"passed\":null}\n";
    if (!report) throw std::runtime_error("Synthetic receipt write failed");
}
