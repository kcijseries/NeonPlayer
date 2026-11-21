#!/usr/bin/env bash
# Build a portable NeonPlayer AppImage (x86_64).
#
# Needs: bash, curl, tar and an internet connection. No root, no Docker, no system Python.
# Result: NeonPlayer-x86_64.AppImage next to this script. Re-run it after changing the code.
#
# Optional env: BUILD_DIR (scratch space, ~1.5 GB; default ./.appimage-build), OUT_DIR (default: here)
set -euo pipefail

SRC="$(dirname "$(readlink -f "$0")")"
WORK="${BUILD_DIR:-$SRC/.appimage-build}"
OUT="${OUT_DIR:-$SRC}"
APPDIR="$WORK/NeonPlayer.AppDir"
PYMINOR=12

for f in neonplayer.py engine.py mpris.py gamepad.py i18n.py neonplayer.png fonts/neurofont.otf; do
    [ -f "$SRC/$f" ] || { echo "Missing $SRC/$f"; exit 1; }
done
[ -f "$SRC/skyline.png" ] || echo "Note: no skyline.png next to the script - the AppImage will use a plain gradient background."
mkdir -p "$WORK" "$OUT"

echo "==> 1/6 Portable Python 3.$PYMINOR"
if [ ! -x "$WORK/python/bin/python3" ]; then
    TAG=$(curl -fsSIL -o /dev/null -w '%{url_effective}' \
          https://github.com/astral-sh/python-build-standalone/releases/latest | sed 's#.*/tag/##')
    PYURL=$(curl -fsSL "https://github.com/astral-sh/python-build-standalone/releases/expanded_assets/$TAG" \
            | grep -o "href=\"[^\"]*cpython-3\.$PYMINOR\.[^\"]*x86_64-unknown-linux-gnu-install_only_stripped\.tar\.gz\"" \
            | head -1 | sed 's/href="//;s/"$//')
    [ -n "$PYURL" ] || { echo "Could not find a Python 3.$PYMINOR build in release $TAG"; exit 1; }
    curl -fL "https://github.com$PYURL" | tar -xz -C "$WORK"
fi

echo "==> 2/6 Installing PyQt6, mutagen, numpy and Pygame (optional runtime-dispatched AVX2)"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/share/neonplayer"
cp -a "$WORK/python" "$APPDIR/usr/python"
PY="$APPDIR/usr/python/bin/python3"
"$PY" -m pip install --no-cache-dir --no-warn-script-location -q PyQt6 mutagen numpy
source "$SRC/install-pygame.sh"
install_pygame "$PY"

echo "==> 3/6 Trimming unused parts"
SP="$APPDIR/usr/python/lib/python3.$PYMINOR/site-packages"
QT="$SP/PyQt6/Qt6"
# The app uses Qt Core, Gui, Widgets, DBus, Network and Multimedia (+ FFmpeg, ICU).
for m in Bluetooth Designer Help Nfc OpenGL OpenGLWidgets Positioning Qml Quick Quick3D QuickWidgets RemoteObjects Sensors \
         SerialPort SpatialAudio Sql StateMachine Test TextToSpeech WebChannel WebSockets Xml \
         MultimediaWidgets PrintSupport SvgWidgets; do
    rm -f "$SP/PyQt6/Qt$m".abi3.so "$SP/PyQt6/Qt$m".pyi
done
# ...but the FFmpeg audio plugin links Qt's Quick/Qml core, so those few libraries must stay.
KEEP=" libQt6Qml.so.6 libQt6QmlMeta.so.6 libQt6QmlModels.so.6 libQt6QmlWorkerScript.so.6 libQt6QmlCore.so.6 libQt6Quick.so.6 "
for f in "$QT"/lib/libQt6{Quick,Qml,Labs,Designer,Help,Bluetooth,Nfc,Positioning,RemoteObjects,Sensors,SerialPort,Sql,StateMachine,Test,TextToSpeech,WebChannel,WebSockets,Xml,SpatialAudio,PrintSupport,MultimediaQuick,MultimediaWidgets,SvgWidgets,EglFSDeviceIntegration,Pdf}*; do
    [ -e "$f" ] || continue
    case "$KEEP" in *" $(basename "$f") "*) continue ;; esac
    rm -f "$f"
done
rm -f "$QT"/plugins/imageformats/libqpdf.so
for d in assetimporters egldeviceintegrations geometryloaders help position printsupport qmllint qmlls \
         renderers renderplugins sceneparsers scxmldatamodel sensors sqldrivers texttospeech; do
    rm -rf "$QT/plugins/$d"
done
rm -f "$QT"/plugins/platforms/lib{qeglfs,qlinuxfb,qminimalegl,qvkkhrdisplay,qvnc}.so
rm -rf "$QT/qml" "$QT/qsci" "$QT/libexec" "$QT/bin" "$SP/PyQt6/bindings" "$SP/PyQt6/uic"
# keep only Qt's own translations for the UI languages (standard dialog buttons etc.)
if [ -d "$QT/translations" ]; then
    find "$QT/translations" -type f ! \( -name 'qtbase_de.qm' -o -name 'qtbase_ja.qm' -o -name 'qtbase_fr.qm' \
        -o -name 'qtbase_es.qm' -o -name 'qtbase_it.qm' -o -name 'qtbase_ko.qm' -o -name 'qtbase_ru.qm' \
        -o -name 'qtbase_pl.qm' -o -name 'qtbase_zh_CN.qm' \) -delete
fi
rm -rf "$SP"/pip "$SP"/pip-* "$SP"/pygame/{docs,examples,tests} "$SP"/numpy/{tests,f2py,_pyinstaller}
find "$SP/numpy" -type d -name tests -prune -exec rm -rf {} + 2>/dev/null || true
PYLIB="$APPDIR/usr/python/lib/python3.$PYMINOR"
rm -rf "$PYLIB"/{test,idlelib,tkinter,turtledemo,lib2to3,ensurepip} "$APPDIR/usr/python"/{include,share} \
       "$APPDIR/usr/python/lib"/{tcl*,tk*,itcl*,thread*,pkgconfig}
find "$APPDIR/usr" -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true

echo "==> 4/6 App files and launcher"
cp "$SRC"/{neonplayer.py,engine.py,mpris.py,gamepad.py,i18n.py,neonplayer.png} "$APPDIR/usr/share/neonplayer/"
cp -r "$SRC/fonts" "$APPDIR/usr/share/neonplayer/fonts"
[ -f "$SRC/skyline.png" ] && cp "$SRC/skyline.png" "$APPDIR/usr/share/neonplayer/"
"$PY" -m compileall -q "$APPDIR/usr" >/dev/null 2>&1       # AppImages are read-only: precompile

cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export APPDIR="${APPDIR:-$HERE}"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH PYTHONHOME
PY="$HERE/usr/python/bin/python3"
APP="$HERE/usr/share/neonplayer/neonplayer.py"

# Command-line flags (--help, --data-dir, --install-desktop ...) print to the terminal as usual.
case "${1:-}" in -*) exec "$PY" "$APP" "$@" ;; esac

# Started from the application menu / file manager (no terminal): log to the portable data folder.
if [ ! -t 1 ]; then
    if   [ -n "${NEONPLAYER_DATA:-}" ]; then D="$NEONPLAYER_DATA"
    elif [ -n "${APPIMAGE:-}" ];        then D="$(dirname "$APPIMAGE")/NeonPlayer-data"
    else D="$HOME/.local/share/NeonPlayer"; fi
    if mkdir -p "$D" 2>/dev/null; then
        exec "$PY" "$APP" "$@" > "$D/neonplayer.log" 2>&1
    fi
fi
exec "$PY" "$APP" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

cat > "$APPDIR/neonplayer.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=NeonPlayer
Comment=Cyberpunk album-grid music player
Exec=AppRun
Icon=neonplayer
Terminal=false
Categories=AudioVideo;Audio;Player;
Keywords=music;player;flac;mp3;
DESKTOP
cp "$SRC/neonplayer.png" "$APPDIR/neonplayer.png"
ln -sf neonplayer.png "$APPDIR/.DirIcon"

echo "==> 5/6 Checking the bundle"
export QT_QPA_PLATFORM=offscreen
"$APPDIR/AppRun" --data-dir
# every bundled Qt/FFmpeg/ICU library must be resolvable from inside the bundle
LIBS="$SP/PyQt6/Qt6/lib:$SP/pygame.libs:$SP/numpy.libs"
MISSING=$(find "$SP/PyQt6" "$SP/pygame" "$SP/numpy" -name '*.so*' -type f 2>/dev/null | while read -r f; do
              LD_LIBRARY_PATH="$LIBS" ldd "$f" 2>/dev/null | grep 'not found' | grep -E 'libQt6|libav|libsw|libicu' | sed "s|^|$(basename "$f"): |"
          done | sort -u || true)
if [ -n "$MISSING" ]; then echo "ERROR: bundled libraries are unresolved:"; echo "$MISSING"; exit 1; fi
APP_SRC="$APPDIR/usr/share/neonplayer" "$PY" - <<'CHECK'
import os, sys, glob
sys.path.insert(0, os.environ["APP_SRC"])
from PyQt6.QtWidgets import QApplication
from PyQt6.QtMultimedia import QMediaPlayer, QAudioBufferOutput
from PyQt6 import QtDBus, QtNetwork
import numpy, mutagen, pygame
app = QApplication([])
assert QMediaPlayer().isAvailable(), "Qt Multimedia backend (FFmpeg) failed to load - no audio would play"
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtCore import QTranslator, QLibraryInfo
fams = set()
for f in glob.glob(os.environ["APP_SRC"] + "/fonts/*.[ot]tf"):
    fid = QFontDatabase.addApplicationFont(f)
    assert fid >= 0, "font failed to load: " + f
    fams.update(QFontDatabase.applicationFontFamilies(fid))
need = {"Neuromax Cool Futuristic Gaming Logo", "Exo 2", "Noto Sans JP", "Noto Sans KR", "Noto Sans SC"}
assert need <= fams, "missing font families: %s" % (need - fams)
tdir = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
for loc in ("de", "ja", "fr", "es", "it", "ko", "ru", "pl", "zh_CN"):
    assert QTranslator().load("qtbase_" + loc, tdir), "Qt translation missing: " + loc
print("fonts OK:", sorted(fams), "| Qt dialog translations OK for 9 languages")
print("bundle OK: PyQt6 + Multimedia + DBus, numpy", numpy.__version__, "| pygame", pygame.version.ver)
CHECK
du -sh "$APPDIR" | sed 's/^/AppDir size: /'

echo "==> 6/6 Packing the AppImage"
TOOL="$WORK/appimagetool-x86_64.AppImage"
if [ ! -x "$TOOL" ]; then
    curl -fL -o "$TOOL" https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x "$TOOL"
fi
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$TOOL" --comp zstd "$APPDIR" "$OUT/NeonPlayer-x86_64.AppImage"
chmod +x "$OUT/NeonPlayer-x86_64.AppImage"
echo
echo "Built: $OUT/NeonPlayer-x86_64.AppImage ($(du -h "$OUT/NeonPlayer-x86_64.AppImage" | cut -f1))"
