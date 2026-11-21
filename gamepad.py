"""Controller support (Xbox / XInput layout) through SDL's GameController API (pygame).

On Linux the kernel `xpad`/`xone` drivers expose Xbox pads and SDL maps every
controller to the standard XInput layout (A/B/X/Y, bumpers, triggers, sticks, D-pad).
Optional: without pygame the app simply has no controller support.
"""
import os
import time

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

BUTTONS = {"BUTTON_A": "a", "BUTTON_B": "b", "BUTTON_X": "x", "BUTTON_Y": "y",
           "BUTTON_BACK": "back", "BUTTON_START": "start", "BUTTON_GUIDE": "guide",
           "BUTTON_LEFTSTICK": "l3", "BUTTON_RIGHTSTICK": "r3",
           "BUTTON_LEFTSHOULDER": "lb", "BUTTON_RIGHTSHOULDER": "rb"}
DPAD = {"BUTTON_DPAD_UP": "up", "BUTTON_DPAD_DOWN": "down",
        "BUTTON_DPAD_LEFT": "left", "BUTTON_DPAD_RIGHT": "right"}


class Gamepad(QObject):
    button = pyqtSignal(str)      # a b x y lb rb back start guide l3 r3
    direction = pyqtSignal(str)   # up down left right (D-pad or left stick, auto-repeats)
    trigger = pyqtSignal(str)     # lt rt (auto-repeats while held)
    scroll = pyqtSignal(float)    # right stick Y, -1..1
    connected = pyqtSignal(str)   # controller name, "" when the last one is unplugged

    FIRST, REPEAT = 0.38, 0.11    # key-repeat timing in seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ok = False
        self.name = ""
        self.pads = {}
        self.held, self.axes, self.next_fire = set(), {}, {}
        self.last_scroll = 0.0
        try:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
            os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
            import pygame
            from pygame._sdl2 import controller
            pygame.display.init()
            pygame.joystick.init()
            controller.init()
        except Exception as ex:
            print("NeonPlayer: controller support disabled:", ex)
            return
        self.pg, self.ct = pygame, controller
        self.btn_map = {getattr(pygame, "CONTROLLER_" + k): v for k, v in BUTTONS.items()
                        if hasattr(pygame, "CONTROLLER_" + k)}
        self.dpad_map = {getattr(pygame, "CONTROLLER_" + k): v for k, v in DPAD.items()
                         if hasattr(pygame, "CONTROLLER_" + k)}
        self.ax = {n: getattr(pygame, "CONTROLLER_AXIS_" + n) for n in
                   ("LEFTX", "LEFTY", "RIGHTY", "TRIGGERLEFT", "TRIGGERRIGHT")}
        self.ok = True
        for i in range(controller.get_count()):
            self._open(i)
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.poll)
        self.timer.start()

    def _open(self, index):
        try:
            if not self.ct.is_controller(index):
                return
            c = self.ct.Controller(index)
            try:
                key = c.as_joystick().get_instance_id()
            except Exception:
                key = index
            self.pads[key] = c
            try:
                self.name = self.ct.name_forindex(index) or "Controller"
            except Exception:
                self.name = "Controller"
            self.connected.emit(self.name)
        except Exception as ex:
            print("NeonPlayer: could not open controller:", ex)

    def _axis(self, name):
        return self.axes.get(self.ax[name], 0) / 32767.0

    def poll(self):
        pg = self.pg
        for ev in pg.event.get():
            t = ev.type
            if t == pg.CONTROLLERDEVICEADDED:
                self._open(ev.device_index)
            elif t == pg.CONTROLLERDEVICEREMOVED:
                self.pads.pop(getattr(ev, "instance_id", None), None)
                if not self.pads:
                    self.name = ""
                    self.held.clear()
                    self.connected.emit("")
            elif t == pg.CONTROLLERBUTTONDOWN:
                # Short, low-intensity haptic acknowledgement for every physical button.
                # SDL exposes rumble on supported XInput/evdev game controllers.
                try:
                    c = next(iter(self.pads.values()))
                    c.rumble(0.28, 0.28, 75)
                except Exception:
                    pass
                if ev.button in self.dpad_map:
                    self.held.add(self.dpad_map[ev.button])
                elif ev.button in self.btn_map:
                    self.button.emit(self.btn_map[ev.button])
            elif t == pg.CONTROLLERBUTTONUP:
                self.held.discard(self.dpad_map.get(ev.button))
            elif t == pg.CONTROLLERAXISMOTION:
                self.axes[ev.axis] = ev.value
        now = time.monotonic()
        active = set(self.held)
        lx, ly = self._axis("LEFTX"), self._axis("LEFTY")
        if lx < -0.55:
            active.add("left")
        if lx > 0.55:
            active.add("right")
        if ly < -0.55:
            active.add("up")
        if ly > 0.55:
            active.add("down")
        trig = set()
        if self._axis("TRIGGERLEFT") > 0.4:
            trig.add("lt")
        if self._axis("TRIGGERRIGHT") > 0.4:
            trig.add("rt")
        for key in list(self.next_fire):
            if key not in active and key not in trig:
                del self.next_fire[key]
        for key in sorted(active | trig):
            due = self.next_fire.get(key)
            if due is None or now >= due:
                self.next_fire[key] = now + (self.FIRST if due is None else self.REPEAT)
                (self.trigger if key in trig else self.direction).emit(key)
        ry = self._axis("RIGHTY")
        if abs(ry) > 0.2 and now - self.last_scroll >= 0.065:
            self.last_scroll = now
            self.scroll.emit(ry)
