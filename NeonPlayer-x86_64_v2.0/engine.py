"""NeonPlayer audio engine.

Two QMediaPlayers give crossfade and gapless playback; a QAudioBufferOutput tap
feeds a numpy FFT analyzer for the real-time spectrum. Everything optional
(numpy / QAudioBufferOutput) degrades gracefully.
"""
import math
import time

from PyQt6.QtCore import QObject, QUrl, QVariantAnimation, pyqtProperty, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

try:
    from PyQt6.QtMultimedia import QAudioBufferOutput, QAudioFormat
except Exception:                                   # older Qt
    QAudioBufferOutput = QAudioFormat = None
try:
    import numpy as np
except Exception:
    np = None

PS = QMediaPlayer.PlaybackState
MS = QMediaPlayer.MediaStatus


class Analyzer:
    """Audio buffer -> list of `bands` levels (0..1), log-spaced 40 Hz .. 16 kHz."""
    N = 2048

    def __init__(self, bands=44):
        self.bands = bands
        self.sr = 0
        self.win = np.hanning(self.N).astype(np.float32)

    def _setup(self, sr):
        freqs = np.fft.rfftfreq(self.N, 1.0 / sr)
        edges = np.geomspace(40.0, min(16000.0, sr / 2.0 - 1.0), self.bands + 1)
        idx = np.maximum.accumulate(np.searchsorted(freqs, edges))
        self.lo = idx[:-1]
        self.hi = np.maximum(idx[1:], self.lo + 1)
        mid = np.sqrt(edges[:-1] * edges[1:])
        self.tilt = (3.0 * np.log2(mid / 1000.0)).astype(np.float32)   # +3 dB/octave
        self.sr = sr

    def process(self, buf):
        fmt = buf.format()
        sr, ch, sf = fmt.sampleRate(), max(1, fmt.channelCount()), fmt.sampleFormat()
        ptr = buf.constData()
        ptr.setsize(buf.byteCount())
        raw = bytes(ptr)
        SF = QAudioFormat.SampleFormat
        if sf == SF.Int16:
            x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
        elif sf == SF.Int32:
            x = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
        elif sf == SF.Float:
            x = np.frombuffer(raw, dtype="<f4")
        elif sf == SF.UInt8:
            x = (np.frombuffer(raw, dtype="u1").astype(np.float32) - 128.0) / 128.0
        else:
            return None
        if ch > 1:
            x = x[: len(x) // ch * ch].reshape(-1, ch).mean(axis=1)
        if len(x) < 64 or sr <= 0:
            return None
        x = x[-self.N:] if len(x) >= self.N else np.pad(x, (self.N - len(x), 0))
        if sr != self.sr:
            self._setup(sr)
        spec = np.abs(np.fft.rfft(x * self.win)) / (self.N / 4.0)
        lv = np.array([spec[l:h].max() for l, h in zip(self.lo, self.hi)], dtype=np.float32)
        db = 20.0 * np.log10(lv + 1e-6) + self.tilt
        return np.clip((db + 75.0) / 70.0, 0.0, 1.0).tolist()


class Engine(QObject):
    positionChanged = pyqtSignal(int)
    durationChanged = pyqtSignal(int)
    stateChanged = pyqtSignal(object)
    ended = pyqtSignal()        # the active track finished on its own
    nearEnd = pyqtSignal()      # time to start a crossfade into the next track

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pl = [QMediaPlayer(), QMediaPlayer()]
        self.ao = [QAudioOutput(), QAudioOutput()]
        self.f = [1.0, 0.0]          # per-player fade factor
        self.act = 0                 # active player
        self.master = 0.7
        self.xfade = 0.0             # crossfade seconds (0 = gapless only)
        self.fading = False
        self.fade_old = None
        self.fade_anim = None
        self.pre = None              # (slot, path) preloaded on the idle player
        self._ne = False             # nearEnd already sent for this track
        self._pending = None         # start position to apply once loaded
        self.lv, self.lv_t = None, 0.0
        self.an = None
        for i in (0, 1):
            self.pl[i].setAudioOutput(self.ao[i])
            self.pl[i].positionChanged.connect(lambda p, i=i: self._pos(i, p))
            self.pl[i].durationChanged.connect(lambda d, i=i: self._dur(i, d))
            self.pl[i].mediaStatusChanged.connect(lambda s, i=i: self._status(i, s))
            self.pl[i].playbackStateChanged.connect(lambda s, i=i: self._state(i, s))
        self._apply()
        self._init_tap()

    # --- spectrum tap ---
    def _init_tap(self):
        self.tap = [None, None]
        if QAudioBufferOutput is None or np is None:
            return
        try:
            self.an = Analyzer(44)
            for i in (0, 1):
                t = QAudioBufferOutput(self)
                self.pl[i].setAudioBufferOutput(t)
                t.audioBufferReceived.connect(lambda b, i=i: self._buf(i, b))
                self.tap[i] = t
        except Exception as ex:
            print("NeonPlayer: spectrum tap unavailable:", ex)
            self.an = None

    def _buf(self, i, buf):
        if i != self.act or self.an is None:
            return
        try:
            lv = self.an.process(buf)
        except Exception:
            lv = None
        if lv:
            self.lv, self.lv_t = lv, time.monotonic()

    def spectrum(self):
        """Latest real FFT levels, or None if no fresh audio data is arriving."""
        if self.lv is not None and time.monotonic() - self.lv_t < 0.3:
            return self.lv
        return None

    # --- volume ---
    def _apply(self):
        for i in (0, 1):
            self.ao[i].setVolume(self.master * self.f[i])

    def _get_volume(self):
        return self.master

    def _set_volume(self, v):
        self.master = max(0.0, min(1.0, float(v)))
        self._apply()
    volume = pyqtProperty(float, _get_volume, _set_volume)

    def setVolume(self, v):
        self._set_volume(v)

    # --- forwarded signals ---
    def _pos(self, i, p):
        if i != self.act:
            return
        self.positionChanged.emit(p)
        if self.xfade > 0 and not self.fading and not self._ne:
            d = self.pl[i].duration()
            if (d > self.xfade * 2500 and d - p <= self.xfade * 1000
                    and self.pl[i].playbackState() == PS.PlayingState):
                self._ne = True
                self.nearEnd.emit()

    def _dur(self, i, d):
        if i == self.act:
            self.durationChanged.emit(d)

    def _state(self, i, s):
        if i == self.act:
            self.stateChanged.emit(s)

    def _status(self, i, s):
        if i != self.act:
            return
        if s in (MS.LoadedMedia, MS.BufferedMedia) and self._pending is not None:
            p, self._pending = self._pending, None
            self.pl[i].setPosition(int(p))
        elif s == MS.EndOfMedia and not self.fading:
            self.ended.emit()

    # --- loading ---
    def load(self, path, play=False, crossfade=False, start=None):
        url = QUrl.fromLocalFile(path)
        self._pending = start
        self._ne = False
        other = 1 - self.act
        cf = (crossfade and self.xfade > 0 and not self.fading
              and self.pl[self.act].playbackState() == PS.PlayingState)
        if cf:
            if self.pre != (other, path):
                self.pl[other].setSource(url)
            self.pre = None
            self.f[other] = 0.0
            self._apply()
            old, self.act = self.act, other
            self.pl[other].play()
            self._start_fade(old, other)
            return
        self._cancel_fade()
        if self.pre == (other, path):
            old, self.act, self.pre = self.act, other, None
            self.pl[old].stop()
            self.f = [1.0, 0.0] if self.act == 0 else [0.0, 1.0]
            self._apply()
            self.durationChanged.emit(self.pl[self.act].duration())
        else:
            self.pre = None
            self.pl[self.act].setSource(url)
        if play:
            self.pl[self.act].play()

    def preload(self, path):
        """Load the upcoming track on the idle player so the switch is gapless."""
        other = 1 - self.act
        if self.fading or self.pre == (other, path):
            return
        if self.pl[other].playbackState() == PS.PlayingState:
            return
        self.pl[other].setSource(QUrl.fromLocalFile(path))
        self.pre = (other, path)

    # --- crossfade ---
    def _start_fade(self, old, new):
        self.fading, self.fade_old = True, old
        a = QVariantAnimation(self)
        a.setDuration(int(self.xfade * 1000))
        a.setStartValue(0.0)
        a.setEndValue(1.0)
        a.valueChanged.connect(lambda t, o=old, n=new: self._fade_step(o, n, float(t)))
        a.finished.connect(lambda a=a: self._fade_done(a))
        self.fade_anim = a
        a.start()

    def _fade_step(self, old, new, t):
        self.f[new] = math.sin(t * math.pi / 2)
        self.f[old] = math.cos(t * math.pi / 2)
        self._apply()

    def _fade_done(self, a):
        if a is not self.fade_anim:
            return
        self.fade_anim = None
        self.fading = False
        self.pl[self.fade_old].stop()
        self.f = [1.0, 0.0] if self.act == 0 else [0.0, 1.0]
        self._apply()

    def _cancel_fade(self):
        a, self.fade_anim = self.fade_anim, None
        if a is not None:
            a.stop()
        if self.fading:
            self.pl[self.fade_old].stop()
            self.fading = False
        self.f = [1.0, 0.0] if self.act == 0 else [0.0, 1.0]
        self._apply()

    # --- transport (active player) ---
    def play(self):
        self.pl[self.act].play()

    def pause(self):
        self._cancel_fade()
        self.pl[self.act].pause()

    def stop(self):
        self._cancel_fade()
        for p in self.pl:
            p.stop()
        self.pre = None

    def clear(self):
        self.stop()
        for p in self.pl:
            p.setSource(QUrl())

    def position(self):
        return self.pl[self.act].position()

    def duration(self):
        return self.pl[self.act].duration()

    def setPosition(self, p):
        self.pl[self.act].setPosition(int(p))

    def playbackState(self):
        return self.pl[self.act].playbackState()
