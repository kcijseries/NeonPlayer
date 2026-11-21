"""MPRIS2 service so KDE media keys, the Plasma media widget and `playerctl` work.

`ctl` must provide:
  m_status() -> "Playing" | "Paused" | "Stopped"
  m_meta() -> None | {"id", "title", "artists", "album", "length_us", "art"}
  m_position_us(), m_volume(), m_loop(), m_shuffle()
  m_play(), m_pause(), m_playpause(), m_stop(), m_next(), m_previous()
  m_seek(offset_us), m_set_position(us), m_set_volume(v), m_set_loop(str),
  m_set_shuffle(bool), m_raise(), m_quit()
Everything is optional: if QtDBus or a session bus is missing, `available` is False.
"""
import os
import sys

from PyQt6.QtCore import QMetaType, QObject, QUrl, pyqtProperty, pyqtSlot

try:
    from PyQt6.QtCore import pyqtClassInfo
    from PyQt6.QtDBus import (QDBusAbstractAdaptor, QDBusArgument, QDBusConnection,
                              QDBusMessage, QDBusObjectPath)
    HAVE = True
except Exception:
    HAVE = False

OBJ = "/org/mpris/MediaPlayer2"
NO_TRACK = "/org/mpris/MediaPlayer2/TrackList/NoTrack"

ROOT_XML = """  <interface name="org.mpris.MediaPlayer2">
    <method name="Raise"/><method name="Quit"/>
    <property name="CanQuit" type="b" access="read"/>
    <property name="CanRaise" type="b" access="read"/>
    <property name="HasTrackList" type="b" access="read"/>
    <property name="Identity" type="s" access="read"/>
    <property name="DesktopEntry" type="s" access="read"/>
    <property name="SupportedUriSchemes" type="as" access="read"/>
    <property name="SupportedMimeTypes" type="as" access="read"/>
  </interface>"""

PLAYER_XML = """  <interface name="org.mpris.MediaPlayer2.Player">
    <method name="Next"/><method name="Previous"/><method name="Pause"/>
    <method name="PlayPause"/><method name="Stop"/><method name="Play"/>
    <method name="Seek"><arg direction="in" name="Offset" type="x"/></method>
    <method name="SetPosition"><arg direction="in" name="TrackId" type="o"/>
      <arg direction="in" name="Position" type="x"/></method>
    <signal name="Seeked"><arg name="Position" type="x"/></signal>
    <property name="PlaybackStatus" type="s" access="read"/>
    <property name="LoopStatus" type="s" access="readwrite"/>
    <property name="Rate" type="d" access="read"/>
    <property name="Shuffle" type="b" access="readwrite"/>
    <property name="Metadata" type="a{sv}" access="read"/>
    <property name="Volume" type="d" access="readwrite"/>
    <property name="Position" type="x" access="read"/>
    <property name="MinimumRate" type="d" access="read"/>
    <property name="MaximumRate" type="d" access="read"/>
    <property name="CanGoNext" type="b" access="read"/>
    <property name="CanGoPrevious" type="b" access="read"/>
    <property name="CanPlay" type="b" access="read"/>
    <property name="CanPause" type="b" access="read"/>
    <property name="CanSeek" type="b" access="read"/>
    <property name="CanControl" type="b" access="read"/>
  </interface>"""


def _str_array(items):
    a = QDBusArgument()
    a.beginArray(QMetaType.Type.QString.value)
    for s in items:
        a.add(str(s))
    a.endArray()
    return a


def _i64(v):
    a = QDBusArgument()
    a.add(int(v), QMetaType.Type.LongLong.value)
    return a


def typed_meta(m):
    if not m:
        return {"mpris:trackid": QDBusObjectPath(NO_TRACK)}
    d = {"mpris:trackid": QDBusObjectPath(f"/org/neonplayer/track/{m['id']}"),
         "xesam:title": m["title"], "xesam:album": m["album"],
         "xesam:artist": _str_array(m["artists"]),
         "mpris:length": _i64(m["length_us"])}
    if m.get("art"):
        d["mpris:artUrl"] = QUrl.fromLocalFile(m["art"]).toString()
    return d


if HAVE:
    @pyqtClassInfo("D-Bus Introspection", ROOT_XML)
    @pyqtClassInfo("D-Bus Interface", "org.mpris.MediaPlayer2")
    class _Root(QDBusAbstractAdaptor):
        def __init__(self, holder, ctl):
            super().__init__(holder)
            self.ctl = ctl

        @pyqtSlot()
        def Raise(self):
            self.ctl.m_raise()

        @pyqtSlot()
        def Quit(self):
            self.ctl.m_quit()

        @pyqtProperty(bool)
        def CanQuit(self):
            return True

        @pyqtProperty(bool)
        def CanRaise(self):
            return True

        @pyqtProperty(bool)
        def HasTrackList(self):
            return False

        @pyqtProperty(str)
        def Identity(self):
            return "NeonPlayer"

        @pyqtProperty(str)
        def DesktopEntry(self):
            return "neonplayer"

        @pyqtProperty("QStringList")
        def SupportedUriSchemes(self):
            return ["file"]

        @pyqtProperty("QStringList")
        def SupportedMimeTypes(self):
            return ["audio/mpeg", "audio/flac", "audio/ogg", "audio/x-wav", "audio/mp4"]

    @pyqtClassInfo("D-Bus Introspection", PLAYER_XML)
    @pyqtClassInfo("D-Bus Interface", "org.mpris.MediaPlayer2.Player")
    class _Player(QDBusAbstractAdaptor):
        def __init__(self, holder, ctl):
            super().__init__(holder)
            self.ctl = ctl

        @pyqtSlot()
        def Next(self):
            self.ctl.m_next()

        @pyqtSlot()
        def Previous(self):
            self.ctl.m_previous()

        @pyqtSlot()
        def Pause(self):
            self.ctl.m_pause()

        @pyqtSlot()
        def PlayPause(self):
            self.ctl.m_playpause()

        @pyqtSlot()
        def Stop(self):
            self.ctl.m_stop()

        @pyqtSlot()
        def Play(self):
            self.ctl.m_play()

        @pyqtSlot("qlonglong")
        def Seek(self, offset):
            self.ctl.m_seek(offset)

        @pyqtSlot(QDBusObjectPath, "qlonglong")
        def SetPosition(self, track, pos):
            self.ctl.m_set_position(pos)

        @pyqtProperty(str)
        def PlaybackStatus(self):
            return self.ctl.m_status()

        def _get_loop(self):
            return self.ctl.m_loop()

        def _set_loop(self, v):
            self.ctl.m_set_loop(v)
        LoopStatus = pyqtProperty(str, _get_loop, _set_loop)

        @pyqtProperty(float)
        def Rate(self):
            return 1.0

        @pyqtProperty(float)
        def MinimumRate(self):
            return 1.0

        @pyqtProperty(float)
        def MaximumRate(self):
            return 1.0

        def _get_shuffle(self):
            return self.ctl.m_shuffle()

        def _set_shuffle(self, v):
            self.ctl.m_set_shuffle(bool(v))
        Shuffle = pyqtProperty(bool, _get_shuffle, _set_shuffle)

        @pyqtProperty("QVariantMap")
        def Metadata(self):
            return typed_meta(self.ctl.m_meta())

        def _get_vol(self):
            return float(self.ctl.m_volume())

        def _set_vol(self, v):
            self.ctl.m_set_volume(float(v))
        Volume = pyqtProperty(float, _get_vol, _set_vol)

        @pyqtProperty("qlonglong")
        def Position(self):
            return int(self.ctl.m_position_us())

        @pyqtProperty(bool)
        def CanGoNext(self):
            return True

        @pyqtProperty(bool)
        def CanGoPrevious(self):
            return True

        @pyqtProperty(bool)
        def CanPlay(self):
            return True

        @pyqtProperty(bool)
        def CanPause(self):
            return True

        @pyqtProperty(bool)
        def CanSeek(self):
            return True

        @pyqtProperty(bool)
        def CanControl(self):
            return True


class MprisService:
    def __init__(self, ctl, name="neonplayer"):
        self.ctl, self.available, self.name = ctl, False, ""
        if not HAVE:
            return
        try:
            bus = QDBusConnection.sessionBus()
            if not bus.isConnected():
                return
            self.holder = QObject()
            self.root = _Root(self.holder, ctl)
            self.player = _Player(self.holder, ctl)
            svc = f"org.mpris.MediaPlayer2.{name}"
            ok = bus.registerService(svc)
            if not ok:
                svc = f"{svc}.instance{os.getpid()}"
                ok = bus.registerService(svc)
            ok = ok and bus.registerObject(OBJ, self.holder,
                                           QDBusConnection.RegisterOption.ExportAdaptors)
            self.available, self.name = bool(ok), svc
        except Exception as ex:
            print("NeonPlayer: MPRIS unavailable:", ex, file=sys.stderr)

    def _value(self, prop):
        c = self.ctl
        return {"PlaybackStatus": c.m_status, "Metadata": lambda: typed_meta(c.m_meta()),
                "Volume": c.m_volume, "LoopStatus": c.m_loop,
                "Shuffle": c.m_shuffle}[prop]()

    def notify(self, *props):
        """Emit PropertiesChanged for the given Player properties."""
        if not self.available:
            return
        try:
            invalid = QDBusArgument()
            invalid.beginArray(QMetaType.Type.QString.value)
            invalid.endArray()
            msg = QDBusMessage.createSignal(OBJ, "org.freedesktop.DBus.Properties",
                                            "PropertiesChanged")
            msg.setArguments(["org.mpris.MediaPlayer2.Player",
                              {p: self._value(p) for p in props}, invalid])
            QDBusConnection.sessionBus().send(msg)
        except Exception as ex:
            print("NeonPlayer: MPRIS notify failed:", ex, file=sys.stderr)

    def seeked(self, pos_us):
        if not self.available:
            return
        try:
            msg = QDBusMessage.createSignal(OBJ, "org.mpris.MediaPlayer2.Player", "Seeked")
            msg.setArguments([_i64(pos_us)])
            QDBusConnection.sessionBus().send(msg)
        except Exception:
            pass
