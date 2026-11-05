#include "bridge_capture.h"

#include "bridge_frame_buffer.h"
#include "bridge_preview.h"

#include <android/native_window.h>
#include <android/native_window_jni.h>
#include <dlfcn.h>
#include <media/NdkImage.h>
#include <media/NdkImageReader.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <thread>

struct NativeCapturer {
    AImageReader *reader = nullptr;
    ANativeWindow *window = nullptr;
    AImageReader_ImageListener listener{};
    int width = 0;
    int height = 0;
};

static NativeCapturer *g_capturer = nullptr;
static std::atomic<int> g_captureFpsLimit{30};
static std::atomic<bool> g_capturerRunning{false};

using PFN_ANativeWindow_setFrameRate = int32_t (*)(ANativeWindow *, float, int8_t);

static void ApplyWindowFrameRate(ANativeWindow *window, int fps) {
    if (!window) {
        return;
    }
    static auto fn = reinterpret_cast<PFN_ANativeWindow_setFrameRate>(
            dlsym(RTLD_DEFAULT, "ANativeWindow_setFrameRate"));
    if (!fn) {
        return;
    }
    const float rate = (fps > 0 && fps < 60) ? static_cast<float>(fps) : 0.0f;
    // ANATIVEWINDOW_FRAME_RATE_COMPATIBILITY_DEFAULT = 0
    fn(window, rate, 0);
}

void SetCaptureFpsLimit(int fps) {
    const int normalized = (fps <= 0 || fps >= 60) ? 60 : (fps < 5 ? 5 : fps);
    g_captureFpsLimit.store(normalized, std::memory_order_relaxed);
    if (g_capturer && g_capturer->window) {
        ApplyWindowFrameRate(g_capturer->window, normalized);
    }
    LOGI("SetCaptureFpsLimit: %d FPS", normalized);
}

int GetCaptureFpsLimit() {
    return g_captureFpsLimit.load(std::memory_order_relaxed);
}

static void onImageAvailable(void *context, AImageReader *reader) {
    (void) context;

    if (!g_capturerRunning.load(std::memory_order_acquire)) {
        return;
    }

    const int fpsLimit = g_captureFpsLimit.load(std::memory_order_relaxed);
    if (fpsLimit > 0 && fpsLimit < 60) {
        static auto lastCaptureTime = std::chrono::steady_clock::now() - std::chrono::seconds(1);
        const auto targetInterval = std::chrono::microseconds(1000000 / fpsLimit);
        auto now = std::chrono::steady_clock::now();
        while (g_capturerRunning.load(std::memory_order_acquire) && (now - lastCaptureTime) < targetInterval) {
            auto remaining = std::chrono::duration_cast<std::chrono::microseconds>(targetInterval - (now - lastCaptureTime));
            std::this_thread::sleep_for(std::min(remaining, std::chrono::microseconds(4000)));
            now = std::chrono::steady_clock::now();
        }
        if (!g_capturerRunning.load(std::memory_order_acquire)) {
            return;
        }
        lastCaptureTime = now;
    }

    AImage *image = nullptr;
    if (AImageReader_acquireLatestImage(reader, &image) != AMEDIA_OK || !image) {
        return;
    }

    AHardwareBuffer *hb = nullptr;
    if (AImage_getHardwareBuffer(image, &hb) == AMEDIA_OK && hb) {
        WriteHardwareBufferToFrame(hb);
    }

    bool handedOver = false;
    if (IsPreviewEnabled()) {
        handedOver = DispatchPreview(image);
    }

    if (!handedOver) {
        AImage_delete(image);
    }
}

jobject SetupNativeCapturer(JNIEnv *env, int width, int height) {
    ReleaseNativeCapturer();
    InitFrameBuffers(width, height);

    g_capturer = new NativeCapturer();
    g_capturer->width = width;
    g_capturer->height = height;

    media_status_t status = AImageReader_newWithUsage(
            width, height, AIMAGE_FORMAT_RGBA_8888,
            AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN | AHARDWAREBUFFER_USAGE_GPU_SAMPLED_IMAGE, 3,
            &g_capturer->reader);
    if (status != AMEDIA_OK) {
        LOGE("AImageReader_newWithUsage failed: %d", status);
        delete g_capturer;
        g_capturer = nullptr;
        ReleaseFrameBuffers();
        return nullptr;
    }

    g_capturer->listener.context = g_capturer;
    g_capturer->listener.onImageAvailable = onImageAvailable;
    status = AImageReader_setImageListener(g_capturer->reader, &g_capturer->listener);
    if (status != AMEDIA_OK) {
        LOGE("SetupNativeCapturer: AImageReader_setImageListener failed: %d", status);
        AImageReader_delete(g_capturer->reader);
        delete g_capturer;
        g_capturer = nullptr;
        ReleaseFrameBuffers();
        return nullptr;
    }

    status = AImageReader_getWindow(g_capturer->reader, &g_capturer->window);
    if (status != AMEDIA_OK || !g_capturer->window) {
        LOGE("SetupNativeCapturer: AImageReader_getWindow failed: status=%d, window=%p",
             status, g_capturer->window);
        AImageReader_setImageListener(g_capturer->reader, nullptr);
        AImageReader_delete(g_capturer->reader);
        delete g_capturer;
        g_capturer = nullptr;
        ReleaseFrameBuffers();
        return nullptr;
    }

    g_capturerRunning.store(true, std::memory_order_release);
    ApplyWindowFrameRate(g_capturer->window, g_captureFpsLimit.load(std::memory_order_relaxed));
    return ANativeWindow_toSurface(env, g_capturer->window);
}

void ReleaseNativeCapturer() {
    g_capturerRunning.store(false, std::memory_order_release);
    DrainPreviewQueue();

    if (g_capturer) {
        if (g_capturer->reader) {
            AImageReader_setImageListener(g_capturer->reader, nullptr);
        }
        if (g_capturer->reader) {
            AImageReader_delete(g_capturer->reader);
        }

        delete g_capturer;
        g_capturer = nullptr;
    }

    ReleaseFrameBuffers();
}
