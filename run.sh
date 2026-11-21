#!/usr/bin/env bash
# From a terminal: output is shown. From the app menu / file manager: output goes to neonplayer.log.
DIR="$(dirname "$(readlink -f "$0")")"
if [ -t 1 ]; then
    exec "$DIR/.venv/bin/python" "$DIR/neonplayer.py" "$@"
else
    exec "$DIR/.venv/bin/python" "$DIR/neonplayer.py" "$@" > "$DIR/neonplayer.log" 2>&1
fi
