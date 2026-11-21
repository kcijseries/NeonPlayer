#!/usr/bin/env bash
# NeonPlayer setup. Safe to re-run any time (e.g. to pick up new dependencies).
cd "$(dirname "$(readlink -f "$0")")"
[ -d .venv ] || python -m venv .venv
.venv/bin/pip install --upgrade pip PyQt6 mutagen numpy
source "$PWD/install-pygame.sh"
install_pygame "$PWD/.venv/bin/python"
chmod +x run.sh neonplayer.py

# Application-menu launcher: starts without a terminal, with an icon
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/neonplayer.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=NeonPlayer
Comment=Cyberpunk album-grid music player
Exec="$PWD/run.sh"
Path=$PWD
Icon=$PWD/neonplayer.png
Terminal=false
Categories=AudioVideo;Audio;Player;
Keywords=music;player;flac;mp3;
DESKTOP
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 >/dev/null 2>&1

echo "Done. Find NeonPlayer in your application menu (or press Alt+Space and type 'neon')."
echo "From a terminal you can still use ./run.sh"
