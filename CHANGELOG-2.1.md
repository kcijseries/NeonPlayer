# NeonPlayer 2.1.0

## Playback and browsing
- Selecting another album while audio is playing stages that album without interrupting the active track.
- The album track list now automatically highlights and scrolls to the currently playing track when that track is present in the displayed album.
- The active-track highlight stays synchronized when a track is selected, skipped, played from the queue, or advanced automatically.

## Visualizer restoration (2.1.0)
- Removed the experimental alternate visualizer modes and restored the single classic segmented spectrum from the 2.0 release.
- Restored the original 44-bar cyan-to-magenta equalizer, 40 ms animation timer, 72% main display and short segmented reflection in the remaining 28%.
- Restored the original small 10-bar mini-player equalizer.
- Reverted the main and mini visualizers from QOpenGLWidget to ordinary QWidget painting. This avoids OpenGL child-framebuffer composition artefacts in the translucent player overlay on Wayland/KWin and returns to the original Qt backing-store path.
- Removed the experimental visualizer selector, click-to-cycle interaction, custom colour/sensitivity controls, GLSL renderer and PyOpenGL dependency. Existing unrelated player settings are unchanged.
- The FPS diagnostic remains opt-in with `NEONPLAYER_SHOW_FPS=1` and does not alter the normal visualization.

## 2.1.0 maintenance updates
- Added a first-run/library-scan progress dialog with a genuine folder-count percentage and a message explaining that the process may take some time.


### Library scan and artwork performance
- The scanned music library is now published to the interface as soon as folder discovery and basic metadata processing finish.
- Embedded artwork extraction, thumbnail generation and cache serialization continue in the scanner background thread.
- The progress dialog becomes non-modal once the library is ready, so playback can begin while artwork caching finishes.
- Existing thumbnail cache entries are reused; artwork is only extracted when a per-track thumbnail is missing.

### Library scan completion behaviour
- Keep the always-on-top library preparation dialog visible through artwork caching and final library-view construction.
- Defer building the potentially large library tile view until scanning and artwork caching have completed, avoiding a misleading early completion and ensuring the dialog closes only after the main window is ready.
- The preparation dialog remains non-modal and stays above the NeonPlayer window throughout the operation.

### Optional Pygame AVX2 blitters
- On native x86-64 Linux, the installer detects Pygame's missing-AVX2 warning and attempts a source build with `PYGAME_DETECT_AVX2=1`.
- Pygame's AVX2 blitters use SDL runtime feature detection (`SDL_HasAVX2`); machines without AVX2 use the standard blitters.
- If compilation is unavailable, installation falls back to the standard portable Pygame wheel. Other platforms and architectures retain the standard package.
