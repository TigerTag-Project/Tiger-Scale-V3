#pragma once
// LVGL custom allocator: PSRAM first, DRAM fallback.
// heap_caps_malloc(..., MALLOC_CAP_SPIRAM) returns null silently if PSRAM
// isn't available for some reason -- see CLAUDE.md's ps_malloc warning, same
// failure mode applies here. Falling through to plain malloc()/realloc()
// (ESP-IDF's default heap) avoids a null pointer reaching LVGL's internals,
// which was causing a boot crash-loop.

#include <stdlib.h>
#include "esp_heap_caps.h"

static inline void *lv_psram_malloc(size_t size) {
    void *p = heap_caps_malloc(size, MALLOC_CAP_SPIRAM);
    if (!p) p = malloc(size);
    return p;
}

static inline void *lv_psram_realloc(void *ptr, size_t size) {
    void *p = heap_caps_realloc(ptr, size, MALLOC_CAP_SPIRAM);
    if (!p) p = realloc(ptr, size);
    return p;
}

static inline void lv_psram_free(void *ptr) {
    heap_caps_free(ptr);
}
