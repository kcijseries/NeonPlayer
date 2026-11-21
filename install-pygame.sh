#!/usr/bin/env bash
# Install Pygame with optional AVX2 blitters on native x86-64 Linux.
# Pygame's AVX2 implementation uses SDL_HasAVX2() at runtime, so the
# optimized object is only selected on CPUs that actually support AVX2.
# Other CPUs use Pygame's normal implementation.

install_pygame() {
    local py="$1"
    local platform machine diagnostic

    "$py" -m pip install --upgrade pygame || return $?

    platform="$(uname -s 2>/dev/null || true)"
    machine="$(uname -m 2>/dev/null || true)"
    case "$platform:$machine" in
        Linux:x86_64|Linux:amd64|Linux:i?86)
            diagnostic="$("$py" -W always -c 'import pygame' 2>&1 || true)"
            if ! grep -qi 'system is avx2 capable but pygame was not built with support' <<< "$diagnostic"; then
                echo "Pygame SIMD check: no AVX2 rebuild needed."
                return 0
            fi

            echo "AVX2-capable CPU detected. Building Pygame's optional AVX2 blitter module..."
            echo "The AVX2 code is runtime-dispatched; CPUs without AVX2 retain the standard blitters."
            if PYGAME_DETECT_AVX2=1 "$py" -m pip install \
                --no-cache-dir --no-binary=pygame --force-reinstall pygame; then
                echo "Pygame built with optional AVX2 support."
            else
                echo "WARNING: Pygame's optional AVX2 build failed; keeping/reinstalling the standard portable wheel."
                "$py" -m pip install --no-cache-dir --only-binary=:all: --force-reinstall pygame || return $?
            fi
            ;;
        *)
            echo "Pygame: using the standard portable build for $platform/$machine."
            ;;
    esac
}
