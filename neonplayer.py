#!/usr/bin/env python3
"""NeonPlayer v2.1.0 - portable cyberpunk album-grid music player."""
import hashlib
import html
import json
import math
import os
import random
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import mutagen
from PyQt6.QtCore import (QEasingCurve, QParallelAnimationGroup, QPoint,
                          QPointF, QPropertyAnimation, QRect, QRectF, QSize,
                          QMimeData, Qt, QThread, QTimer, QUrl, pyqtSignal)
from PyQt6.QtGui import (QBrush, QColor, QCursor, QDrag, QFont, QFontMetrics, QIcon,
                         QImage, QKeySequence, QLinearGradient, QRadialGradient, QPainter,
                         QPainterPath, QPen, QPixmap, QPolygonF, QShortcut)
from PyQt6.QtCore import QLibraryInfo, QTranslator
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtWidgets import (QApplication, QButtonGroup, QFileDialog,
                             QGraphicsBlurEffect, QGraphicsDropShadowEffect,
                             QGraphicsOpacityEffect, QGraphicsPixmapItem,
                             QGraphicsScene, QGridLayout, QHBoxLayout, QInputDialog, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem,
                             QMainWindow, QMenu, QPushButton, QScrollArea,
                             QAbstractItemView, QSizeGrip, QSlider, QSplitter, QStyle, QStyledItemDelegate,
                             QToolTip, QVBoxLayout, QWidget, QDialog, QComboBox, QCheckBox, QProgressDialog)

APP_DIR = Path(__file__).resolve().parent     # code + bundled assets (read-only inside an AppImage)
sys.path.insert(0, str(APP_DIR))


def _find_data_dir():
    """Portable data folder (config, cache, playlists, custom background).

    NEONPLAYER_DATA if set; inside an AppImage: NeonPlayer-data/ next to the .AppImage file;
    otherwise the app folder itself (the venv / run.sh layout)."""
    env, appimage = os.environ.get("NEONPLAYER_DATA"), os.environ.get("APPIMAGE")
    if env:
        d = Path(env).expanduser()
    elif appimage:
        d = Path(appimage).resolve().parent / "NeonPlayer-data"
    else:
        return APP_DIR
    first = not d.exists()
    try:
        d.mkdir(parents=True, exist_ok=True)
        if not os.access(d, os.W_OK):
            raise OSError("not writable")
    except OSError as ex:       # e.g. the AppImage sits on a read-only drive
        d = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "NeonPlayer"
        print(f"NeonPlayer: portable data folder unusable ({ex}); using {d}", file=sys.stderr)
        d.mkdir(parents=True, exist_ok=True)
        return d
    if first and not env and appimage:      # one-time import of an older folder-based install
        old = Path(appimage).resolve().parent
        try:
            for name in ("config.json", "skyline.png"):
                if (old / name).is_file():
                    shutil.copy2(old / name, d / name)
            if (old / "cache").is_dir():
                shutil.copytree(old / "cache", d / "cache", dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns("now_cover_*", "*.tmp"))
        except OSError as ex:
            print("NeonPlayer: could not import previous data:", ex, file=sys.stderr)
    return d


DATA_DIR = _find_data_dir()
import engine as eng          # noqa: E402  (audio engine: crossfade, gapless, FFT)
import mpris                  # noqa: E402  (media keys / Plasma widget)
import i18n                   # noqa: E402  (translations + language/font table)
from i18n import tr           # noqa: E402
try:
    import gamepad            # noqa: E402  (controller support, needs pygame)
except Exception:
    gamepad = None
MIME = "application/x-neonplayer-tracks"
UR = Qt.ItemDataRole.UserRole
CONFIG = DATA_DIR / "config.json"
CACHE_DIR = DATA_DIR / "cache"
THUMBS = CACHE_DIR / "thumbs"
CACHE_FILE = CACHE_DIR / "library.json"
CACHE_V = 3
SKYLINE = next((p for p in (DATA_DIR / "skyline.png", APP_DIR / "skyline.png") if p.exists()),
               APP_DIR / "skyline.png")     # drop your own skyline.png into the data folder to override

AUDIO_EXT = {".mp3", ".wav", ".flac", ".ogg", ".oga", ".opus", ".m4a",
             ".aac", ".wma", ".aiff", ".aif", ".ape"}
IMG_NAMES = ("cover", "folder", "front", "album", "artwork")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
TILE = 150
CYAN, PINK, PURPLE, YELLOW, MAGENTA = "#00e5ff", "#ff2a9d", "#7b2ff7", "#fcee0a", "#ff00c8"
NEON = [CYAN, PINK, PURPLE, YELLOW, MAGENTA]

MODES = {"folders": "FOLDERS", "artists": "ARTISTS", "albums": "ALBUMS",
         "genres": "GENRES", "playlists": "PLAYLISTS", "favorites": "FAVORITES",
         "recent": "RECENTLY ADDED"}
NAV = [("folders", "▤", "Folders"), ("artists", "☺", "Artists"),
       ("albums", "◉", "Albums"), ("genres", "▥", "Genres"),
       ("playlists", "☰", "Playlists"), ("favorites", "♥", "Favorites"),
       ("recent", "◔", "Recently Added")]

STYLE = f"""
QMainWindow {{background:#06041a;}}
QLabel {{color:#e8e6ff;}}
QLabel#cap {{color:{CYAN}; font-size:11px; font-weight:bold;}}
QLabel#msg {{color:#9b6bff; font-size:18px;}}
QLabel#badge {{color:{PINK}; border:2px solid {PINK}; border-radius:9px; padding:6px 18px;
    font-size:15px; font-weight:bold; background:rgba(255,42,157,28);}}
QLabel#ptitle {{color:#fff; font-size:30px; font-weight:bold;}}
QLabel#partist {{color:#e8e6ff; font-size:22px;}}
QLabel#palbum {{color:#e8e6ff; font-size:19px;}}
QLabel#pmeta {{color:#cfe9ff; font-size:14px;}}
QLabel#time {{color:#fff; font-size:18px;}}
QLabel#chip {{color:{CYAN}; border:1px solid {CYAN}; border-radius:7px; padding:5px 10px;
    font-size:14px; font-weight:bold; background:rgba(0,229,255,30);}}
QPushButton {{background:#1a0b33; color:{CYAN}; border:1px solid {PURPLE};
             padding:6px 14px; border-radius:3px;}}
QPushButton:hover {{border-color:{PINK}; color:{YELLOW};}}
QPushButton#nav {{text-align:left; padding:0 18px; font-size:15px; color:#d8ecff;
    background:transparent; border:none; border-bottom:1px solid rgba(0,229,255,70);
    border-radius:0;}}
QPushButton#nav:hover {{color:{YELLOW};}}
QPushButton#nav:checked {{color:#fff; border:2px solid {PINK}; border-radius:10px;
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba(255,42,157,120),stop:1 rgba(123,47,247,70));}}
QPushButton#win {{background:transparent; border:none; color:#fff; font-size:18px; padding:2px 10px;}}
QPushButton#win:hover {{color:{PINK};}}
QPushButton#vt {{background:transparent; border:1px solid transparent; border-radius:6px; padding:4px;}}
QPushButton#vt:checked {{border:1px solid {PINK};}}
QPushButton#back {{padding:4px 12px; font-size:14px; background:rgba(26,11,51,200);}}
QPushButton#rail {{border:2px solid rgba(0,229,255,150); border-radius:12px; font-size:26px;
    color:{CYAN}; background:rgba(0,229,255,15); padding:0;}}
QPushButton#rail:checked {{border-color:{PINK}; color:{PINK}; background:rgba(255,42,157,45);}}
QPushButton#rail:hover {{color:{YELLOW};}}
QPushButton#tbtn {{border:none; background:transparent; font-size:26px; color:{CYAN}; padding:0;}}
QPushButton#tbtn:checked {{color:{PINK};}}
QPushButton#tbtn:hover {{color:{YELLOW};}}
QLineEdit#search {{background:rgba(0,16,40,200); border:1px solid {CYAN}; border-radius:15px;
    padding:6px 12px; color:#fff; selection-background-color:{PINK};}}
QScrollArea, QScrollArea > QWidget > QWidget {{background:transparent; border:none;}}
QScrollBar:vertical {{background:transparent; width:10px; margin:4px;}}
QScrollBar::handle:vertical {{background:{PINK}; border-radius:4px; min-height:30px;}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{height:0;}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{background:transparent;}}
QWidget#overlay {{background:rgba(6,2,18,140);}}
QListWidget {{background:transparent; border:none; outline:none;}}
QSlider::groove:horizontal {{height:5px; background:rgba(123,47,247,90); border-radius:2px;}}
QSlider::sub-page:horizontal {{background:{PINK}; border-radius:2px;}}
QSlider::handle:horizontal {{background:#fff; border:3px solid {PINK}; width:12px; margin:-8px 0;
    border-radius:9px;}}
QDialog {{background:#12062e;}}
QLabel#dtitle {{color:#fff; font-size:14px; font-weight:bold;}}
QLabel#dartist {{color:#cfe9ff; font-size:12px;}}
QLabel#chip2 {{color:{YELLOW}; border:1px solid {YELLOW}; border-radius:7px; padding:3px 8px;
    font-size:12px; font-weight:bold; background:rgba(252,238,10,25);}}
QPushButton#navt {{text-align:left; padding:0 18px; font-size:15px; color:#d8ecff;
    background:transparent; border:none; border-bottom:1px solid rgba(0,229,255,70); border-radius:0;}}
QPushButton#navt:hover {{color:{YELLOW};}}
QPushButton#navt:checked {{color:{CYAN};}}
QDialog {{background:#12062e;}}
QLineEdit {{background:rgba(0,16,40,230); border:1px solid {CYAN}; color:#fff; padding:4px 8px; border-radius:4px;}}
QLabel#sec {{color:{CYAN}; font-size:12px; font-weight:bold; letter-spacing:2px;}}
QPushButton#mini {{padding:2px 6px; font-size:11px; border-radius:9px;}}
QSplitter::handle {{background:rgba(255,42,157,130); margin:3px 70px; border-radius:2px;}}
QMenu {{background:#12062e; color:#e8e6ff; border:1px solid {PURPLE}; padding:4px;}}
QMenu::item {{padding:8px 24px;}}
QMenu::item:selected {{background:#2a0f55; color:{YELLOW};}}
QToolTip {{background:#12062e; color:{CYAN}; border:1px solid {PINK};}}
"""


# ---------- fonts & translation plumbing ----------
FONT_DIRS = (DATA_DIR / "fonts", APP_DIR / "fonts")      # NeonPlayer-data/fonts overrides bundled ones
FONT_FILES = {"neuro": ["neurofont.otf"], "exo2": ["Exo2-Regular.ttf", "Exo2-Bold.ttf"],
              "jp": ["NotoSansJP-Regular.otf", "NotoSansJP-Bold.otf"],
              "kr": ["NotoSansKR-Regular.otf", "NotoSansKR-Bold.otf"],
              "sc": ["NotoSansSC-Regular.otf", "NotoSansSC-Bold.otf"]}
FAMILY = {}          # logical name -> installed family name
_REG = []            # (widget, setter, key, prefix, upper) for static texts, re-applied on language change
_QT_TR = None


def load_fonts():
    for key, names in FONT_FILES.items():
        for n in names:
            p = next((d / n for d in FONT_DIRS if (d / n).is_file()), None)
            if p is None:
                continue
            fid = QFontDatabase.addApplicationFont(str(p))
            fams = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
            if fams:
                FAMILY.setdefault(key, fams[0])


def apply_font(app, code):
    fams = [FAMILY[k] for k in i18n.FONT_CHAIN.get(code, ["neuro"]) if k in FAMILY]
    if fams:
        f = QFont()
        f.setFamilies(fams)
        f.setPointSize(10)
        app.setFont(f)


def init_i18n(app, code, fonts=True):
    """Select language, load fonts, install Qt's own translations (standard dialog buttons)."""
    global _QT_TR
    i18n.set_lang(code)
    if fonts:
        load_fonts()
    apply_font(app, i18n.lang())
    if _QT_TR is not None:
        app.removeTranslator(_QT_TR)
        _QT_TR = None
    if i18n.lang() != "en":
        t = QTranslator(app)
        loc = "zh_CN" if i18n.lang() == "zh" else i18n.lang()
        if t.load(f"qtbase_{loc}", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
            app.installTranslator(t)
            _QT_TR = t
    app.setStyleSheet(STYLE)          # re-polish so every widget picks up the new font


def treg(widget, key, method="setText", prefix="", upper=False):
    """Set a translated text now and remember it so a language change can refresh it."""
    _REG.append((widget, method, key, prefix, upper))
    _apply_reg(_REG[-1])
    return widget


def _apply_reg(e):
    w, method, key, prefix, upper = e
    s = tr(key)
    getattr(w, method)(prefix + (s.upper() if upper else s))


def retranslate_all():
    for e in list(_REG):
        try:
            _apply_reg(e)
        except RuntimeError:              # widget already destroyed
            _REG.remove(e)


def mode_label(key):
    labels = {k: lbl for k, _, lbl in NAV}
    return tr(labels[key]).upper() if key in labels else str(key).upper()


# ---------- helpers ----------
def read_tags(path):
    try:
        f = mutagen.File(path, easy=True)
        t = f.tags if f else None
        if t:
            def g(*keys):
                for k in keys:
                    try:
                        v = t.get(k)
                    except Exception:
                        v = None
                    if v:
                        return str(v[0]).strip()
                return ""
            return g("albumartist", "artist"), g("genre")
    except Exception:
        pass
    return "", ""


def track_info(path, artist, album):
    d = {"path": path, "title": Path(path).stem, "artist": artist, "album": album, "length": 0.0,
         "sr": 0, "bits": 0, "bitrate": 0, "vbr": False, "br_mode": "",
         "codec": Path(path).suffix[1:].upper(), "lyrics": "", "rg_track": None, "rg_album": None, "rg_peak": None, "rg_album_peak": None}
    try:
        f = mutagen.File(path, easy=True)
        if f is not None:
            i = f.info
            d["length"] = float(getattr(i, "length", 0) or 0)
            d["sr"] = int(getattr(i, "sample_rate", 0) or 0)
            d["bits"] = int(getattr(i, "bits_per_sample", 0) or 0)
            d["bitrate"] = int(getattr(i, "bitrate", 0) or 0)
            # VBR is available on common Mutagen MPEG/Ogg/MP4 info objects.
            mode = str(getattr(i, "bitrate_mode", "") or "").upper().split(".")[-1]
            d["br_mode"] = mode if mode in ("CBR", "VBR", "ABR") else ""
            d["vbr"] = d["br_mode"] == "VBR"
            t = f.tags
            if t:
                for key, tag in (("title", "title"), ("artist", "artist"), ("album", "album")):
                    v = t.get(tag)
                    if v and str(v[0]).strip(): d[key] = str(v[0]).strip()
                # Embedded synchronized/unsynchronized lyrics and ReplayGain tags.
                for k in ("lyrics", "unsyncedlyrics", "USLT::", "©lyr"):
                    try:
                        v = t.get(k)
                        if v:
                            item = v[0] if isinstance(v, (list, tuple)) else v
                            d["lyrics"] = str(getattr(item, "text", item)); break
                    except Exception: pass
                for key, names in (("rg_track", ("replaygain_track_gain", "TXXX:REPLAYGAIN_TRACK_GAIN")),
                                   ("rg_album", ("replaygain_album_gain", "TXXX:REPLAYGAIN_ALBUM_GAIN")),
                                   ("rg_peak", ("replaygain_track_peak", "TXXX:REPLAYGAIN_TRACK_PEAK")),
                                   ("rg_album_peak", ("replaygain_album_peak", "TXXX:REPLAYGAIN_ALBUM_PEAK"))):
                    for name in names:
                        try:
                            val = t.get(name)
                            if val:
                                raw = str(val[0] if isinstance(val, (list, tuple)) else val)
                                import re
                                m = re.search(r"[-+]?\d+(?:\.\d+)?", raw)
                                if m: d[key] = float(m.group())
                                break
                        except Exception: pass
    except Exception:
        pass
    return d


def embedded_art(path):
    try:
        f = mutagen.File(path)
        if f is None:
            return None
        if getattr(f, "pictures", None):
            return f.pictures[0].data
        tags = f.tags
        if tags is None:
            return None
        if hasattr(tags, "getall"):
            apic = tags.getall("APIC")
            if apic:
                return apic[0].data
        if "covr" in tags:
            return bytes(tags["covr"][0])
    except Exception:
        pass
    return None


def load_cover(folder, tracks):
    try:
        names = {n.lower(): n for n in os.listdir(folder)}
        for base in IMG_NAMES:
            for ext in IMG_EXT:
                if base + ext in names:
                    img = QImage(os.path.join(folder, names[base + ext]))
                    if not img.isNull():
                        return img
    except OSError:
        pass
    for t in tracks[:3]:
        data = embedded_art(os.path.join(folder, t))
        img = QImage()
        if data and img.loadFromData(data):
            return img
    return QImage()


def placeholder(size=300):
    pm = QPixmap(size, size)
    p = QPainter(pm)
    g = QLinearGradient(0, 0, size, size)
    g.setColorAt(0, QColor(PURPLE))
    g.setColorAt(1, QColor(MAGENTA))
    p.fillRect(pm.rect(), g)
    p.setPen(QColor(YELLOW))
    p.setFont(QFont("sans", size // 3))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
    p.end()
    return pm


def fit(ar, box):
    w = box.width()
    h = w / ar
    if h > box.height():
        h = box.height()
        w = h * ar
    r = QRect(0, 0, max(1, int(w)), max(1, int(h)))
    r.moveCenter(box.center())
    return r


def fmt(ms):
    s = int(ms) // 1000
    return f"{s // 60}:{s % 60:02d}"


def cover_scaled(pm, size):
    s = pm.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                  Qt.TransformationMode.SmoothTransformation)
    return s.copy((s.width() - size.width()) // 2, (s.height() - size.height()) // 2,
                  size.width(), size.height())


def make_blur(pm, width=480, radius=9):
    small = pm.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)
    scene = QGraphicsScene()
    item = QGraphicsPixmapItem(small)
    eff = QGraphicsBlurEffect()
    eff.setBlurRadius(radius)
    eff.setBlurHints(QGraphicsBlurEffect.BlurHint.QualityHint)
    item.setGraphicsEffect(eff)
    scene.addItem(item)
    out = QImage(small.size(), QImage.Format.Format_ARGB32_Premultiplied)
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    scene.render(p, QRectF(out.rect()), QRectF(small.rect()))
    p.end()
    c = int(radius * 1.6)
    return QPixmap.fromImage(out.copy(c, c, out.width() - 2 * c, out.height() - 2 * c))


def chamfer(rect, c):
    r = QRectF(rect)
    path = QPainterPath()
    path.moveTo(r.left() + c, r.top())
    path.lineTo(r.right() - c, r.top())
    path.lineTo(r.right(), r.top() + c)
    path.lineTo(r.right(), r.bottom() - c)
    path.lineTo(r.right() - c, r.bottom())
    path.lineTo(r.left() + c, r.bottom())
    path.lineTo(r.left(), r.bottom() - c)
    path.lineTo(r.left(), r.top() + c)
    path.closeSubpath()
    return path


def glow(p, path, rect, c1, c2, core=2.0):
    """Stroke a path with a soft neon glow in a two-color gradient."""
    def pen(alpha, width):
        g = QLinearGradient(rect.topLeft(), rect.bottomRight())
        a, b = QColor(c1), QColor(c2)
        a.setAlpha(alpha)
        b.setAlpha(alpha)
        g.setColorAt(0, a)
        g.setColorAt(1, b)
        return QPen(QBrush(g), width)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for width, alpha in ((12, 18), (7, 40), (4, 75)):
        p.setPen(pen(alpha, width))
        p.drawPath(path)
    p.setPen(pen(255, core))
    p.drawPath(path)


def icon_search():
    pm = QPixmap(18, 18)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(CYAN), 2))
    p.drawEllipse(2, 2, 9, 9)
    p.drawLine(10, 10, 16, 16)
    p.end()
    return QIcon(pm)


def icon_view(kind):
    def draw(color):
        pm = QPixmap(26, 26)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(color))
        if kind == "grid":
            for i in range(3):
                for j in range(3):
                    p.drawRoundedRect(QRectF(2 + i * 8, 2 + j * 8, 6, 6), 1.5, 1.5)
        else:
            for j in range(3):
                p.drawRoundedRect(QRectF(2, 3 + j * 8, 5, 5), 1.5, 1.5)
                p.drawRoundedRect(QRectF(10, 4 + j * 8, 14, 3), 1.5, 1.5)
        p.end()
        return pm
    ic = QIcon()
    ic.addPixmap(draw(PINK), QIcon.Mode.Normal, QIcon.State.On)
    ic.addPixmap(draw(CYAN), QIcon.Mode.Normal, QIcon.State.Off)
    return ic


@dataclass(eq=False)
class Node:
    """A folder (album or container) or a synthetic group (artist/genre)."""
    path: str
    name: str
    tracks: list
    children: list
    img: QImage
    artist: str = ""
    genre: str = ""
    mtime: float = 0.0
    dmtime: float = 0.0
    fresh: bool = False
    hit: int = -1      # index of the track that matched a search


# ---------- cache ----------
def thumb_name(path):
    return hashlib.md5(path.encode("utf-8", "surrogateescape")).hexdigest()[:16] + ".jpg"


def node_to_dict(n):
    return {"p": n.path, "n": n.name, "t": n.tracks, "a": n.artist, "g": n.genre,
            "m": n.mtime, "d": n.dmtime, "th": not n.img.isNull(),
            "c": [node_to_dict(c) for c in n.children]}


def dict_to_node(d):
    img = QImage(str(THUMBS / thumb_name(d["p"]))) if d.get("th") else QImage()
    return Node(d["p"], d["n"], d["t"], [dict_to_node(c) for c in d["c"]],
                img, d["a"], d["g"], d["m"], d["d"])


def track_thumb_name(path):
    return "track_" + thumb_name(path)


def cached_track_cover(path, fallback=None):
    """Return per-file artwork, falling back to the containing album image."""
    f = THUMBS / track_thumb_name(path)
    if f.exists():
        im = QImage(str(f))
        if not im.isNull():
            return im
    data = embedded_art(path)
    im = QImage()
    if data and im.loadFromData(data):
        im = im.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio,
                       Qt.TransformationMode.SmoothTransformation)
        try:
            THUMBS.mkdir(parents=True, exist_ok=True)
            im.save(str(f), "JPG", 90)
        except OSError:
            pass
        return im
    return fallback if fallback is not None and not fallback.isNull() else QImage()


def save_cache(root, lib, progress=None):
    """Write album/track thumbnails and the library index, reporting real work."""
    THUMBS.mkdir(parents=True, exist_ok=True)
    nodes = []
    def gather(n):
        nodes.append(n)
        for child in n.children:
            gather(child)
    gather(root)
    # Count every thumbnail candidate, including cached items, so progress is
    # deterministic and reaches 100% only after all candidates were examined.
    total = sum(1 + len(n.tracks) for n in nodes)
    done = 0
    def report(label):
        if progress:
            progress(done, max(1, total), label)
    report("Preparing artwork thumbnails…")
    for n in nodes:
        f = THUMBS / thumb_name(n.path)
        if not n.img.isNull() and (n.fresh or not f.exists()):
            n.img.save(str(f), "JPG", 88)
        done += 1
        report("Caching album artwork…")
        for track in n.tracks:
            full = os.path.join(n.path, track)
            tf = THUMBS / track_thumb_name(full)
            if not tf.exists():
                data = embedded_art(full)
                im = QImage()
                if data and im.loadFromData(data):
                    im = im.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
                elif not n.img.isNull():
                    im = n.img
                if not im.isNull():
                    im.save(str(tf), "JPG", 90)
            done += 1
            report("Caching track artwork and thumbnails…")
        n.fresh = False
    # Prune orphaned thumbnails after a complete tree has been serialized.
    live = set()
    def collect(n):
        live.add(thumb_name(n.path))
        live.update(track_thumb_name(os.path.join(n.path, t)) for t in n.tracks)
        for c in n.children: collect(c)
    collect(root)
    for f in THUMBS.glob("*.jpg"):
        if f.name not in live:
            try: f.unlink()
            except OSError: pass
    tmp = CACHE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"v": CACHE_V, "lib": lib, "tree": node_to_dict(root)}))
    os.replace(tmp, CACHE_FILE)
    if progress:
        progress(max(1, total), max(1, total), "Finishing library cache…")


def load_cache_json(lib):
    try:
        data = json.loads(CACHE_FILE.read_text())
        if data.get("v") == CACHE_V and data.get("lib") == lib:
            return data["tree"]
    except Exception:
        pass
    return None


class CacheLoader(QThread):
    done = pyqtSignal(object)

    def __init__(self, tree):
        super().__init__()
        self.tree = tree

    def run(self):
        try:
            self.done.emit(dict_to_node(self.tree))
        except Exception:
            self.done.emit(None)


class Scanner(QThread):
    """Incremental scan, then build artwork thumbnails in the background."""
    tree_ready = pyqtSignal(object, bool)
    done = pyqtSignal(object, bool)
    count = pyqtSignal(int)
    total = pyqtSignal(int)
    cache_progress = pyqtSignal(int, int, str)

    def __init__(self, root, old):
        super().__init__()
        self.root = root
        self.old = old
        self.n = 0
        self.changed = False
        self.cache_error = ""

    def build(self, folder):
        try:
            entries = sorted(os.scandir(folder), key=lambda e: e.name.casefold())
        except OSError:
            return None
        tracks, subdirs, mt = [], [], 0.0
        self.n += 1
        self.count.emit(self.n)
        for e in entries:
            if e.name.startswith("."):
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    subdirs.append(e.path)
                elif os.path.splitext(e.name)[1].lower() in AUDIO_EXT:
                    tracks.append(e.name)
                    mt = max(mt, e.stat().st_mtime)
            except OSError:
                continue
        children = [c for c in map(self.build, subdirs) if c]
        if not tracks and not children:
            return None
        try:
            dm = os.stat(folder).st_mtime
        except OSError:
            dm = 0.0
        old = self.old.get(folder)
        if old and old.dmtime == dm and old.tracks == tracks and old.mtime == mt:
            img, artist, genre, fresh = old.img, old.artist, old.genre, False
        else:
            self.changed = fresh = True
            img = load_cover(folder, tracks)
            if not img.isNull():
                img = img.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
            else:
                for c in children:
                    if not c.img.isNull():
                        img = c.img
                        break
            artist, genre = read_tags(os.path.join(folder, tracks[0])) if tracks else ("", "")
        if not old or {c.path for c in old.children} != {c.path for c in children}:
            self.changed = True
        return Node(folder, os.path.basename(folder) or folder, tracks, children,
                    img, artist, genre, mt, dm, fresh)

    def run(self):
        # Count directories first so the progress percentage reflects real work.
        # The actual scan remains in this worker thread; the GUI stays responsive.
        folder_total = 0
        for base, dirs, _files in os.walk(self.root):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            folder_total += 1
        self.total.emit(max(1, folder_total))
        root = self.build(self.root)
        changed = self.changed or root is None
        # Publish the usable library as soon as folder/track discovery and basic
        # metadata are complete. Artwork extraction, thumbnail generation and
        # cache serialization continue in this worker thread afterwards.
        self.tree_ready.emit(root, changed)
        if root is not None and (self.changed or not CACHE_FILE.exists()):
            try:
                save_cache(root, self.root,
                           lambda done, total, label: self.cache_progress.emit(done, total, label))
            except Exception as ex:
                self.cache_error = str(ex)
                print("NeonPlayer: could not save cache:", ex, file=sys.stderr)
        self.done.emit(root, changed)


# ---------- widgets ----------
class Central(QWidget):
    """Window background: skyline image, neon outer frame."""
    resized = pyqtSignal()

    def __init__(self, src, blur_src):
        super().__init__()
        self.src, self.blur_src = src, blur_src
        self.bg_sharp = self.bg_blur = None

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.src is not None and self.width() > 0 and self.height() > 0:
            self.bg_sharp = cover_scaled(self.src, self.size())
            self.bg_blur = cover_scaled(self.blur_src, self.size())
        self.resized.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.bg_sharp is not None:
            p.drawPixmap(0, 0, self.bg_sharp)
            p.fillRect(self.rect(), QColor(2, 2, 14, 60))
        else:
            g = QLinearGradient(0, 0, 0, self.height())
            g.setColorAt(0, QColor("#05031a"))
            g.setColorAt(1, QColor("#2c0a4e"))
            p.fillRect(self.rect(), g)
        rect = QRectF(self.rect()).adjusted(7, 7, -7, -7)
        path = QPainterPath()
        path.addRoundedRect(rect, 18, 18)
        glow(p, path, rect, CYAN, MAGENTA, 2.5)


class Panel(QWidget):
    """Frosted-glass panel: blurred, darkened slice of the skyline behind it."""

    def __init__(self, c1, c2, bgc, radius=14):
        super().__init__()
        self.c1, self.c2, self.bgc, self.radius = c1, c2, bgc, radius

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(7, 7, -7, -7)
        path = QPainterPath()
        path.addRoundedRect(rect, self.radius, self.radius)
        bg = self.bgc.bg_blur
        if bg is not None:
            p.save()
            p.setClipPath(path)
            off = self.mapTo(self.bgc, QPoint(0, 0))
            p.drawPixmap(self.rect(), bg, QRect(off, self.size()))
            p.fillPath(path, QColor(2, 3, 18, 150))
            p.restore()
        else:
            p.fillPath(path, QColor(4, 8, 28, 190))
        glow(p, path, rect, self.c1, self.c2, 2.0)


class Frame(QWidget):
    """Chamfered neon frame (player screen)."""

    def __init__(self, c1, c2, cut=20, fill=190, parent=None):
        super().__init__(parent)
        self.c1, self.c2, self.cut, self.fill = c1, c2, cut, fill

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        path = chamfer(rect, self.cut)
        if self.fill:
            p.fillPath(path, QColor(4, 8, 28, self.fill))
        glow(p, path, rect, self.c1, self.c2, 2.2)


class Logo(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(360, 62)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        f = QFont(FAMILY.get("neuro", "sans"), 24)
        f.setBold(True)
        f.setItalic(True)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        path = QPainterPath()
        path.addText(6, 34, f, "NEON PLAYER")
        for width, alpha in ((9, 30), (4, 70)):
            c = QColor(PINK)
            c.setAlpha(alpha)
            p.strokePath(path, QPen(c, width))
        g = QLinearGradient(0, 0, 250, 0)
        g.setColorAt(0, QColor(PINK))
        g.setColorAt(0.5, QColor("#c13cff"))
        g.setColorAt(1, QColor(CYAN))
        p.fillPath(path, QBrush(g))
        x = 6 + QFontMetrics(f).horizontalAdvance("NEON PLAYER") + 8
        f2 = QFont(FAMILY.get("neuro", "sans"), 11)
        f2.setBold(True)
        p.setFont(f2)
        p.setPen(QColor(CYAN))
        p.drawText(int(x), 30, "v2.0")
        p.setFont(QFont(FAMILY.get("jp", "sans"), 9))
        p.setPen(QColor("#e8e6ff"))
        p.drawText(8, 54, "ネオンプレイヤー")
        rnd = random.Random(5)
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(16):
            hgt = rnd.randint(4, 18)
            p.setBrush(QColor(PINK if i % 3 else MAGENTA))
            p.drawRect(QRectF(210 + i * 6, 56 - hgt, 4, hgt))


class DragBar(QWidget):
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(10, 4, -10, -4), 14, 14)
        p.fillPath(path, QColor(3, 3, 20, 150))

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            h = self.window().windowHandle()
            if h:
                h.startSystemMove()

    def mouseDoubleClickEvent(self, e):
        self.window().toggle_max()


class PulseButton(QPushButton):
    """Sidebar button that glows/pulses while music is playing."""

    def __init__(self, text):
        super().__init__(text)
        self.pulse, self.phase = False, 0.0
        self._last_tick = time.monotonic()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.setInterval(16)  # ~60 Hz target; actual rate depends on rendering load
        self.timer.timeout.connect(self.tick)

    def set_pulse(self, on):
        self.pulse = on
        if on:
            self._last_tick = time.monotonic()
            self.timer.start()
        else:
            self.timer.stop()
        self.update()

    def tick(self):
        now = time.monotonic()
        dt = min(0.05, max(0.0, now - self._last_tick))
        self._last_tick = now
        # Keep the old 40 ms animation speed while allowing smooth 60 Hz updates.
        self.phase += 0.22 * (dt / 0.040)
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        if not self.pulse:
            return
        k = 0.5 + 0.5 * math.sin(self.phase)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        p.setBrush(QColor(255, 42, 157, int(25 + 55 * k)))
        p.setPen(QPen(QColor(255, 42, 157, int(40 + 60 * k)), 7))
        p.drawRoundedRect(r, 10, 10)
        p.setPen(QPen(QColor(255, 120, 200, int(110 + 145 * k)), 2))
        p.drawRoundedRect(r, 10, 10)


class Scroller(QScrollArea):
    resized = pyqtSignal()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.resized.emit()


class CoverBox(QWidget):
    """A cover with rounded corners and a neon glow border."""

    def __init__(self, pm, size, parent):
        super().__init__(parent)
        self.pm = pm
        self.hover = False
        self.focused = False
        self.setFixedSize(size, size)
        ar = pm.width() / max(1, pm.height())
        self.pr = fit(ar, QRect(4, 4, size - 8, size - 8))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        color = QColor(PINK if (self.hover or self.focused) else CYAN)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.pr), 5, 5)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for width, alpha in ((7, 28), (4, 55)) + (((12, 70),) if self.focused else ()):
            c = QColor(color)
            c.setAlpha(alpha)
            p.setPen(QPen(c, width))
            p.drawPath(path)
        p.save()
        p.setClipPath(path)
        p.drawPixmap(self.pr, self.pm)
        p.restore()
        p.setPen(QPen(color, 1.6))
        p.drawPath(path)


class Tile(QWidget):
    clicked = pyqtSignal(object)

    def __init__(self, node, list_mode, parent, paths_fn=None):
        super().__init__(parent)
        self.node, self.paths_fn, self._press = node, paths_fn, None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        pm = QPixmap.fromImage(node.img) if not node.img.isNull() else placeholder()
        self.cover = CoverBox(pm, 46 if list_mode else TILE + 8, self)
        if node.hit >= 0:
            text = f"♪ {Path(node.tracks[node.hit]).stem}\n{node.name}"
        else:
            text = node.name + ("  ▶" if node.children else "")
        cap = QLabel(text, self)
        cap.setObjectName("cap")
        cap.setWordWrap(True)
        if list_mode:
            lay = QHBoxLayout(self)
            lay.setContentsMargins(6, 3, 6, 3)
            lay.setSpacing(12)
            lay.addWidget(self.cover)
            lay.addWidget(cap, 1)
            cap.setStyleSheet("font-size:13px;")
            self.setFixedHeight(54)
        else:
            lay = QVBoxLayout(self)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(2)
            cap.setFixedHeight(38)
            cap.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            lay.addWidget(self.cover)
            lay.addWidget(cap)
            self.setFixedSize(TILE + 8, TILE + 8 + 42)

    def enterEvent(self, e):
        self.cover.hover = True
        self.cover.update()

    def leaveEvent(self, e):
        self.cover.hover = False
        self.cover.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._press = e.position().toPoint()

    def mouseMoveEvent(self, e):
        if (self._press is not None and self.paths_fn and
                (e.position().toPoint() - self._press).manhattanLength() >= QApplication.startDragDistance()):
            self._press = None
            md = QMimeData()
            md.setData(MIME, json.dumps(self.paths_fn(self.node)).encode())
            d = QDrag(self)
            d.setMimeData(md)
            d.setPixmap(self.cover.pm.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation))
            d.exec(Qt.DropAction.CopyAction)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._press is not None:
            self._press = None
            self.clicked.emit(self)


# ----- player screen widgets -----
class HexButton(QPushButton):
    def __init__(self, kind, big=False, parent=None):
        super().__init__(parent)
        self.kind, self.big, self.active = kind, big, False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(7, 7, -7, -7)
        cx, cy = r.center().x(), r.center().y()
        if self.big:
            rad = min(r.width(), r.height()) / 2
            pts = [QPointF(cx + rad * math.cos(math.radians(-90 + 60 * i)),
                           cy + rad * math.sin(math.radians(-90 + 60 * i))) for i in range(6)]
        else:
            c = r.height() / 2
            pts = [QPointF(r.left() + c, r.top()), QPointF(r.right() - c, r.top()),
                   QPointF(r.right(), cy), QPointF(r.right() - c, r.bottom()),
                   QPointF(r.left() + c, r.bottom()), QPointF(r.left(), cy)]
        path = QPainterPath()
        path.addPolygon(QPolygonF(pts))
        path.closeSubpath()
        hot = self.big or self.active
        c1, c2 = (PINK, MAGENTA) if hot else (CYAN, "#4aa8ff")
        fc = QColor(c1)
        fc.setAlpha(80 if self.underMouse() else 32)
        p.fillPath(path, fc)
        glow(p, path, r, c1, c2, 2.2)
        col = QColor("#ffffff") if self.big else QColor(c1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(col)
        u = r.height() * (0.2 if self.big else 0.24)
        k = self.kind
        if k == "pause":
            p.drawRect(QRectF(cx - u * 0.95, cy - u, u * 0.75, u * 2))
            p.drawRect(QRectF(cx + u * 0.2, cy - u, u * 0.75, u * 2))
        elif k == "play":
            p.drawPolygon(QPolygonF([QPointF(cx - u * 0.6, cy - u), QPointF(cx - u * 0.6, cy + u),
                                     QPointF(cx + u, cy)]))
        elif k == "next":
            p.drawRect(QRectF(cx + u * 0.6, cy - u, u * 0.35, u * 2))
            p.drawPolygon(QPolygonF([QPointF(cx - u, cy - u), QPointF(cx - u, cy + u),
                                     QPointF(cx + u * 0.5, cy)]))
        elif k == "prev":
            p.drawRect(QRectF(cx - u * 0.95, cy - u, u * 0.35, u * 2))
            p.drawPolygon(QPolygonF([QPointF(cx + u, cy - u), QPointF(cx + u, cy + u),
                                     QPointF(cx - u * 0.5, cy)]))
        else:
            p.setPen(col)
            p.setFont(QFont("sans", 22))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "⇄" if k == "shuffle" else "↻")


class Spectrum(QWidget):
    """Animated equalizer bars (decorative; not a real FFT)."""

    def __init__(self, parent=None, n=44, reflect=True, seg=8):
        super().__init__(parent)
        self.n, self.reflect, self.seg = n, reflect, seg
        self.levels = [0.0] * n
        self.playing = False
        self.source = None       # callable -> real FFT levels (or None)
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.tick)
        self._fps_started = time.monotonic()
        self._fps_frames = 0
        self.measured_fps = 0.0

    def showEvent(self, e):
        self.timer.start()

    def hideEvent(self, e):
        self.timer.stop()

    def tick(self):
        src = self.source() if self.source else None
        for i in range(self.n):
            if src:
                k = len(src) / self.n
                lo = int(i * k)
                t = max(src[lo:max(lo + 1, int((i + 1) * k))])
                self.levels[i] = t if t > self.levels[i] else self.levels[i] * 0.8 + t * 0.2
            elif self.playing:
                env = (1 - i / self.n) ** 0.7 * 0.85 + 0.15
                t = (random.random() ** 1.4) * env
                self.levels[i] += (t - self.levels[i]) * 0.4
            else:
                self.levels[i] *= 0.88
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        w, h = self.width(), self.height()
        top_h = h * 0.72 if self.reflect else h
        bw = w / self.n
        step = self.seg + 2
        maxs = max(1, int(top_h // step))
        c1, c2 = QColor(CYAN), QColor(MAGENTA)
        p.setPen(Qt.PenStyle.NoPen)
        for i, lv in enumerate(self.levels):
            t = i / max(1, self.n - 1)
            col = QColor(int(c1.red() + (c2.red() - c1.red()) * t),
                         int(c1.green() + (c2.green() - c1.green()) * t),
                         int(c1.blue() + (c2.blue() - c1.blue()) * t))
            ns = max(1, int(lv * maxs))
            x = i * bw
            for s in range(ns):
                p.setBrush(col)
                p.drawRect(QRectF(x, top_h - (s + 1) * step, bw - 2, self.seg))
                if self.reflect and s * step < h - top_h:
                    rc = QColor(col)
                    rc.setAlpha(int(90 * (1 - s * step / max(1, h - top_h))))
                    p.setBrush(rc)
                    p.drawRect(QRectF(x, top_h + 2 + s * step, bw - 2, self.seg))
        if os.environ.get("NEONPLAYER_SHOW_FPS") == "1" and self.reflect:
            self._fps_frames += 1
            elapsed = time.monotonic() - self._fps_started
            if elapsed >= 1.0:
                self.measured_fps = self._fps_frames / elapsed
                self._fps_frames = 0
                self._fps_started = time.monotonic()
            p.setPen(QColor(180, 255, 255, 230))
            p.setFont(QFont("monospace", 9))
            p.drawText(6, 14, f"{self.measured_fps:.1f} FPS · QWidget")


class LyricsWindow(QDialog):
    def __init__(self,parent):
        super().__init__(parent); self.setWindowTitle("NeonPlayer · Synchronized Lyrics"); self.resize(620,560)
        self.setStyleSheet("QDialog{background:#080719;color:#eee} QLabel{color:#aaa;font-size:16px} QSlider{min-height:24px}")
        lay=QVBoxLayout(self); self.heading=QLabel("LYRICS"); self.heading.setStyleSheet("color:#00e5ff;font-size:20px;font-weight:bold")
        lay.addWidget(self.heading); self.lines=[]; self.labels=[]
        for _ in range(9):
            lb=QLabel(" "); lb.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(lb); self.labels.append(lb)
        row=QHBoxLayout(); row.addWidget(QLabel("Sync offset")); self.offset=QSlider(Qt.Orientation.Horizontal); self.offset.setRange(-10000,10000); self.offset.setSingleStep(100); row.addWidget(self.offset); self.offset_label=QLabel("0 ms"); row.addWidget(self.offset_label); lay.addLayout(row)
        self.offset.valueChanged.connect(lambda v:self.offset_label.setText(f"{v:+d} ms"))
    def set_lyrics(self,lyrics):
        import re
        self.lines=[]
        for line in (lyrics or "").splitlines():
            stamps=re.findall(r"\[(\d{1,2}):(\d{2})(?:[.:](\d{1,3}))?\]",line)
            text=re.sub(r"\[[^]]+\]", "", line).strip()
            for mm,ss,frac in stamps:
                ms=int((frac or "0").ljust(3,"0")[:3]); self.lines.append((int(mm)*60000+int(ss)*1000+ms,text))
        self.lines.sort(key=lambda x:x[0])
        self.synced=bool(self.lines)
        if not self.lines and lyrics: self.lines=[(0,x.strip()) for x in lyrics.splitlines() if x.strip()]
        self.update_position(0)
    def update_position(self,ms):
        if not self.lines:return
        t=ms+self.offset.value(); idx=0
        if self.synced:
            for i,(stamp,_) in enumerate(self.lines):
                if stamp<=t:idx=i
                else:break
            start=max(0,idx-4)
        else: start=0
        for j,lb in enumerate(self.labels):
            k=start+j
            if k<len(self.lines):
                lb.setText(self.lines[k][1]); lb.setStyleSheet("color:#ff2a9d;font-size:22px;font-weight:bold" if self.synced and k==idx else "color:#aaa;font-size:16px")
            else: lb.setText(" ")


class TrackDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, queue=False):
        super().__init__(parent)
        self.queue = queue

    def sizeHint(self, opt, idx):
        return QSize(opt.rect.width(), 38)

    def paint(self, p, opt, idx):
        num, title, dur = idx.data(Qt.ItemDataRole.UserRole)
        cur = bool(opt.state & QStyle.StateFlag.State_Selected)
        r = QRectF(opt.rect).adjusted(2, 2, -2, -2)
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if cur:
            acc = QColor(CYAN if self.queue else PINK)
            p.setPen(QPen(acc, 1.6))
            acc.setAlpha(40)
            p.setBrush(acc)
            p.drawRoundedRect(r, 10, 10)
        else:
            p.setPen(QColor(255, 255, 255, 28))
            p.drawLine(QPointF(r.left() + 6, r.bottom()), QPointF(r.right() - 6, r.bottom()))
        f = QFont(opt.font)
        f.setPointSize(11)
        p.setFont(f)
        p.setPen(QColor(YELLOW if (cur and not self.queue) else "#e8e6ff"))
        vc = Qt.AlignmentFlag.AlignVCenter
        if cur and not self.queue:
            p.drawText(QRectF(r.left() + 10, r.top(), 20, r.height()), vc | Qt.AlignmentFlag.AlignLeft, "▶")
        p.drawText(QRectF(r.left() + 32, r.top(), 34, r.height()), vc | Qt.AlignmentFlag.AlignLeft, num)
        tw = r.width() - 72 - 64
        p.drawText(QRectF(r.left() + 72, r.top(), tw, r.height()), vc | Qt.AlignmentFlag.AlignLeft,
                   QFontMetrics(f).elidedText(title, Qt.TextElideMode.ElideRight, int(tw)))
        p.drawText(QRectF(r.right() - 62, r.top(), 54, r.height()), vc | Qt.AlignmentFlag.AlignRight, dur)
        p.restore()




def fill_list(lw, rows, infos=None):
    lw.clear()
    for i, r in enumerate(rows):
        it = QListWidgetItem()
        it.setData(UR, r)
        if infos is not None:
            it.setData(UR + 1, infos[i])
        lw.addItem(it)


class TrackList(QListWidget):
    """Track list with drag & drop. Album lists are drag sources; queue lists accept drops
    (from album tiles, album lists, other lists) and reorder internally."""
    dropped = pyqtSignal(list, int)          # paths, insert row

    def __init__(self, queue=False):
        super().__init__()
        self.setItemDelegate(TrackDelegate(self, queue))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        if queue:
            self.setAcceptDrops(True)
            self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
            self.setDefaultDropAction(Qt.DropAction.MoveAction)
        else:
            self.setDragEnabled(True)
            self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)

    def mimeData(self, items):
        paths = [it.data(UR + 1)["path"] for it in items if it.data(UR + 1)]
        md = QMimeData()
        md.setData(MIME, json.dumps(paths).encode())
        return md

    def _external(self, e):
        return e.mimeData().hasFormat(MIME) and e.source() is not self

    def dragEnterEvent(self, e):
        e.acceptProposedAction() if self._external(e) else super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        e.acceptProposedAction() if self._external(e) else super().dragMoveEvent(e)

    def dropEvent(self, e):
        if self._external(e):
            paths = json.loads(bytes(e.mimeData().data(MIME)).decode())
            row = self.indexAt(e.position().toPoint()).row()
            self.dropped.emit(paths, self.count() if row < 0 else row)
            e.acceptProposedAction()
        else:
            super().dropEvent(e)


def small_btn(text, name="tbtn", size=18):
    b = QPushButton(text)
    b.setObjectName(name)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if name == "tbtn":
        b.setStyleSheet(f"font-size:{size}px;")
    return b


class QueueDock(Panel):
    """Browser side panel: mini now-playing card + queue (a drop target for tiles/tracks)."""

    def __init__(self, bgc):
        super().__init__(PINK, PURPLE, bgc)
        self.setFixedWidth(292)
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 16, 18)
        v.setSpacing(8)
        top = QHBoxLayout()
        top.setSpacing(10)
        self.thumb = QLabel()
        self.thumb.setFixedSize(64, 64)
        self.thumb.setScaledContents(True)
        tv = QVBoxLayout()
        tv.setSpacing(2)
        self.title = QLabel(tr("Nothing playing"))
        self.title.setObjectName("dtitle")
        self.title.setWordWrap(True)
        self.title.setFixedHeight(40)
        self.title.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.artist = QLabel("")
        self.artist.setObjectName("dartist")
        tv.addWidget(self.title)
        tv.addWidget(self.artist)
        tv.addStretch()
        top.addWidget(self.thumb)
        top.addLayout(tv, 1)
        v.addLayout(top)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        v.addWidget(self.seek)
        row = QHBoxLayout()
        self.prev, self.play, self.next = small_btn("◀◀"), small_btn("▶", size=22), small_btn("▶▶")
        self.time = QLabel("0:00 / 0:00")
        self.time.setObjectName("dartist")
        self.open_btn = treg(small_btn("", "mini"), "Open")
        for w in (self.prev, self.play, self.next):
            row.addWidget(w)
        row.addStretch()
        row.addWidget(self.time)
        v.addLayout(row)
        row2 = QHBoxLayout()
        row2.addStretch()
        row2.addWidget(self.open_btn)
        v.addLayout(row2)
        hdr = QHBoxLayout()
        self.qlab = QLabel(tr("Queue").upper() + " · 0")
        self.qlab.setObjectName("sec")
        self.btn_clear = treg(small_btn("", "mini"), "Clear")
        self.btn_save = treg(small_btn("", "mini"), "Save…")
        hdr.addWidget(self.qlab)
        hdr.addStretch()
        hdr.addWidget(self.btn_clear)
        hdr.addWidget(self.btn_save)
        v.addLayout(hdr)
        self.qlist = TrackList(True)
        v.addWidget(self.qlist, 1)

    def set_queue(self, rows, infos):
        fill_list(self.qlist, rows, infos)
        self.qlab.setText(tr("Queue").upper() + f" · {len(rows)}")


class MiniWindow(QWidget):
    """Small always-on-top player bar (the full window hides while it is shown)."""
    wheel = pyqtSignal(int)
    prev_clicked = pyqtSignal()
    play_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    expand_clicked = pyqtSignal()
    seek_moved = pyqtSignal(int)

    def __init__(self):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("NeonPlayer mini")
        self.resize(560, 140)
        self.setMinimumSize(430, 130)
        root = QHBoxLayout(self)
        root.setContentsMargins(24, 22, 22, 22)
        root.setSpacing(14)
        self.thumb = QLabel()
        self.thumb.setFixedSize(92, 92)
        self.thumb.setScaledContents(True)
        root.addWidget(self.thumb)
        col = QVBoxLayout()
        col.setSpacing(2)
        top = QHBoxLayout()
        self.title = QLabel(tr("Nothing playing"))
        self.title.setObjectName("dtitle")
        top.addWidget(self.title, 1)
        self.exp = small_btn("⤢", "tbtn", 20)
        top.addWidget(self.exp)
        col.addLayout(top)
        self.artist = QLabel("")
        self.artist.setObjectName("dartist")
        col.addWidget(self.artist)
        srow = QHBoxLayout()
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.time = QLabel("0:00")
        self.time.setObjectName("dartist")
        srow.addWidget(self.seek, 1)
        srow.addWidget(self.time)
        col.addLayout(srow)
        brow = QHBoxLayout()
        self.prev, self.play, self.next = small_btn("◀◀"), small_btn("▶", size=22), small_btn("▶▶")
        brow.addStretch()
        for w in (self.prev, self.play, self.next):
            brow.addWidget(w)
        brow.addStretch()
        col.addLayout(brow)
        root.addLayout(col, 1)
        self.prev.clicked.connect(self.prev_clicked)
        self.play.clicked.connect(self.play_clicked)
        self.next.clicked.connect(self.next_clicked)
        self.exp.clicked.connect(self.expand_clicked)
        self.seek.sliderMoved.connect(self.seek_moved)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(8, 8, -8, -8)
        path = chamfer(rect, 16)
        p.fillPath(path, QColor(6, 4, 24, 232))
        glow(p, path, rect, CYAN, PINK, 2.2)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.windowHandle():
            self.windowHandle().startSystemMove()

    def mouseDoubleClickEvent(self, e):
        self.expand_clicked.emit()

    def wheelEvent(self, e):
        self.wheel.emit(1 if e.angleDelta().y() > 0 else -1)

    def update_info(self, title, artist, pm):
        self.title.setText(title)
        self.artist.setText(artist)
        if pm is not None:
            self.thumb.setPixmap(pm)

    def set_playing(self, on):
        self.play.setText("❚❚" if on else "▶")

    def set_pos(self, p, d):
        self.seek.setRange(0, max(0, d))
        if not self.seek.isSliderDown():
            self.seek.setValue(p)
        self.time.setText(f"{fmt(p)} / {fmt(d)}")


class Overlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.ar = 1.0
        self.busy = False
        self.cover_box = QRect(0, 0, 100, 100)
        ui = self.ui = QWidget(self)

        # header
        self.head = DragBar(ui)
        hl = QHBoxLayout(self.head)
        hl.setContentsMargins(24, 0, 4, 0)
        hl.addWidget(Logo())
        hl.addSpacing(16)
        self.close_btn, self.stop_btn, self.mini_btn = QPushButton(), QPushButton(), QPushButton()
        self.lyrics_btn = QPushButton("♫ Lyrics")
        self.lyrics_btn.setObjectName("back")
        hl.addWidget(self.lyrics_btn)
        specs = ((self.close_btn, "Library", "◀  ", "Back to the library — music keeps playing"),
                 (self.stop_btn, "Stop", "■  ", "Stop playback and close the player"),
                 (self.mini_btn, "Mini", "▭  ", "Switch to the small always-on-top player"))
        for b, key, glyph, tip in specs:
            b.setObjectName("back")
            treg(b, key, prefix=glyph, upper=True)
            treg(b, tip, "setToolTip")
            hl.addWidget(b)
        hl.addStretch()

        # left rail
        self.rail = Frame(CYAN, PURPLE, 16, 170, ui)
        rl = QVBoxLayout(self.rail)
        rl.setContentsMargins(11, 18, 11, 18)
        rl.setSpacing(14)

        def rbtn(txt, checkable=True):
            b = QPushButton(txt)
            b.setObjectName("rail")
            b.setCheckable(checkable)
            b.setFixedSize(62, 62)
            rl.addWidget(b)
            return b
        self.note_btn = rbtn("♫")
        self.note_btn.setChecked(True)
        self.note_btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.fav = rbtn("♡")
        self.list_btn = rbtn("☰")
        self.list_btn.setChecked(True)
        self.sleep_btn = rbtn("☾", False)
        treg(self.sleep_btn, "Sleep timer", "setToolTip")

        # cover frame + cover (cover sits above the ui layer)
        self.cframe = Frame(PINK, MAGENTA, 22, 0, ui)
        self.cframe.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.cframe.hide()
        self.cover = QLabel(self)
        self.cover.setScaledContents(True)
        shadow = QGraphicsDropShadowEffect(self.cover)
        shadow.setBlurRadius(80)
        shadow.setOffset(0, 26)
        shadow.setColor(QColor(255, 42, 157, 160))
        self.cover.setGraphicsEffect(shadow)

        # info
        def lab(name, text=""):
            lb = QLabel(text, ui)
            lb.setObjectName(name)
            return lb
        self.badge = treg(lab("badge"), "Now Playing", upper=True)
        self.title = lab("ptitle")
        self.title.setWordWrap(True)
        self.title.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.artist = lab("partist")
        self.album = lab("palbum")
        self.meta = lab("pmeta")
        self.spec = Spectrum(ui, 44, True, 8)

        # seek
        self.pos = lab("time", "0:00")
        self.slider = QSlider(Qt.Orientation.Horizontal, ui)
        self.dur = lab("time", "0:00")
        self.dur.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # transport
        self.hx_shuffle = HexButton("shuffle", False, ui)
        self.hx_prev = HexButton("prev", False, ui)
        self.hx_play = HexButton("play", True, ui)
        self.hx_next = HexButton("next", False, ui)
        self.hx_repeat = HexButton("repeat", False, ui)

        # bottom row
        self.chip_codec = lab("chip", "—")
        self.chip_sr = lab("chip", "—")
        self.chip_bits = lab("chip", "—")
        for c in (self.chip_codec, self.chip_sr, self.chip_bits):
            c.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mini = Spectrum(ui, 10, False, 5)
        self.sleep_lbl = lab("chip2")
        self.sleep_lbl.hide()
        self.vol_lbl = treg(lab("time"), "VOL")
        self.vol_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.vol = QSlider(Qt.Orientation.Horizontal, ui)
        self.vol.setRange(0, 100)

        # right panel: album list on top, queue below, resizable splitter
        self.rframe = Frame(CYAN, PINK, 26, 190, ui)
        self.tool_shuffle = QPushButton("⇄", self.rframe)
        self.tool_repeat = QPushButton("↻", self.rframe)
        for b in (self.tool_shuffle, self.tool_repeat):
            b.setObjectName("tbtn")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        self.panel = TrackList(False)
        self.qpanel = TrackList(True)
        self.btn_qall = treg(small_btn("", "mini"), "Queue all", prefix="+ ")
        self.btn_qclear = treg(small_btn("", "mini"), "Clear")
        self.btn_qsave = treg(small_btn("", "mini"), "Save…")
        self.sec_a, self.lab_a = self.section("Album", self.panel, [self.btn_qall])
        self.sec_q, self.lab_q = self.section("Queue", self.qpanel, [self.btn_qclear, self.btn_qsave], reg=False)
        self.split = QSplitter(Qt.Orientation.Vertical, self.rframe)
        self.split.setChildrenCollapsible(False)
        self.split.setHandleWidth(10)
        self.split.addWidget(self.sec_a)
        self.split.addWidget(self.sec_q)
        self.split.setStretchFactor(0, 3)
        self.split.setStretchFactor(1, 2)
        self.split.setSizes([600, 400])
        self.list_btn.clicked.connect(self.rframe.setVisible)

    @staticmethod
    def section(title, lst, buttons, reg=True):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
        row = QHBoxLayout()
        lab = QLabel()
        if reg:
            treg(lab, title, upper=True)
        else:
            lab.setText(tr(title).upper() + " · 0")
        lab.setObjectName("sec")
        row.addWidget(lab)
        row.addStretch()
        for b in buttons:
            row.addWidget(b)
        v.addLayout(row)
        v.addWidget(lst, 1)
        return w, lab

    def set_tracks(self, rows, infos):
        fill_list(self.panel, rows, infos)

    def set_queue(self, rows, infos):
        fill_list(self.qpanel, rows, infos)
        self.lab_q.setText(tr("Queue").upper() + f" · {len(rows)}")

    def set_cover(self, pm):
        self.ar = pm.width() / max(1, pm.height())
        self.cover.setPixmap(pm)
        self.relayout()

    def set_now(self, info, label, row):
        self.badge.setText(tr("Now Playing").upper())
        self.title.setText(info["title"])
        self.artist.setText(info["artist"] or " ")
        self.album.setText(info["album"] or " ")
        # Keep the album list selection tied to the actual playing track.
        # QListWidget's delegate uses State_Selected to draw the neon highlight.
        if row is not None and 0 <= row < self.panel.count():
            self.panel.setCurrentRow(row)
            self.panel.scrollToItem(self.panel.item(row), QAbstractItemView.ScrollHint.EnsureVisible)
        else:
            self.panel.setCurrentRow(-1)

    def set_album_preview(self, node, infos, playing_path=None):
        """Show a browsed album without changing the active playback session.

        Album previews have no currently selected track, so technical details are
        taken from the first track only as a representative sample. Playback
        state and the active track metadata are deliberately left untouched.
        """
        self.badge.setText(tr("Album Preview").upper())
        self.title.setText(node.name or tr("Unknown album"))
        self.artist.setText(node.artist or " ")
        self.album.setText(node.name or " ")
        # If the currently playing track belongs to this album, highlight it
        # immediately even when this album was opened as a preview.
        playing_row = next((i for i, item in enumerate(infos)
                            if playing_path and item.get("path") == playing_path), -1)
        if playing_row >= 0:
            self.panel.setCurrentRow(playing_row)
            self.panel.scrollToItem(self.panel.item(playing_row), QAbstractItemView.ScrollHint.EnsureVisible)
        else:
            self.panel.setCurrentRow(-1)

        if not infos:
            self.chip_codec.setText("—")
            self.chip_sr.setText("—")
            self.chip_bits.setText("—")
            self.meta.setText(tr("{n} tracks · select a track to play", n=0))
            return

        sample = infos[0]
        sr = sample.get("sr", 0)
        bits = sample.get("bits", 0)
        bitrate = sample.get("bitrate", 0)
        codec = sample.get("codec", "")
        srt = f"{sr / 1000:g} kHz" if sr else "—"
        bt = f"{bits}-bit" if bits else "—"
        self.chip_codec.setText(codec or "—")
        self.chip_sr.setText(srt)
        self.chip_bits.setText(bt)

        extra = " ".join(x for x in (codec, srt if sr else "") if x)
        if bt != "—":
            extra += f" / {bt}"
        if bitrate:
            mode = sample.get("br_mode", "")
            extra += f" / {bitrate // 1000} kbps" + (f" {mode}" if mode else "")
        self.meta.setText(
            tr("{n} tracks · select a track to play", n=len(infos))
            + (f"   |   {extra}" if extra else "")
        )

    def target_rect(self):
        return fit(self.ar, self.cover_box)

    def relayout(self):
        W, H = self.width(), self.height()
        self.ui.setGeometry(0, 0, W, H)
        self.head.setGeometry(0, 0, W, 70)
        m = 24
        pw = int(max(300, min(430, W * 0.26)))
        ph = max(300, H - 84 - 44)
        self.rframe.setGeometry(W - pw - m, 84, pw, ph)
        self.tool_shuffle.setGeometry(pw // 2 - 56, 10, 44, 40)
        self.tool_repeat.setGeometry(pw // 2 + 12, 10, 44, 40)
        self.split.setGeometry(20, 54, pw - 40, ph - 72)
        self.rail.setGeometry(m, 110, 86, 4 * 62 + 3 * 14 + 36)
        cx0, cx1 = m + 86 + 34, W - pw - m - 34
        aw = cx1 - cx0
        s = int(min(aw * 0.52, H * 0.46))
        top = 96
        self.cover_box = QRect(cx0 + 14, top + 14, s - 28, s - 28)
        t = self.target_rect()
        self.cframe.setGeometry(t.adjusted(-14, -14, 14, 14))
        if self.cover.isVisible() and not self.busy:
            self.cover.setGeometry(t)
        ix, iw = cx0 + s + 30, max(200, cx1 - (cx0 + s + 30))
        self.badge.setGeometry(ix, top + 4, 190, 40)
        self.title.setGeometry(ix, top + 58, iw, 84)
        self.artist.setGeometry(ix, top + 146, iw, 34)
        self.album.setGeometry(ix, top + 182, iw, 30)
        self.meta.setGeometry(ix, top + 226, iw, 26)
        self.spec.setGeometry(ix, top + 262, iw, max(80, s - 242))
        ys = top + s + 30
        self.pos.setGeometry(cx0, ys, 56, 28)
        self.slider.setGeometry(cx0 + 62, ys, aw - 124, 28)
        self.dur.setGeometry(cx1 - 56, ys, 56, 28)
        big, gap = 112, 14
        sw = int(min(140, (aw - big - 4 * gap) / 4))
        sh = 62
        ytr = ys + 46
        x = cx0 + (aw - (4 * sw + big + 4 * gap)) // 2
        yb = ytr + (big - sh) // 2
        for b in (self.hx_shuffle, self.hx_prev):
            b.setGeometry(x, yb, sw, sh)
            x += sw + gap
        self.hx_play.setGeometry(x, ytr, big, big)
        x += big + gap
        for b in (self.hx_next, self.hx_repeat):
            b.setGeometry(x, yb, sw, sh)
            x += sw + gap
        yb = H - 66
        self.chip_codec.setGeometry(cx0, yb, 76, 34)
        self.chip_sr.setGeometry(cx0 + 86, yb, 100, 34)
        self.chip_bits.setGeometry(cx0 + 196, yb, 84, 34)
        self.mini.setGeometry(cx0 + 296, yb - 4, 90, 42)
        vw = max(100, min(240, cx1 - (cx0 + 400) - 56))
        self.sleep_lbl.setGeometry(cx0 + 396, yb, max(60, cx1 - vw - 86 - (cx0 + 396) - 6), 34)
        self.vol_lbl.setGeometry(cx1 - vw - 84, yb, 78, 34)
        self.vol.setGeometry(cx1 - vw, yb + 4, vw, 26)

    def resizeEvent(self, e):
        self.relayout()


# ---------- main window ----------
class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeonPlayer")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.resize(1360, 860)
        self.setMinimumSize(1100, 740)
        self.cfg = {}
        try:
            self.cfg = json.loads(CONFIG.read_text())
        except Exception:
            pass
        self.root = None
        self.node_map = {}
        self.all_albums, self.items, self.shown, self.tiles, self.visible = [], [], [], [], []
        self.stack, self.crumbs, self.empty_msg = [], [""], ""
        self.mode, self.search_q = "folders", ""
        self.list_mode = bool(self.cfg.get("list_mode", False))
        self.cur = self.cur_tile = self.last_node = None
        self.pending_node = None
        self.pending_tinfo = None
        self.tinfo = []
        self.idx = 0
        self.now_info = None
        self.now_q = False
        self.cover_pm = self.album_pm = None
        self.cover_for_queue = False
        self.shuffle = self.repeat = False
        self.played = set()
        self.anim = None
        self.scanner = self.loader = None
        self.scan_silent = False
        self.cache_error = ""
        self.scan_progress = None
        self.scan_total = 0
        self.resumed = False
        self.serial = 0
        self.art_path = ""
        self.cols, self.focus_idx, self.pad_active, self.pad_name = 1, -1, False, ""
        self.sleep_left, self.sleep_eot, self.sleep_anim = 0, False, None
        self.volume = float(self.cfg.get("volume", 0.7))
        self.queue = []
        for pth in self.cfg.get("queue", []):
            if os.path.isfile(pth):
                self.queue.append(track_info(pth, "", os.path.basename(os.path.dirname(pth))))

        self.engine = eng.Engine(self)
        self.engine.setVolume(self.volume)
        self.engine.xfade = float(self.cfg.get("xfade", 0))

        sky = QPixmap(str(SKYLINE))
        sky = None if sky.isNull() else sky
        self.central = Central(sky, make_blur(sky) if sky else None)
        self.setCentralWidget(self.central)
        outer = QVBoxLayout(self.central)
        outer.setContentsMargins(18, 14, 18, 18)
        self.content = QWidget()
        outer.addWidget(self.content)
        cv = QVBoxLayout(self.content)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(4)

        # header
        head = DragBar()
        head.setFixedHeight(70)
        hl = QHBoxLayout(head)
        hl.setContentsMargins(10, 0, 4, 0)
        hl.addWidget(Logo())
        hl.addSpacing(14)
        self.back_btn = QPushButton("◀")
        self.back_btn.setObjectName("back")
        self.back_btn.hide()
        self.back_btn.clicked.connect(self.go_back)
        hl.addWidget(self.back_btn)
        self.crumb_label = QLabel("")
        hl.addWidget(self.crumb_label)
        hl.addStretch()
        self.search = QLineEdit()
        self.search.setObjectName("search")
        treg(self.search, "Search albums, artists, tracks…", "setPlaceholderText")
        self.search.setFixedWidth(270)
        self.search.addAction(icon_search(), QLineEdit.ActionPosition.LeadingPosition)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(180)
        self.search_timer.timeout.connect(self.run_search)
        self.search.textChanged.connect(lambda *_: self.search_timer.start())
        hl.addWidget(self.search)
        hl.addSpacing(10)
        grp = QButtonGroup(self)
        for kind in ("grid", "list"):
            b = QPushButton()
            b.setObjectName("vt")
            b.setCheckable(True)
            b.setIcon(icon_view(kind))
            b.setIconSize(QSize(26, 26))
            b.setChecked((kind == "list") == self.list_mode)
            b.clicked.connect(lambda _, k=kind: self.set_list_mode(k == "list"))
            grp.addButton(b)
            hl.addWidget(b)
        hl.addSpacing(14)
        self.add_win_buttons(hl)
        cv.addWidget(head)

        # body
        body = QHBoxLayout()
        body.setSpacing(6)
        cv.addLayout(body, 1)

        side = Panel(PINK, CYAN, self.central)
        side.setFixedWidth(250)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(18, 18, 18, 14)
        sl.setSpacing(0)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for key, glyph, label in NAV:
            b = QPushButton()
            treg(b, label, prefix=f"{glyph}    ")
            b.setObjectName("nav")
            b.setCheckable(True)
            b.setFixedHeight(44)
            b.setChecked(key == self.mode)
            b.clicked.connect(lambda _, k=key: self.set_mode(k))
            self.nav_group.addButton(b)
            sl.addWidget(b)
        self.np_btn = PulseButton("♫    " + tr("Now Playing"))
        self.np_btn.setObjectName("nav")
        self.np_btn.setFixedHeight(44)
        self.np_btn.clicked.connect(self.now_playing)
        sl.addWidget(self.np_btn)
        self.dock_btn = treg(QPushButton(), "Queue", prefix="▤    ")
        self.dock_btn.setObjectName("navt")
        self.dock_btn.setCheckable(True)
        self.dock_btn.setChecked(bool(self.cfg.get("dock", True)))
        self.dock_btn.setFixedHeight(44)
        self.dock_btn.clicked.connect(self.set_dock)
        sl.addWidget(self.dock_btn)
        mb = treg(QPushButton(), "Mini Player", prefix="▭    ")
        mb.setObjectName("nav")
        mb.setFixedHeight(44)
        mb.clicked.connect(self.toggle_mini)
        sl.addWidget(mb)
        sb = treg(QPushButton(), "Settings", prefix="⚙    ")
        sb.setObjectName("nav")
        sb.setFixedHeight(44)
        sb.clicked.connect(lambda _=False, btn=sb: self.settings_menu(btn))
        sl.addWidget(sb)
        sl.addStretch(1)
        self.pad_chip = treg(QLabel(), "Gamepad", prefix="◈ ", upper=True)
        self.pad_chip.setObjectName("chip2")
        self.pad_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pad_chip.hide()
        sl.addWidget(self.pad_chip)
        body.addWidget(side)

        main = Panel(CYAN, PURPLE, self.central)
        ml = QVBoxLayout(main)
        ml.setContentsMargins(20, 20, 12, 20)
        self.scroll = Scroller()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.holder = QWidget()
        self.grid = QGridLayout(self.holder)
        self.grid.setSpacing(14)
        self.scroll.setWidget(self.holder)
        self.scroll.resized.connect(self.reflow)
        self.msg = QLabel("")
        self.msg.setObjectName("msg")
        self.msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg.hide()
        ml.addWidget(self.scroll, 1)
        ml.addWidget(self.msg, 1)
        body.addWidget(main, 1)

        self.dock = QueueDock(self.central)
        self.dock.setVisible(self.dock_btn.isChecked())
        body.addWidget(self.dock)

        self.grip = QSizeGrip(self.central)
        self.mini_win = MiniWindow()

        # overlay (full player screen)
        self.overlay = Overlay(self.central)
        self.overlay.hide()
        o = self.overlay
        self.add_win_buttons(o.head.layout())
        o.close_btn.clicked.connect(self.minimize_overlay)
        o.stop_btn.clicked.connect(self.stop_and_close)
        o.mini_btn.clicked.connect(self.toggle_mini)
        o.sleep_btn.clicked.connect(lambda: self.sleep_menu(o.sleep_btn.mapToGlobal(QPoint(70, 0))))
        o.hx_play.clicked.connect(self.toggle_play)
        o.hx_next.clicked.connect(self.next_track)
        o.hx_prev.clicked.connect(self.prev_track)
        o.hx_shuffle.clicked.connect(self.toggle_shuffle)
        o.hx_repeat.clicked.connect(self.toggle_repeat)
        o.tool_shuffle.clicked.connect(self.toggle_shuffle)
        o.tool_repeat.clicked.connect(self.toggle_repeat)
        o.fav.clicked.connect(self.toggle_fav)
        self.lyrics_win = LyricsWindow(self)
        self.lyrics_win.offset.valueChanged.connect(self.save_lyrics_offset)
        o.lyrics_btn.clicked.connect(self.show_lyrics)
        self.lyrics_timer = QTimer(self); self.lyrics_timer.setInterval(100); self.lyrics_timer.timeout.connect(self.sync_lyrics)
        o.panel.itemClicked.connect(lambda it: self.play_index(o.panel.row(it)))
        o.panel.customContextMenuRequested.connect(self.album_menu)
        o.btn_qall.clicked.connect(self.queue_all)
        o.slider.sliderMoved.connect(self.seek_to)
        o.vol.setValue(int(self.volume * 100))
        o.vol.valueChanged.connect(self.set_volume)
        for lw, clear, save in ((o.qpanel, o.btn_qclear, o.btn_qsave),
                                (self.dock.qlist, self.dock.btn_clear, self.dock.btn_save)):
            lw.dropped.connect(self.queue_dropped)
            lw.itemDoubleClicked.connect(lambda it, lw=lw: self.queue_play(lw.row(it)))
            lw.customContextMenuRequested.connect(lambda pos, lw=lw: self.queue_menu(lw, pos))
            lw.model().rowsMoved.connect(lambda *a, lw=lw: QTimer.singleShot(0, lambda: self.queue_reordered(lw)))
            clear.clicked.connect(self.clear_queue)
            save.clicked.connect(self.save_playlist)
        d = self.dock
        d.play.clicked.connect(self.toggle_play)
        d.next.clicked.connect(self.next_track)
        d.prev.clicked.connect(self.prev_track)
        d.open_btn.clicked.connect(self.now_playing)
        d.seek.sliderMoved.connect(self.seek_to)
        m = self.mini_win
        m.prev_clicked.connect(self.prev_track)
        m.next_clicked.connect(self.next_track)
        m.play_clicked.connect(self.toggle_play)
        m.expand_clicked.connect(self.toggle_mini)
        m.seek_moved.connect(self.seek_to)
        m.wheel.connect(lambda s: self.nudge_volume(5 * s))
        o.spec.source = o.mini.source = self.engine.spectrum
        self.refresh_queue()

        E = self.engine
        E.positionChanged.connect(self.on_pos)
        E.durationChanged.connect(self.on_dur)
        E.stateChanged.connect(self.on_state)
        E.ended.connect(self.on_ended)
        E.nearEnd.connect(self.on_near_end)
        E.mediaError.connect(self.on_media_error)

        QShortcut(QKeySequence("Esc"), self, self.on_escape)
        QShortcut(QKeySequence("Backspace"), self, self.go_back)
        QShortcut(QKeySequence("Space"), self, self.toggle_play)
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Ctrl+M"), self, self.toggle_mini)
        self.central.resized.connect(self.on_resize)

        self.sleep_timer = QTimer(self)
        self.sleep_timer.setInterval(1000)
        self.sleep_timer.timeout.connect(self.sleep_tick)
        self.session_timer = QTimer(self)
        self.session_timer.setInterval(5000)
        self.session_timer.timeout.connect(self.save_session)
        self.session_timer.start()

        self.mpris = mpris.MprisService(self)
        self.pad = None
        if gamepad is not None:
            self.pad = gamepad.Gamepad(self)
            if self.pad.ok:
                self.pad.button.connect(self.on_pad_button)
                self.pad.direction.connect(self.on_pad_dir)
                self.pad.trigger.connect(self.on_pad_trigger)
                self.pad.scroll.connect(self.on_pad_scroll)
                self.pad.connected.connect(self.on_pad_connected)
                if self.pad.name:
                    self.on_pad_connected(self.pad.name)

        self.set_ui_scale(int(self.cfg.get("ui_scale", 100)))
        self.start()

    def add_win_buttons(self, layout):
        for txt, fn in (("–", self.showMinimized), ("□", self.toggle_max), ("✕", self.close)):
            b = QPushButton(txt)
            b.setObjectName("win")
            b.clicked.connect(fn)
            layout.addWidget(b)

    def closeEvent(self, e):
        self.save_session()
        self.mini_win.close()
        super().closeEvent(e)

    # --- window ---
    def toggle_max(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def on_resize(self):
        self.overlay.setGeometry(self.central.rect())
        self.grip.move(self.central.width() - self.grip.width() - 10,
                       self.central.height() - self.grip.height() - 10)
        if not self.overlay.isVisible():
            self.grip.raise_()

    def set_dock(self, on):
        self.dock.setVisible(on)
        self.cfg["dock"] = on
        self.save_cfg()

    def toggle_mini(self):
        if self.mini_win.isVisible():
            self.mini_win.hide()
            self.show()
            self.activateWindow()
        else:
            self.mini_sync()
            self.hide()
            self.mini_win.show()
            self.mini_win.activateWindow()

    def mini_sync(self):
        i = self.now_info
        self.mini_win.update_info(i["title"] if i else tr("Nothing playing"),
                                  (i["artist"] or i["album"]) if i else "",
                                  self.cover_pm.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio,
                                                       Qt.TransformationMode.SmoothTransformation)
                                  if self.cover_pm is not None else None)
        self.mini_win.set_playing(self.engine.playbackState() == QMediaPlayer.PlaybackState.PlayingState)
        self.mini_win.set_pos(self.engine.position(), self.engine.duration())

    def settings_menu(self, btn):
        m = QMenu(self)
        lm = m.addMenu(tr("Language"))
        for code, native in i18n.LANGS:
            a = lm.addAction(native)
            a.setCheckable(True)
            a.setChecked(code == i18n.lang())
            a.triggered.connect(lambda _, c=code: self.set_language(c))
        m.addSeparator()
        m.addAction(tr("Change library…"), lambda: self.start(choose=True))
        m.addAction(tr("Rescan library (changes only)"), self.rescan)
        m.addAction(tr("Rebuild cache (full rescan)"), lambda: self.start(full=True))
        m.addSeparator()
        fm = m.addMenu(tr("UI font size"))
        for pct in (100, 110, 125, 150, 175, 200):
            a = fm.addAction(f"{pct}%")
            a.setCheckable(True)
            a.setChecked(int(self.cfg.get("ui_scale", 100)) == pct)
            a.triggered.connect(lambda _, v=pct: self.set_ui_scale(v))
        m.addSeparator()
        rg = m.addMenu("ReplayGain")
        for key,label in (("off","Off"),("track","Track gain"),("album","Album gain")):
            a=rg.addAction(label); a.setCheckable(True); a.setChecked(self.cfg.get("replaygain_mode","off")==key)
            a.triggered.connect(lambda _,k=key:self.set_replaygain_mode(k))
        xm = m.addMenu(tr("Crossfade"))
        for secs in (0, 2, 4, 6, 8, 10):
            label = tr("Off (gapless)") if secs == 0 else tr("{n} s", n=secs)
            a = xm.addAction(label)
            a.setCheckable(True)
            a.setChecked(int(self.engine.xfade) == secs)
            a.triggered.connect(lambda _, s=secs: self.set_xfade(s))
        sm = m.addMenu(tr("Sleep timer"))
        self.fill_sleep_menu(sm)
        r = m.addAction(tr("Resume last session on launch"))
        r.setCheckable(True)
        r.setChecked(bool(self.cfg.get("resume", True)))
        r.triggered.connect(self.set_resume)
        m.addAction(tr("Mini player (Ctrl+M)"), self.toggle_mini)
        m.addAction(tr("Toggle fullscreen (F11)"), self.toggle_fullscreen)
        m.addSeparator()
        pad_state = self.pad_name if self.pad_name else (
            tr("none detected") if self.pad is not None and self.pad.ok else tr("needs pygame"))
        for text in (tr("Cache folder: {path}", path=CACHE_DIR),
                     tr("Media keys (MPRIS): {state}",
                        state=tr("active") if self.mpris.available else tr("unavailable")),
                     tr("Spectrum: {state}",
                        state=tr("real-time FFT") if self.engine.an is not None else tr("animated (needs numpy)")),
                     tr("Controller: {state}", state=pad_state)):
            m.addAction(text).setEnabled(False)
        if self.cache_error:
            m.addAction(tr("⚠ Cache save failed: {err}", err=self.cache_error)).setEnabled(False)
        m.exec(btn.mapToGlobal(QPoint(btn.width(), 0)))

    def set_replaygain_mode(self, mode):
        self.cfg["replaygain_mode"]=mode
        if self.now_info: self.apply_replaygain(self.now_info)
        else: self.engine.setVolume(self.volume)
        self.save_cfg()

    def set_ui_scale(self, percent):
        percent = int(percent)
        self.cfg["ui_scale"] = percent
        scale = percent / 100.0
        app = QApplication.instance()
        base = QFont(app.font())
        base.setPointSizeF(max(8.0, 10.0 * scale))
        app.setFont(base)
        # Scale typography and spacing in the main stylesheet. Preserve the
        # intentionally oversized transport/window controls.
        import re
        def scaled_style(css):
            blocks = []
            for block in css.split("}"):
                if "{" not in block:
                    if block.strip(): blocks.append(block)
                    continue
                selector, body = block.split("{", 1)
                if any(x in selector for x in ("#tbtn", "#rail", "#win", "#mini")):
                    blocks.append(selector + "{" + body)
                    continue
                body = re.sub(r"(font-size\s*:\s*)(\d+(?:\.\d+)?)px",
                              lambda m: m.group(1) + f"{float(m.group(2))*scale:.1f}px", body)
                blocks.append(selector + "{" + body)
            return "}".join(blocks) + "}"
        app.setStyleSheet(scaled_style(STYLE))
        self.save_cfg()

    def set_xfade(self, secs):
        self.engine.xfade = float(secs)
        self.cfg["xfade"] = secs
        self.save_cfg()

    def now_label(self):
        if self.now_q or self.cur is None or not self.cur.tracks:
            return tr("From queue").upper()
        return f"{self.idx + 1:02d} / {len(self.cur.tracks):02d}"

    def set_language(self, code):
        """Switch language live: font, Qt dialogs, every label, menu and list."""
        if code == i18n.lang():
            return
        self.cfg["lang"] = code
        self.save_cfg()
        init_i18n(QApplication.instance(), code, fonts=False)
        self.set_ui_scale(int(self.cfg.get("ui_scale", 100)))
        retranslate_all()
        self.update_now_button()
        self.update_dock_now()
        self.mini_sync()
        self.update_sleep_label()
        self.refresh_queue()
        if self.now_info is not None and self.cur is not None:
            self.overlay.set_now(self.now_info, self.now_label(), None if self.now_q else self.idx)
        self.set_mode(self.mode)       # rebuilds breadcrumbs, group names and empty-state messages

    def set_resume(self, on):
        self.cfg["resume"] = bool(on)
        self.save_cfg()

    # --- library / cache ---
    def busy_scanning(self):
        return any(t is not None and t.isRunning() for t in (self.scanner, self.loader))

    def start(self, choose=False, full=False):
        lib = self.cfg.get("library")
        if choose or not lib or not os.path.isdir(lib):
            lib = QFileDialog.getExistingDirectory(
                self, tr("Where do you keep your music library?"), str(Path.home()))
            if not lib:
                return
            self.cfg["library"] = lib
            self.save_cfg()
            choose = True
        if self.busy_scanning():
            return
        if choose or full:
            shutil.rmtree(CACHE_DIR, ignore_errors=True)
            self.node_map = {}
            self.begin_scan(lib, silent=False)
            return
        tree = load_cache_json(lib)
        if tree is None:
            self.begin_scan(lib, silent=False)
            return
        self.set_plain_header(tr("Loading…").upper())
        self.loader = CacheLoader(tree)
        self.loader.done.connect(self.on_cache)
        self.loader.start()

    def rescan(self):
        lib = self.cfg.get("library")
        if lib and not self.busy_scanning():
            self.begin_scan(lib, silent=False)

    def on_cache(self, root):
        lib = self.cfg.get("library")
        if root is None:
            self.begin_scan(lib, silent=False)
            return
        self.apply_tree(root)
        self.begin_scan(lib, silent=True)   # quiet background refresh

    def begin_scan(self, lib, silent):
        if self.scanner is not None and self.scanner.isRunning():
            return
        self.scan_silent = silent
        self.scan_tree_applied = False
        if not silent:
            self.set_plain_header(tr("Preparing your music library…").upper())
            self.scan_progress = QProgressDialog(
                "NeonPlayer is scanning your music collection and building its library.\n"
                "This might take some time, depending on the size of your collection.",
                "", 0, 0, self)
            self.scan_progress.setWindowTitle("Preparing Your Music Library")
            # Keep the progress dialog stacked above its owning player window.
            # It becomes non-modal once the library is usable, but must remain
            # visible while scanning/caching continues, without blocking the
            # main window. The library itself becomes available when discovery
            # completes; artwork caching then continues in the background.
            self.scan_progress.setWindowFlag(
                Qt.WindowType.WindowStaysOnTopHint, True)
            self.scan_progress.setWindowModality(Qt.WindowModality.NonModal)
            self.scan_progress.setMinimumDuration(0)
            self.scan_progress.setAutoClose(False)
            self.scan_progress.setAutoReset(False)
            self.scan_progress.setCancelButton(None)
            self.scan_progress.show()
            self.scan_progress.raise_()
            self.scan_progress.activateWindow()
        self.scanner = Scanner(lib, self.node_map)
        self.scanner.total.connect(self.on_scan_total)
        self.scanner.count.connect(self.on_scan_count)
        self.scanner.tree_ready.connect(self.on_scan_tree_ready)
        self.scanner.cache_progress.connect(self.on_cache_progress)
        self.scanner.done.connect(self.on_scanned)
        self.scanner.start()

    def on_scan_total(self, total):
        self.scan_total = max(1, total)
        if self.scan_progress is not None:
            self.scan_progress.setRange(0, self.scan_total)
            self.scan_progress.setValue(0)

    def on_scan_count(self, n):
        if not self.scan_silent:
            self.set_plain_header(tr("Scanning… (folders: {n})", n=n).upper())
            if self.scan_progress is not None:
                self.scan_progress.setValue(min(n, self.scan_total))
                self.scan_progress.setLabelText(
                    "NeonPlayer is preparing your music library. This might take some time.\n"
                    f"Scanning folders: {n:,} / {self.scan_total:,}")

    def on_cache_progress(self, done, total, label):
        if self.scan_silent or self.scan_progress is None:
            return
        total = max(1, int(total))
        done = max(0, min(int(done), total))
        self.scan_progress.setRange(0, total)
        self.scan_progress.setValue(done)
        percent = int(done * 100 / total)
        self.scan_progress.setLabelText(
            "Folder scanning is complete. Now preparing your artwork thumbnails.\n"
            "This might take some time, depending on the size of your collection.\n"
            f"{label}  {done:,} / {total:,}  ({percent}%)")
        self.set_plain_header(tr("Caching artwork… ({p}%)", p=percent).upper())

    def on_scan_tree_ready(self, root, changed):
        # Do not build the potentially very large library view while the cache
        # worker is still running. Keep the progress dialog visible in front;
        # publish the completed tree only after scanning and artwork caching end.
        self.scan_tree_applied = False
        if not self.scan_silent and self.scan_progress is not None:
            self.scan_progress.setLabelText(
                "Folder scanning is complete. Preparing artwork thumbnails and finishing your library.\n"
                "This might take some time, depending on the size of your collection.")
            self.scan_progress.raise_()
            self.scan_progress.activateWindow()

    def on_scanned(self, root, changed):
        self.cache_error = self.scanner.cache_error
        if self.scan_silent and not changed:
            return
        # Building the library widgets can itself take time for large libraries.
        # Keep the always-on-top progress window visible until that work is done,
        # then close it so the main window is ready for interaction.
        if not getattr(self, "scan_tree_applied", False):
            if self.scan_progress is not None:
                self.scan_progress.setValue(self.scan_progress.maximum())
                self.scan_progress.setLabelText("Finishing your music library…")
                self.scan_progress.raise_()
                self.scan_progress.activateWindow()
            self.apply_tree(root)
            self.scan_tree_applied = True
        if self.scan_progress is not None:
            self.scan_progress.close()
            self.scan_progress.deleteLater()
            self.scan_progress = None

    def set_plain_header(self, text):
        self.crumb_label.setText(f"<span style='color:#00e5ff;font-size:19px;"
                                 f"font-weight:bold;letter-spacing:2px'>{html.escape(text)}</span>")

    def save_cfg(self):
        try:
            CONFIG.parent.mkdir(parents=True, exist_ok=True)
            tmp = CONFIG.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.cfg, ensure_ascii=False, indent=2))
            os.replace(tmp, CONFIG)
        except OSError as ex:
            print("NeonPlayer: could not save configuration:", ex, file=sys.stderr)

    def apply_tree(self, root):
        self.root = root
        self.all_albums = []
        self.node_map = {}

        def walk(n):
            self.node_map[n.path] = n
            if n.tracks:
                self.all_albums.append(n if not n.children else Node(
                    n.path, n.name, n.tracks, [], n.img, n.artist, n.genre, n.mtime))
            for c in n.children:
                walk(c)
        if root:
            walk(root)
        self.all_albums.sort(key=lambda a: a.name.casefold())
        self.set_mode(self.mode)
        if not self.resumed:
            self.resumed = True
            if self.cfg.get("resume", True):
                self.resume_session()

    # --- views ---
    @staticmethod
    def make_items(node):
        items = list(node.children)
        if node.tracks:
            name = tr("{name} (loose tracks)", name=node.name) if node.children else node.name
            items.insert(0, Node(node.path, name, node.tracks, [], node.img,
                                 node.artist, node.genre, node.mtime))
        return items

    def group(self, mode):
        d = {}
        for a in self.all_albums:
            key = (a.artist if mode == "artists" else a.genre) or (
                tr("Unknown Artist") if mode == "artists" else tr("Unknown Genre"))
            d.setdefault(key, []).append(a)
        out = []
        for k in sorted(d, key=str.casefold):
            kids = d[k]
            img = next((a.img for a in kids if not a.img.isNull()), QImage())
            out.append(Node("", k, [], kids, img))
        return out

    def playlist_nodes(self):
        out = []
        pls = self.cfg.get("playlists", {})
        for name in sorted(pls, key=str.casefold):
            paths = [p for p in pls[name] if os.path.isfile(p)]
            nd = self.node_map.get(os.path.dirname(paths[0])) if paths else None
            out.append(Node("", name, paths, [], nd.img if nd else QImage()))
        return out

    def search_results(self, q):
        ql, out = q.casefold(), []
        for a in self.all_albums:
            hit = -1
            hay = f"{a.name} {a.artist} {a.genre}".casefold()
            if ql not in hay:
                for i, t in enumerate(a.tracks):
                    if ql in Path(t).stem.casefold():
                        hit = i
                        break
                if hit < 0:
                    continue
            out.append(Node(a.path, a.name, a.tracks, [], a.img, a.artist, a.genre, a.mtime, 0.0, False, hit))
            if len(out) >= 300:
                break
        return out

    def set_mode(self, mode):
        self.mode = mode
        for i, (key, _, _) in enumerate(NAV):
            self.nav_group.buttons()[i].setChecked(key == mode)
        self.stack = []
        label = mode
        items, crumbs, msg = [], [label], ""
        if mode == "playlists":
            items = self.playlist_nodes()
            msg = "No playlists yet — add tracks to the queue and press Save…"
        elif self.root is None:
            msg = "No music found in that folder"
        elif mode == "folders":
            items, crumbs = self.make_items(self.root), [label, self.root.name]
        elif mode == "albums":
            items = list(self.all_albums)
        elif mode in ("artists", "genres"):
            items = self.group(mode)
        elif mode == "recent":
            items = sorted(self.all_albums, key=lambda a: -a.mtime)[:100]
        elif mode == "favorites":
            favs = []
            for entry in self.cfg.get("favorites", []):
                if os.path.isfile(entry):
                    favs.append(entry)
                elif os.path.isdir(entry):  # migrate older album-level favorites on display
                    favs.extend(os.path.join(entry, t) for t in os.listdir(entry)
                                if os.path.splitext(t)[1].lower() in AUDIO_EXT)
            items = []
            for fp in favs:
                parent = os.path.dirname(fp)
                name = os.path.basename(fp)
                info = track_info(fp, "", os.path.basename(parent))
                im = cached_track_cover(fp)
                items.append(Node(parent, info["title"], [name], [], im,
                                  info["artist"], "", os.path.getmtime(fp), 0.0))
            msg = "No favorite tracks yet — press ♥ in the player"
        self.show_view(items, crumbs, 0, msg)

    def show_view(self, items, crumbs, scroll=0, msg=""):
        self.items, self.crumbs, self.empty_msg = items, crumbs, msg
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.search_q = ""
        self.shown = items
        self.back_btn.setVisible(bool(self.stack))
        self.build_tiles()
        self.refresh_view()
        QTimer.singleShot(60, lambda: self.scroll.verticalScrollBar().setValue(scroll))

    def run_search(self):
        q = self.search.text().strip()
        active = len(q) >= 2
        if not active and not self.search_q:
            return
        self.search_q = q if active else ""
        self.shown = self.search_results(q) if active else self.items
        self.build_tiles()
        self.refresh_view()

    def build_tiles(self):
        while self.grid.count():
            self.grid.takeAt(0)
        for t in self.tiles:
            t.hide()
            t.deleteLater()
        self.tiles = []
        for n in self.shown:
            t = Tile(n, self.list_mode, self.holder, self.node_tracks)
            t.clicked.connect(self.on_tile)
            t.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            t.customContextMenuRequested.connect(
                lambda pos, t=t: self.tile_menu(t, t.mapToGlobal(pos)))
            self.tiles.append(t)

    def refresh_view(self):
        self.visible = list(self.tiles)
        for t in self.tiles:
            t.show()
        has = bool(self.visible)
        self.scroll.setVisible(has)
        self.msg.setVisible(not has)
        if not has:
            self.msg.setText(tr("No results") if self.search_q else tr(self.empty_msg or "Nothing here"))
        self.focus_idx = -1
        self.reflow()
        if self.pad_active and has:
            self.set_focus(0)
        crumbs = ([tr("Search").upper(), f"“{self.search_q}”"] if self.search_q
                  else [mode_label(self.crumbs[0])] + list(self.crumbs[1:]))
        sep = "<span style='color:#00e5ff'>&nbsp;&nbsp;/&nbsp;&nbsp;</span>"
        parts = [f"<span style='color:#00e5ff;font-size:19px;font-weight:bold;"
                 f"letter-spacing:2px'>{html.escape(crumbs[0])}</span>"]
        parts += [f"<span style='color:#fff;font-size:15px'>{html.escape(c)}</span>" for c in crumbs[1:]]
        parts.append(f"<span style='color:#fff;font-size:15px'>{html.escape(tr('Items: {n}', n=len(self.visible)))}</span>")
        self.crumb_label.setText(sep.join(parts))

    def reflow(self):
        while self.grid.count():
            self.grid.takeAt(0)
        for c in range(self.grid.columnCount()):
            self.grid.setColumnStretch(c, 0)
        if self.list_mode:
            cols = 1
            self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.grid.setColumnStretch(0, 1)
        else:
            cols = max(1, (self.scroll.viewport().width() - 10) // (TILE + 8 + 14))
            self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.cols = cols
        for i, t in enumerate(self.visible):
            self.grid.addWidget(t, i // cols, i % cols)

    def set_list_mode(self, flag):
        if flag == self.list_mode:
            return
        self.list_mode = flag
        self.cfg["list_mode"] = flag
        self.save_cfg()
        self.build_tiles()
        self.refresh_view()

    def on_tile(self, tile):
        n = tile.node
        if n.children:
            self.stack.append((self.items, self.crumbs, self.empty_msg,
                               self.scroll.verticalScrollBar().value()))
            self.show_view(self.make_items(n), self.crumbs + [n.name])
        else:
            self.open_album(n, tile)

    def go_back(self):
        if self.overlay.isVisible() or not self.stack:
            return
        items, crumbs, msg, sv = self.stack.pop()
        self.show_view(items, crumbs, sv, msg)

    def on_escape(self):
        if self.overlay.isVisible():
            self.minimize_overlay()
        elif self.mini_win.isVisible():
            self.toggle_mini()
        else:
            self.go_back()

    # --- controller focus ring ---
    def set_focus(self, i):
        if not self.visible:
            return
        if 0 <= self.focus_idx < len(self.visible):
            old = self.visible[self.focus_idx].cover
            old.focused = False
            old.update()
        self.focus_idx = max(0, min(len(self.visible) - 1, i))
        t = self.visible[self.focus_idx]
        t.cover.focused = True
        t.cover.update()
        self.scroll.ensureWidgetVisible(t, 20, 60)

    # --- queue / playlists ---
    def node_tracks(self, n):
        out = [os.path.join(n.path, t) for t in n.tracks]
        for c in n.children:
            out += self.node_tracks(c)
        return out

    def tile_menu(self, tile, gpos):
        n = tile.node
        m = QMenu(self)
        m.addAction(tr("Add to queue"), lambda: self.enqueue(self.node_tracks(n)))
        m.addAction(tr("Play next"), lambda: self.enqueue(self.node_tracks(n), front=True))
        if self.mode == "playlists":
            m.addSeparator()
            m.addAction(tr("Delete playlist"), lambda: self.delete_playlist(n.name))
        m.exec(gpos)

    def enqueue(self, paths, front=False, at=None):
        infos = [track_info(p, "", os.path.basename(os.path.dirname(p))) for p in paths]
        self.enqueue_infos(infos, front, at)

    def enqueue_infos(self, infos, front=False, at=None):
        if not infos:
            return
        if at is not None:
            self.queue[at:at] = infos
        else:
            self.queue = infos + self.queue if front else self.queue + infos
        self.refresh_queue()
        self.save_queue()
        QToolTip.showText(QCursor.pos(), tr("Tracks added to the queue: {n}", n=len(infos)))

    def queue_dropped(self, paths, row):
        self.enqueue(paths, at=row)

    def refresh_queue(self):
        rows = [(f"{i + 1:02d}", d["title"], fmt(d["length"] * 1000)) for i, d in enumerate(self.queue)]
        self.overlay.set_queue(rows, self.queue)
        self.dock.set_queue(rows, self.queue)
        self.schedule_preload()

    def save_queue(self):
        self.cfg["queue"] = [d["path"] for d in self.queue]
        self.save_cfg()

    def queue_reordered(self, lw):
        self.queue = [lw.item(i).data(UR + 1) for i in range(lw.count())]
        self.refresh_queue()
        self.save_queue()

    def queue_play(self, row):
        if 0 <= row < len(self.queue):
            info = self.queue.pop(row)
            self.refresh_queue()
            self.save_queue()
            self.play_info(info, True)

    def clear_queue(self):
        self.queue = []
        self.refresh_queue()
        self.save_queue()

    def queue_all(self):
        infos = self.pending_tinfo if self.pending_node is not None else self.tinfo
        if infos:
            self.enqueue_infos([dict(d) for d in infos])

    def album_menu(self, pos):
        o = self.overlay
        it = o.panel.itemAt(pos)
        if it is None:
            return
        r = o.panel.row(it)
        m = QMenu(self)
        m.addAction(tr("Play now"), lambda: self.play_index(r))
        infos = self.pending_tinfo if self.pending_node is not None else self.tinfo
        if not (0 <= r < len(infos)):
            return
        m.addAction(tr("Add to queue"), lambda: self.enqueue_infos([dict(infos[r])]))
        m.addAction(tr("Play next"), lambda: self.enqueue_infos([dict(infos[r])], True))
        m.exec(o.panel.viewport().mapToGlobal(pos))

    def queue_menu(self, lw, pos):
        it = lw.itemAt(pos)
        if it is None:
            return
        r = lw.row(it)
        m = QMenu(self)
        m.addAction(tr("Play now"), lambda: self.queue_play(r))
        m.addAction(tr("Move to top"), lambda: self.queue_to_top(r))
        m.addAction(tr("Remove"), lambda: self.queue_remove(r))
        m.exec(lw.viewport().mapToGlobal(pos))

    def queue_to_top(self, r):
        self.queue.insert(0, self.queue.pop(r))
        self.refresh_queue()
        self.save_queue()

    def queue_remove(self, r):
        self.queue.pop(r)
        self.refresh_queue()
        self.save_queue()

    def save_playlist(self):
        if not self.queue:
            QToolTip.showText(QCursor.pos(), tr("The queue is empty"))
            return
        name, ok = QInputDialog.getText(self, tr("Save playlist"), tr("Playlist name:"))
        name = name.strip()
        if ok and name:
            pls = self.cfg.setdefault("playlists", {})
            pls[name] = [d["path"] for d in self.queue]
            self.save_cfg()
            QToolTip.showText(QCursor.pos(), tr("Saved playlist “{name}”", name=name))
            if self.mode == "playlists":
                self.set_mode("playlists")

    def delete_playlist(self, name):
        self.cfg.get("playlists", {}).pop(name, None)
        self.save_cfg()
        self.set_mode("playlists")

    # --- player screen open / minimize / stop ---
    def tile_rect(self):
        t = self.cur_tile
        try:
            if t is not None and t.isVisible():
                cb = t.cover
                return QRect(cb.mapTo(self.central, cb.pr.topLeft()), cb.pr.size())
        except RuntimeError:
            pass
        tr = self.overlay.target_rect()
        s = QRect(0, 0, int(tr.width() * 0.3), int(tr.height() * 0.3))
        s.moveCenter(tr.center())
        return s

    def np_rect(self):
        b = self.np_btn
        side = b.height() - 8
        box = QRect(b.mapTo(self.central, QPoint(10, 4)), QSize(side, side))
        return fit(self.overlay.ar, box)

    def show_cover(self, pm):
        self.cover_pm = pm
        self.overlay.set_cover(pm)

    def update_now_button(self):
        b = self.np_btn
        if self.cur is not None and self.cover_pm is not None:
            b.setIcon(QIcon(self.cover_pm.scaled(
                36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            b.setIconSize(QSize(32, 32))
            b.setText("  " + tr("Now Playing"))
            b.setToolTip(self.now_info["title"] if self.now_info else "")
        else:
            b.setIcon(QIcon())
            b.setText("♫    " + tr("Now Playing"))
            b.setToolTip("")

    def update_dock_now(self):
        i, d = self.now_info, self.dock
        d.title.setText(i["title"] if i else tr("Nothing playing"))
        d.artist.setText((i["artist"] or i["album"]) if i else "")
        if self.cover_pm is not None and i:
            d.thumb.setPixmap(self.cover_pm.scaled(
                72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            d.thumb.clear()

    def write_art(self):
        """Save the current cover for MPRIS (Plasma media widget artwork)."""
        old = self.art_path
        self.art_path = ""
        if self.cover_pm is not None and self.now_info:
            try:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                p = CACHE_DIR / f"now_cover_{self.serial}.jpg"
                self.cover_pm.scaled(512, 512, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation).save(str(p), "JPG", 88)
                self.art_path = str(p)
            except Exception:
                pass
        if old and old != self.art_path:
            try:
                os.remove(old)
            except OSError:
                pass

    def after_track_change(self):
        self.serial += 1
        self.write_art()
        self.update_now_button()
        self.update_dock_now()
        self.mini_sync()
        self.schedule_preload()
        self.save_session()
        self.mpris_notify("Metadata", "PlaybackStatus")

    def present_overlay(self, from_np):
        o = self.overlay
        o.setGraphicsEffect(None)
        o.setGeometry(self.central.rect())
        o.show()
        o.raise_()
        o.cframe.hide()
        o.busy = True
        o.relayout()
        self.setFocus()
        start = self.np_rect() if from_np else self.tile_rect()
        o.cover.setGeometry(start)
        o.cover.show()
        self.blur = QGraphicsBlurEffect()
        self.blur.setBlurRadius(0)
        self.content.setGraphicsEffect(self.blur)
        ueff = QGraphicsOpacityEffect(o.ui)
        ueff.setOpacity(0.0)
        o.ui.setGraphicsEffect(ueff)
        fade = QPropertyAnimation(ueff, b"opacity")
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        self.run_anim(start, o.target_rect(), 0, 28, "open", extra=[fade])

    def begin_session(self, node):
        o = self.overlay
        # Do not interrupt a track merely because the user browses to another album.
        # The new album becomes the play target; playback switches only on Play/track click.
        self.cur = self.last_node = node
        self.pending_node = self.pending_tinfo = None
        img = load_cover(node.path, node.tracks)
        pm = QPixmap.fromImage(img) if not img.isNull() else (
            QPixmap.fromImage(node.img) if not node.img.isNull() else placeholder())
        self.album_pm = self.cover_pm = pm
        self.cover_for_queue = False
        o.set_cover(pm)
        self.tinfo = [track_info(os.path.join(node.path, t), node.artist, node.name)
                      for t in node.tracks]
        o.set_tracks([(f"{i + 1:02d}", d["title"], fmt(d["length"] * 1000))
                      for i, d in enumerate(self.tinfo)], self.tinfo)
        fav = bool(self.now_info and self.now_info.get("path") in self.cfg.get("favorites", []))
        o.fav.setChecked(fav)
        o.fav.setText("♥" if fav else "♡")
        self.played = set()
        self.now_q = False
        self.engine.setVolume(self.volume)
        self.sync_modes()

    def open_album(self, node, tile):
        if self.anim:
            return
        self.cur_tile = tile
        if self.cur is not None and node.path and self.cur.path == node.path and not self.pending_node:
            self.last_node = node
            self.restore_playback_view()
            self.present_overlay(False)
            return
        if self.engine.playbackState() == QMediaPlayer.PlaybackState.PlayingState and self.now_info:
            # Keep the active playback session intact, while visibly opening the
            # selected album as a preview in the player.
            self.pending_node = node
            self.pending_tinfo = [track_info(os.path.join(node.path, t), node.artist, node.name)
                                  for t in node.tracks]
            self.overlay.set_tracks([(f"{i + 1:02d}", d["title"], fmt(d["length"] * 1000))
                                     for i, d in enumerate(self.pending_tinfo)], self.pending_tinfo)
            img = load_cover(node.path, node.tracks)
            pm = QPixmap.fromImage(img) if not img.isNull() else (
                QPixmap.fromImage(node.img) if not node.img.isNull() else placeholder())
            self.overlay.set_cover(pm)
            self.overlay.set_album_preview(node, self.pending_tinfo, self.now_info.get("path") if self.now_info else None)
            self.present_overlay(False)
            return
        self.begin_session(node)
        if node.tracks:
            self.load_index(node.hit if node.hit >= 0 else 0, play=False)
        else:
            self.advance(play=False)
        self.present_overlay(False)

    def start_queue_session(self, play):
        self.begin_session(Node("", "Queue", [], [], QImage()))
        self.advance(play=play)

    def restore_playback_view(self):
        """Restore the actual playing track after viewing another album."""
        if self.now_info is None:
            return
        self.pending_node = self.pending_tinfo = None
        if self.cur is not None and not self.now_q:
            self.overlay.set_tracks(
                [(f"{i + 1:02d}", d["title"], fmt(d["length"] * 1000))
                 for i, d in enumerate(self.tinfo)], self.tinfo)
            row = self.idx if 0 <= self.idx < len(self.tinfo) else None
            self.overlay.set_now(self.now_info, self.now_label(), row)
        else:
            self.overlay.set_tracks([], [])
            self.overlay.set_now(self.now_info, tr("From queue").upper(), None)
        if self.cover_pm is not None:
            self.overlay.set_cover(self.cover_pm)

    def now_playing(self, _=None):
        if self.overlay.isVisible() or self.anim:
            return
        if self.cur is not None:
            self.cur_tile = None
            self.restore_playback_view()
            self.present_overlay(True)
        elif self.queue:
            self.cur_tile = None
            self.start_queue_session(False)
            self.present_overlay(True)
        else:
            QToolTip.showText(QCursor.pos(), tr("Nothing playing — right-click an album to queue it"))

    def minimize_overlay(self):
        """Library button / Esc: keep playing and shrink into the Now Playing button."""
        o = self.overlay
        if not o.isVisible() or self.anim:
            return
        if self.engine.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
            self.stop_and_close()
            return
        o.cframe.hide()
        o.busy = True
        eff = QGraphicsOpacityEffect(o.ui)
        eff.setOpacity(1.0)
        o.ui.setGraphicsEffect(eff)
        fade = QPropertyAnimation(eff, b"opacity")
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        self.run_anim(o.cover.geometry(), self.np_rect(), 28, 0, "minimize", extra=[fade])

    def stop_and_close(self):
        o = self.overlay
        if not o.isVisible() or self.anim:
            return
        o.cframe.hide()
        o.busy = True
        end = self.tile_rect()
        eff = QGraphicsOpacityEffect(o.ui)
        eff.setOpacity(1.0)
        o.ui.setGraphicsEffect(eff)
        fade = QPropertyAnimation(eff, b"opacity")
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        vol = QPropertyAnimation(self.engine, b"volume")
        vol.setStartValue(self.volume)
        vol.setEndValue(0.0)
        self.run_anim(o.cover.geometry(), end, 28, 0, "close_stop", extra=[fade, vol])

    def end_session(self):
        self.engine.clear()
        self.engine.setVolume(self.volume)
        self.cur = self.now_info = None
        self.pending_node = self.pending_tinfo = None
        self.cover_for_queue = False
        self.cfg.pop("session", None)
        self.save_cfg()
        self.update_now_button()
        self.update_dock_now()
        self.mini_sync()
        self.mpris_notify("Metadata", "PlaybackStatus")

    def run_anim(self, g0, g1, b0, b1, mode, extra=()):
        dur = {"open": 450, "minimize": 650, "close_stop": 800}[mode]
        grp = QParallelAnimationGroup(self)
        a = QPropertyAnimation(self.overlay.cover, b"geometry")
        a.setStartValue(g0)
        a.setEndValue(g1)
        b = QPropertyAnimation(self.blur, b"blurRadius")
        b.setStartValue(float(b0))
        b.setEndValue(float(b1))
        for x in (a, b):
            x.setDuration(dur)
            x.setEasingCurve(QEasingCurve.Type.OutCubic)
            grp.addAnimation(x)
        for x in extra:
            x.setDuration(dur)
            x.setEasingCurve(QEasingCurve.Type.InOutQuad)
            grp.addAnimation(x)

        def cleanup():
            self.overlay.setGraphicsEffect(None)
            self.overlay.ui.setGraphicsEffect(None)
            if mode != "open":
                self.content.setGraphicsEffect(None)

        def done():
            self.anim = None
            self.overlay.busy = False
            if mode == "open":
                self.overlay.cframe.show()
            else:
                if mode == "close_stop":
                    self.end_session()
                self.overlay.hide()
                self.grip.raise_()
                self.update_now_button()
            QTimer.singleShot(0, cleanup)
        grp.finished.connect(done)
        self.anim = grp
        grp.start()

    # --- playback ---
    def toggle_fav(self, on):
        if not self.now_info or not self.now_info.get("path"):
            self.overlay.fav.setChecked(False)
            return
        track_path = self.now_info["path"]
        favs = [f for f in self.cfg.get("favorites", []) if f != track_path]
        if on: favs.append(track_path)
        self.cfg["favorites"] = favs
        self.save_cfg()
        self.overlay.fav.setText("♥" if on else "♡")
        if self.mode == "favorites": self.set_mode("favorites")

    def sync_modes(self):
        o = self.overlay
        o.hx_shuffle.active, o.hx_repeat.active = self.shuffle, self.repeat
        o.hx_shuffle.update()
        o.hx_repeat.update()
        o.tool_shuffle.setChecked(self.shuffle)
        o.tool_repeat.setChecked(self.repeat)
        self.schedule_preload()

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self.sync_modes()
        self.mpris_notify("Shuffle")

    def toggle_repeat(self):
        self.repeat = not self.repeat
        self.sync_modes()
        self.mpris_notify("LoopStatus")

    def set_volume(self, v):
        self.volume = v / 100
        if not self.anim and not self.sleep_fading():
            if self.now_info: self.apply_replaygain(self.now_info)
            else: self.engine.setVolume(self.volume)
        self.cfg["volume"] = self.volume
        self.save_cfg()
        self.mpris_notify("Volume")

    def nudge_volume(self, delta):
        v = max(0, min(100, int(round(self.volume * 100)) + delta))
        self.overlay.vol.setValue(v)
        QToolTip.showText(QCursor.pos(), tr("Volume {v}%", v=v))

    def seek_to(self, ms):
        self.engine.setPosition(ms)
        if self.mpris.available:
            self.mpris.seeked(ms * 1000)

    def seek_by(self, delta_ms):
        self.seek_to(max(0, min(self.engine.duration(), self.engine.position() + delta_ms)))

    def peek_next_path(self):
        if self.queue:
            return self.queue[0]["path"]
        if self.cur and self.cur.tracks and not self.shuffle and self.tinfo:
            i = self.idx + 1
            if i < len(self.tinfo):
                return self.tinfo[i]["path"]
            if self.repeat:
                return self.tinfo[0]["path"]
        return None

    def schedule_preload(self):
        if self.cur is None or self.now_info is None:
            return
        p = self.peek_next_path()
        if p:
            self.engine.preload(p)

    def next_index(self):
        if not self.cur or not self.cur.tracks:
            return None
        n = len(self.cur.tracks)
        if self.shuffle:
            self.played.add(self.idx)
            rest = [i for i in range(n) if i not in self.played]
            if not rest:
                if not self.repeat:
                    return None
                self.played = {self.idx}
                rest = [i for i in range(n) if i != self.idx]
            return random.choice(rest) if rest else None
        i = self.idx + 1
        if i < n:
            return i
        return 0 if self.repeat else None

    def advance(self, play=True, crossfade=False):
        """Next track: queued tracks first, then the album continues."""
        if self.queue:
            info = self.queue.pop(0)
            self.refresh_queue()
            self.save_queue()
            self.play_info(info, play, crossfade)
            return True
        n = self.next_index()
        if n is not None:
            self.load_index(n, play, crossfade)
            return True
        return False

    def next_track(self):
        if self.cur is None and self.queue:
            self.start_queue_session(True)
            return
        self.advance()

    def prev_track(self):
        if self.engine.position() > 3000 or self.now_q or self.idx == 0:
            self.engine.setPosition(0)
        else:
            self.load_index(self.idx - 1, True)

    def apply_replaygain(self, info):
        mode=self.cfg.get("replaygain_mode", "off")
        gain=info.get("rg_track") if mode=="track" else info.get("rg_album") if mode=="album" else None
        if gain is None and mode=="album": gain=info.get("rg_track")
        if gain is None and mode=="track": gain=info.get("rg_album")
        if gain is None:
            gain=0.0  # Missing tags: preserve the user's normal volume unchanged.
        try: factor=10 ** (float(gain)/20.0)
        except Exception: factor=1.0
        peak=info.get("rg_album_peak") if mode=="album" else info.get("rg_peak")
        if peak is None: peak=info.get("rg_peak") or info.get("rg_album_peak")
        if peak and peak>0: factor=min(factor,1.0/float(peak))
        self.engine.setVolume(min(1.0,self.volume*factor))

    def load_index(self, i, play, crossfade=False, start=None):
        a = self.cur
        if not a or not (0 <= i < len(a.tracks)):
            return
        self.idx = i
        self.played.add(i)
        self.now_q = False
        info = self.tinfo[i]
        self.now_info = info
        if self.cover_for_queue and self.album_pm is not None:
            self.cover_for_queue = False
            self.show_cover(self.album_pm)
        self.apply_replaygain(info)
        self.engine.load(info["path"], play, crossfade, start)
        art = cached_track_cover(info["path"], self.album_pm.toImage() if self.album_pm else None)
        if not art.isNull():
            self.show_cover(QPixmap.fromImage(art))
        self.overlay.set_now(info, f"{i + 1:02d} / {len(a.tracks):02d}", i)
        fav = info["path"] in self.cfg.get("favorites", [])
        self.overlay.fav.setChecked(fav)
        self.overlay.fav.setText("♥" if fav else "♡")
        self.after_track_change()

    def play_index(self, i):
        if self.pending_node is not None:
            node = self.pending_node
            self.begin_session(node)
        self.load_index(i, True)

    def play_info(self, info, play=True, crossfade=False, start=None):
        self.now_q = True
        self.now_info = info
        self.apply_replaygain(info)
        self.engine.load(info["path"], play, crossfade, start)
        art = cached_track_cover(info["path"], self.album_pm.toImage() if self.album_pm else None)
        if not art.isNull():
            self.show_cover(QPixmap.fromImage(art))
        self.overlay.set_now(info, tr("From queue").upper(), None)
        img = load_cover(os.path.dirname(info["path"]), [os.path.basename(info["path"])])
        if not img.isNull():
            self.cover_for_queue = True
            self.show_cover(QPixmap.fromImage(img))
        self.after_track_change()

    def play_any(self):
        if self.engine.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            return
        if self.pending_node is not None and self.pending_node.tracks:
            node = self.pending_node
            self.begin_session(node)
            self.load_index(node.hit if node.hit >= 0 else 0, True)
        elif self.cur is not None and self.now_info is not None:
            self.engine.play()
        elif self.queue:
            self.start_queue_session(True)

    def toggle_play(self):
        if self.engine.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.engine.pause()
        else:
            self.play_any()

    def on_state(self, s):
        playing = s == QMediaPlayer.PlaybackState.PlayingState
        o = self.overlay
        o.hx_play.kind = "pause" if playing else "play"
        o.hx_play.update()
        o.spec.playing = o.mini.playing = playing
        self.np_btn.set_pulse(playing)
        self.dock.play.setText("❚❚" if playing else "▶")
        self.mini_win.set_playing(playing)
        if not playing:
            self.save_session()
        self.mpris_notify("PlaybackStatus")

    def show_lyrics(self):
        if not self.now_info: return
        lyrics=self.now_info.get("lyrics", "")
        path=Path(self.now_info["path"])
        lrc=path.with_suffix(".lrc")
        if lrc.is_file():
            try: lyrics=lrc.read_text(encoding="utf-8-sig")
            except Exception: pass
        self.lyrics_win.set_lyrics(lyrics)
        self.lyrics_win.offset.setValue(int(self.cfg.get("lyrics_offset_ms", 0)))
        self.lyrics_win.setWindowTitle("NeonPlayer · "+self.now_info.get("title","Lyrics"))
        self.lyrics_win.show(); self.lyrics_win.raise_(); self.lyrics_win.activateWindow()
        self.sync_lyrics()
    def save_lyrics_offset(self, value):
        self.cfg["lyrics_offset_ms"]=int(value); self.save_cfg()
    def sync_lyrics(self):
        if self.lyrics_win.isVisible(): self.lyrics_win.update_position(self.engine.position())
    def on_pos(self, p):
        o, d = self.overlay, self.dock
        if hasattr(self, "lyrics_win") and self.lyrics_win.isVisible(): self.lyrics_win.update_position(p)
        if not o.slider.isSliderDown():
            o.slider.setValue(p)
        o.pos.setText(fmt(p))
        dur = self.engine.duration()
        if not d.seek.isSliderDown():
            d.seek.setValue(p)
        d.time.setText(f"{fmt(p)} / {fmt(dur)}")
        self.mini_win.set_pos(p, dur)

    def on_dur(self, dd):
        self.overlay.slider.setRange(0, dd)
        self.overlay.dur.setText(fmt(dd))
        self.dock.seek.setRange(0, dd)

    def on_media_error(self, message):
        self.statusBar().showMessage(tr("Playback error: {error}", error=message), 8000)
        QToolTip.showText(QCursor.pos(), tr("Could not play this track: {error}", error=message))

    def on_ended(self):
        if not self.cur:
            return
        if self.sleep_eot:
            self.set_sleep(0, False)
            return
        self.advance()

    def on_near_end(self):
        if not self.cur or self.sleep_eot:
            return
        self.advance(True, True)

    # --- resume last session ---
    def save_session(self):
        if not self.cur or not self.now_info:
            return
        s = {"pos": int(self.engine.position()), "idx": self.idx, "q": self.now_q,
             "track": self.now_info["path"]}
        if self.cur.path:
            s.update(kind="album", key=self.cur.path)
        elif self.cur.name != "Queue":
            s.update(kind="playlist", key=self.cur.name)
        else:
            return
        self.cfg["session"] = s
        self.save_cfg()

    def resume_session(self):
        s = self.cfg.get("session")
        if not s or self.cur is not None:
            return
        if s.get("kind") == "album":
            node = next((a for a in self.all_albums if a.path == s["key"]), None)
        else:
            node = next((n for n in self.playlist_nodes() if n.name == s.get("key")), None)
        if node is None or not node.tracks:
            return
        self.begin_session(node)
        if s.get("q") and os.path.isfile(s.get("track", "")):
            self.play_info(track_info(s["track"], "", os.path.basename(os.path.dirname(s["track"]))),
                           False, start=s.get("pos", 0))
        else:
            self.load_index(min(int(s.get("idx", 0)), len(node.tracks) - 1), False, start=s.get("pos", 0))
        self.on_pos(int(s.get("pos", 0)))

    # --- sleep timer ---
    def sleep_fading(self):
        return self.sleep_anim is not None and self.sleep_anim.state() == QPropertyAnimation.State.Running

    def fill_sleep_menu(self, m):
        a = m.addAction(tr("Off"))
        a.setCheckable(True)
        a.setChecked(not self.sleep_eot and self.sleep_left <= 0)
        a.triggered.connect(lambda: self.set_sleep(0, False))
        for mins in (15, 30, 45, 60, 90):
            a = m.addAction(tr("{n} min", n=mins))
            a.triggered.connect(lambda _, mn=mins: self.set_sleep(mn, False))
        a = m.addAction(tr("End of this track"))
        a.setCheckable(True)
        a.setChecked(self.sleep_eot)
        a.triggered.connect(lambda: self.set_sleep(0, True))

    def sleep_menu(self, gpos):
        m = QMenu(self)
        self.fill_sleep_menu(m)
        m.exec(gpos)

    def set_sleep(self, minutes, eot):
        self.sleep_eot = eot
        self.sleep_left = minutes * 60
        if minutes or eot:
            self.sleep_timer.start()
        else:
            self.sleep_timer.stop()
        self.update_sleep_label()

    def update_sleep_label(self):
        txt = ""
        if self.sleep_eot:
            txt = "☾ " + tr("end of track")
        elif self.sleep_left > 0:
            txt = f"☾ {self.sleep_left // 60}:{self.sleep_left % 60:02d}"
        self.overlay.sleep_lbl.setText(txt)
        self.overlay.sleep_lbl.setVisible(bool(txt))

    def sleep_tick(self):
        if self.sleep_left > 0:
            self.sleep_left -= 1
            if self.sleep_left <= 0:
                self.sleep_timer.stop()
                self.sleep_fire()
        self.update_sleep_label()

    def sleep_fire(self):
        a = QPropertyAnimation(self.engine, b"volume")
        a.setStartValue(self.volume)
        a.setEndValue(0.0)
        a.setDuration(8000)

        def done():
            self.engine.pause()
            self.engine.setVolume(self.volume)
        a.finished.connect(done)
        self.sleep_anim = a
        a.start()

    # --- MPRIS (media keys, Plasma media widget) ---
    def mpris_notify(self, *props):
        if self.mpris.available:
            self.mpris.notify(*props)

    def m_status(self):
        st = self.engine.playbackState()
        if self.cur is None or self.now_info is None:
            return "Stopped"
        return {QMediaPlayer.PlaybackState.PlayingState: "Playing",
                QMediaPlayer.PlaybackState.PausedState: "Paused"}.get(st, "Stopped")

    def m_meta(self):
        i = self.now_info
        if not i:
            return None
        return {"id": self.serial, "title": i["title"], "artists": [i["artist"]] if i["artist"] else [],
                "album": i["album"], "length_us": int(i["length"] * 1_000_000), "art": self.art_path}

    def m_position_us(self):
        return self.engine.position() * 1000

    def m_volume(self):
        return self.volume

    def m_loop(self):
        return "Playlist" if self.repeat else "None"

    def m_shuffle(self):
        return self.shuffle

    def m_play(self):
        self.play_any()

    def m_pause(self):
        self.engine.pause()

    def m_playpause(self):
        self.toggle_play()

    def m_stop(self):
        self.engine.stop()

    def m_next(self):
        self.next_track()

    def m_previous(self):
        self.prev_track()

    def m_seek(self, off_us):
        self.seek_by(int(off_us // 1000))

    def m_set_position(self, us):
        self.seek_to(int(us // 1000))

    def m_set_volume(self, v):
        self.overlay.vol.setValue(int(max(0.0, min(1.0, v)) * 100))

    def m_set_loop(self, s):
        if (s != "None") != self.repeat:
            self.toggle_repeat()

    def m_set_shuffle(self, b):
        if bool(b) != self.shuffle:
            self.toggle_shuffle()

    def m_raise(self):
        if self.mini_win.isVisible():
            self.toggle_mini()
        self.show()
        self.raise_()
        self.activateWindow()

    def m_quit(self):
        self.close()

    # --- controller (Xbox / XInput layout) ---
    def on_pad_connected(self, name):
        self.pad_name = name
        self.pad_chip.setVisible(bool(name))
        self.pad_chip.setToolTip(name)
        if name:
            QToolTip.showText(QCursor.pos(), tr("Controller connected: {name}", name=name))

    def pad_context(self):
        if QApplication.activeWindow() is None:
            return None
        if self.overlay.isVisible():
            return "player"
        if self.mini_win.isVisible():
            return "mini"
        return "browser"

    def on_pad_button(self, b):
        ctx = self.pad_context()
        if ctx is None:
            return
        o = self.overlay
        if ctx == "player":
            {"a": self.toggle_play, "b": self.minimize_overlay, "x": self.toggle_shuffle,
             "y": o.fav.click, "lb": self.prev_track, "rb": self.next_track,
             "start": self.toggle_mini, "back": self.toggle_repeat, "l3": o.list_btn.click,
             "r3": lambda: self.sleep_menu(QCursor.pos())}.get(b, lambda: None)()
        elif ctx == "mini":
            {"a": self.toggle_play, "b": self.toggle_mini, "start": self.toggle_mini,
             "lb": self.prev_track, "rb": self.next_track}.get(b, lambda: None)()
        else:
            self.pad_active = True
            if self.focus_idx < 0 and self.visible:
                self.set_focus(0)
            t = self.visible[self.focus_idx] if 0 <= self.focus_idx < len(self.visible) else None
            keys = [k for k, _, _ in NAV]
            if b == "a" and t:
                self.on_tile(t)
            elif b == "b":
                self.go_back()
            elif b == "x" and t:
                self.enqueue(self.node_tracks(t.node))
            elif b == "y" and t:
                self.enqueue(self.node_tracks(t.node), front=True)
            elif b in ("lb", "rb"):
                self.set_mode(keys[(keys.index(self.mode) + (1 if b == "rb" else -1)) % len(keys)])
            elif b == "start":
                self.now_playing()
            elif b == "back":
                self.toggle_play()
            elif b == "guide":
                self.toggle_mini()
            elif b == "l3":
                self.dock_btn.click()

    def on_pad_dir(self, d):
        ctx = self.pad_context()
        if ctx is None:
            return
        if ctx in ("player", "mini"):
            {"left": lambda: self.seek_by(-10000), "right": lambda: self.seek_by(10000),
             "up": lambda: self.nudge_volume(5), "down": lambda: self.nudge_volume(-5)}[d]()
            return
        self.pad_active = True
        if not self.visible:
            return
        if self.focus_idx < 0:
            self.set_focus(0)
            return
        i, c, n = self.focus_idx, self.cols, len(self.visible)
        if d == "left":
            i -= 1
        elif d == "right":
            i += 1
        elif d == "up":
            i -= c
        elif d == "down":
            i = min(i + c, n - 1) if i + c < n or (i // c) < ((n - 1) // c) else i
        self.set_focus(max(0, min(n - 1, i)))

    def on_pad_trigger(self, t):
        if self.pad_context() is not None:
            self.nudge_volume(5 if t == "rt" else -5)

    def on_pad_scroll(self, v):
        if self.pad_context() == "browser":
            sb = self.scroll.verticalScrollBar()
            sb.setValue(sb.value() + int(v * 28))


HELP = f"""NeonPlayer
  --install-desktop     add NeonPlayer to the application menu (uses this AppImage's current location)
  --uninstall-desktop   remove that menu entry
  --data-dir            print where config, cache and playlists are stored
Data folder: {DATA_DIR}"""


def desktop_integration(install):
    f = Path.home() / ".local/share/applications/neonplayer.desktop"
    if not install:
        f.unlink(missing_ok=True)
        print("Removed", f)
        return
    appimage = os.environ.get("APPIMAGE")
    exec_cmd = appimage if appimage else str(APP_DIR / "run.sh")
    icon = DATA_DIR / "neonplayer.png"          # must outlive the AppImage's temporary mount
    try:
        shutil.copy2(APP_DIR / "neonplayer.png", icon)
    except OSError:
        pass
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("[Desktop Entry]\nType=Application\nName=NeonPlayer\n"
                 "Comment=Cyberpunk album-grid music player\n"
                 f"Exec=\"{exec_cmd}\"\nIcon={icon}\nTerminal=false\n"
                 "Categories=AudioVideo;Audio;Player;\nKeywords=music;player;flac;mp3;\n")
    print("Installed", f, "->", exec_cmd)


def _cli():
    a = sys.argv[1:]
    if "--install-desktop" in a or "--uninstall-desktop" in a:
        desktop_integration("--install-desktop" in a)
    elif "--data-dir" in a:
        print(DATA_DIR)
    elif "--help" in a or "-h" in a:
        print(HELP)
    else:
        return False
    return True


if __name__ == "__main__":
    if _cli():
        sys.exit(0)
    app = QApplication(sys.argv)
    try:
        _lang = json.loads(CONFIG.read_text()).get("lang", "en")
    except Exception:
        _lang = "en"
    init_i18n(app, _lang)                       # default: English
    app.setApplicationName("NeonPlayer")
    app.setDesktopFileName("neonplayer")        # groups the window with the launcher / pinned icon
    icon_file = APP_DIR / "neonplayer.png"
    if icon_file.exists():
        app.setWindowIcon(QIcon(str(icon_file)))
    w = Main()
    w.show()
    sys.exit(app.exec())
