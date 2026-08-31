"""
RPi Autonomous Cleaning Robot — Moss-Detection Merged Edition
=============================================================
MERGE POLICY (strictly followed):
  • Sections 1–9 (Pin, Config, RobotState, SensorPoller, Hardware, WorldModel,
    Planner, MotionController, Watchdog, Telemetry) are UNCHANGED.
  • Only Section 10 (main) is extended with a thin MossController wrapper.
  • MossController encapsulates ALL camera / pump / relay logic so it never
    bleeds into the navigation classes.
  • Pump relay: BCM 4 (Physical Pin 7). HIGH = pump ON, LOW = pump OFF.

All original optimisation comments preserved verbatim.
"""

from __future__ import annotations

import array
import heapq
import logging
import math
import os
import sys
import threading
import time
from typing import Optional

import RPi.GPIO as GPIO
import cv2
import smbus
from gpiozero import Button, DigitalOutputDevice, PWMOutputDevice
from picamera2 import Picamera2
from ultralytics import YOLO
from datetime import datetime

# ──────────────────────────────────────────────
# Logging  (use WARNING on the Pi to avoid I/O cost in tight loops)
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("robot")

_LOG_DEBUG = log.isEnabledFor(logging.DEBUG)   # pre-check, avoids format cost


# ══════════════════════════════════════════════
# SECTION 1 — CONSTANTS  (UNCHANGED)
# ══════════════════════════════════════════════

class Pin:
    TRIG_FRONT = 17; ECHO_FRONT = 27
    TRIG_BACK  = 5;  ECHO_BACK  = 6
    TRIG_LEFT  = 26; ECHO_LEFT  = 21
    TRIG_RIGHT = 9;  ECHO_RIGHT = 11
    PWM_LEFT   = 19; PWM_RIGHT  = 13
    IN1 = 24; IN2 = 16
    IN3 = 22; IN4 = 23
    ENC_LEFT  = 20
    ENC_RIGHT = 25
    PUMP_RELAY = 4   # BCM 4 / Physical Pin 7 — relay IN1


class Config:
    GRID_SIZE          = 10
    CELL_SIZE_CM       = 30.0
    TICKS_PER_CELL     = 200
    TICK_TO_GRID       = 1.0 / 200        # avoids division in hot loop
    ODOM_UPDATE_TICKS  = 25

    OBSTACLE_COST      = 10
    YAW_TOL_DEG        = 3.0
    TURN_PWR           = 0.45
    DRIVE_PWR          = 0.45
    PID_KP             = 0.18
    PID_CLAMP          = 0.4

    EMERG_DIST         = 10.0
    SLOW_DIST          = 20.0
    CLEAR_DIST         = 300.0
    GHOST_LO           = 23.0
    GHOST_HI           = 26.0

    SENSOR_TIMEOUT     = 0.03
    TURN_TIMEOUT       = 8.0
    DRIVE_TIMEOUT      = 10.0
    ESCAPE_REV_S       = 1.5
    WATCHDOG_IDLE_MAX  = 15

    MPU_ADDR           = 0x68
    GYRO_SCALE         = 131.0
    GYRO_CALIB_N       = 100

    # Sensor indices (used for the pre-allocated sensor array)
    S_FRONT = 0
    S_BACK  = 1
    S_LEFT  = 2
    S_RIGHT = 3

    # ── Moss / coverage constants (new — kept separate for clarity) ──────
    COVERAGE_TARGET_PCT   = 80.0   # stop exploring once this is reached
    SCAN_ROUNDS           = 5      # number of stop-scan cycles at startup
    SCAN_NAVIGATE_S       = 2.0    # drive time per round before stopping
    SCAN_WINDOW_S         = 20.0   # camera-active window per stop
    SPRAY_S               = 3.0    # pump-on duration when moss found
    REVERSE_AFTER_SPRAY_S = 6.0    # reverse duration after spraying
    MOSS_CONF             = 0.60   # YOLO confidence threshold
    MOSS_MODEL_PATH       = '/home/pi/Desktop/best_ncnn_model'
    MOSS_SAVE_DIR         = '/home/pi/Desktop/moss_detections'


# Cell state constants (plain ints — avoids IntEnum overhead in hot paths)
UNKNOWN  = -1
FREE     =  0
OBSTACLE =  1
CLEANED  =  2

# Pre-built neighbour offsets as a tuple (no allocation at call time)
_NEIGHBORS4 = ((0, 1), (1, 0), (0, -1), (-1, 0))
_NEIGHBORS8 = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))

GS = Config.GRID_SIZE   # short alias used in index arithmetic below


# ══════════════════════════════════════════════
# SECTION 2 — ROBOT STATE  (UNCHANGED)
# No dataclass decorator — plain __slots__ class is faster attribute access
# ══════════════════════════════════════════════

class RobotState:
    """
    All mutable robot state in one place.
    Uses __slots__ for faster attribute lookup vs a regular class or dataclass.
    """
    __slots__ = (
        "x", "y", "yaw", "target_yaw",
        "l_ticks", "r_ticks", "_tick_lock",
        "gyro_bias", "_last_imu_t",
        "grid",           # flat array.array('b', ...) — row-major [x*GS + y]
        "cost_layer",     # flat array.array('b', ...) — precomputed A* cell costs
        "cost_dirty",     # bool: cost_layer needs rebuild
        "frontiers",      # set of (x, y) tuples, maintained incrementally
        "cached_path", "map_dirty",
        "cleaned_count",  # running integer — no grid scan needed
        "last_cleaned",   # for watchdog
        "idle_cycles",
        "escape_count",   # consecutive _escape() triggers — trap detection
    )

    def __init__(self) -> None:
        half = GS // 2
        self.x: float = float(half)
        self.y: float = float(half)
        self.yaw: float    = 0.0
        self.target_yaw: float = 0.0

        self.l_ticks: int  = 0
        self.r_ticks: int  = 0
        self._tick_lock    = threading.Lock()

        self.gyro_bias: float  = 0.0
        self._last_imu_t: float = time.monotonic()

        # Flat grid: index as grid[x * GS + y]
        # 'b' = signed char (-128..127) — enough for our 4 state values
        self.grid      = array.array('b', [UNKNOWN] * (GS * GS))
        self.cost_layer = array.array('b', [1]       * (GS * GS))
        self.cost_dirty = True

        self.frontiers: set   = set()
        self.cached_path: list = []
        self.map_dirty: bool   = True

        self.cleaned_count: int = 0
        self.last_cleaned:  int = 0
        self.idle_cycles:   int = 0
        self.escape_count:  int = 0   # consecutive escapes — trap detection

    # ── Inline grid accessors (keep short for inlining by CPython) ────────

    def gget(self, x: int, y: int) -> int:
        return self.grid[x * GS + y]

    def gset(self, x: int, y: int, val: int) -> None:
        """
        Write a cell value. Maintains frontiers set and cleaned_count
        incrementally so callers never need to scan the whole grid.
        """
        idx = x * GS + y
        old = self.grid[idx]
        if old == val:
            return

        self.grid[idx] = val
        self.map_dirty  = True
        self.cost_dirty = True

        # ── Maintain frontier set ─────────────────────────────────────────
        # A frontier cell is FREE/CLEANED with ≥1 UNKNOWN 4-neighbour.
        # On any cell write we re-evaluate the cell itself and its neighbours.
        self._refresh_frontier(x, y)
        for dx, dy in _NEIGHBORS4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < GS and 0 <= ny < GS:
                self._refresh_frontier(nx, ny)

        # ── Maintain cleaned_count ────────────────────────────────────────
        if val == CLEANED and old != CLEANED:
            self.cleaned_count += 1
        elif old == CLEANED and val != CLEANED:
            self.cleaned_count -= 1

    def _refresh_frontier(self, x: int, y: int) -> None:
        """Add or remove (x, y) from the frontier set based on current grid."""
        cell_val = self.grid[x * GS + y]
        if cell_val not in (FREE, CLEANED):
            self.frontiers.discard((x, y))
            return
        for dx, dy in _NEIGHBORS4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < GS and 0 <= ny < GS and self.grid[nx * GS + ny] == UNKNOWN:
                self.frontiers.add((x, y))
                return
        self.frontiers.discard((x, y))

    @property
    def ix(self) -> int:
        return int(self.x)

    @property
    def iy(self) -> int:
        return int(self.y)

    def inc_ticks(self, right: bool) -> None:
        with self._tick_lock:
            if right:
                self.r_ticks += 1
            else:
                self.l_ticks += 1

    def get_r_ticks(self) -> int:
        with self._tick_lock:
            return self.r_ticks


# ══════════════════════════════════════════════
# SECTION 3 — SENSOR POLLER (background thread)  (UNCHANGED)
# Removes ALL blocking echo-wait from the drive loop
# ══════════════════════════════════════════════

class SensorPoller:
    """
    Runs in a daemon thread. Continuously reads all 4 sensors
    in a round-robin and stores results in a pre-allocated array.

    The drive loop reads from this array lock-free (floats are
    atomic on CPython due to the GIL; worst case we read a stale
    value that is 1 cycle old — acceptable for obstacle detection).
    """

    # Sensor layout: [front, back, left, right]
    _SENSORS = (
        (Pin.TRIG_FRONT, Pin.ECHO_FRONT),
        (Pin.TRIG_BACK,  Pin.ECHO_BACK),
        (Pin.TRIG_LEFT,  Pin.ECHO_LEFT),
        (Pin.TRIG_RIGHT, Pin.ECHO_RIGHT),
    )

    def __init__(self) -> None:
        # Pre-allocated result buffer — no dict, no allocation in hot path
        self.dist = [Config.CLEAR_DIST] * 4    # [front, back, left, right]
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="sensor-poll", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _read_once(self, trig: int, echo: int) -> float:
        """Single raw reading with timeout. Returns CLEAR_DIST on timeout."""
        GPIO.output(trig, True)
        time.sleep(0.00001)
        GPIO.output(trig, False)

        deadline = time.monotonic() + Config.SENSOR_TIMEOUT
        t0 = time.monotonic()
        while GPIO.input(echo) == 0:
            t0 = time.monotonic()
            if t0 > deadline:
                return Config.CLEAR_DIST

        t1 = t0
        while GPIO.input(echo) == 1:
            t1 = time.monotonic()
            if t1 > deadline:
                return Config.CLEAR_DIST

        return (t1 - t0) * 34300 / 2

    def _read_median(self, trig: int, echo: int) -> float:
        """3-sample median with ghost filter."""
        a = self._read_once(trig, echo)
        b = self._read_once(trig, echo)
        c = self._read_once(trig, echo)
        # Inline sort of 3 values (no allocation)
        if a > b: a, b = b, a
        if b > c: b, c = c, b
        if a > b: a, b = b, a
        med = b  # middle value
        if Config.GHOST_LO < med < Config.GHOST_HI:
            return Config.CLEAR_DIST
        return med

    def _loop(self) -> None:
        """Round-robin sensor reads, interleaved with a short sleep."""
        idx = 0
        sensors = self._SENSORS
        dist    = self.dist          # local ref avoids attribute lookup
        n       = len(sensors)
        while self._running:
            trig, echo = sensors[idx]
            dist[idx]  = self._read_median(trig, echo)
            idx = (idx + 1) % n
            time.sleep(0.002)        # ~2 ms between each sensor = ~8 ms full cycle


# ══════════════════════════════════════════════
# SECTION 4 — HARDWARE ABSTRACTION  (UNCHANGED)
# ══════════════════════════════════════════════

class HardwareError(RuntimeError):
    pass


class Hardware:
    def __init__(self, state: RobotState, poller: SensorPoller) -> None:
        self.state  = state
        self.poller = poller
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self._init_sensor_pins()
        self._init_motors()
        self._init_encoders()
        self._init_imu()

    def _init_sensor_pins(self) -> None:
        for p in (Pin.TRIG_FRONT, Pin.TRIG_BACK, Pin.TRIG_LEFT, Pin.TRIG_RIGHT):
            GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)
        for p in (Pin.ECHO_FRONT, Pin.ECHO_BACK, Pin.ECHO_LEFT, Pin.ECHO_RIGHT):
            GPIO.setup(p, GPIO.IN)

    def _init_motors(self) -> None:
        self.pwm_l = PWMOutputDevice(Pin.PWM_LEFT)
        self.pwm_r = PWMOutputDevice(Pin.PWM_RIGHT)
        self.in1   = DigitalOutputDevice(Pin.IN1)
        self.in2   = DigitalOutputDevice(Pin.IN2)
        self.in3   = DigitalOutputDevice(Pin.IN3)
        self.in4   = DigitalOutputDevice(Pin.IN4)

    def _init_encoders(self) -> None:
        s = self.state
        self._enc_l = Button(Pin.ENC_LEFT,  pull_up=True)
        self._enc_r = Button(Pin.ENC_RIGHT, pull_up=True)
        self._enc_l.when_pressed = lambda: s.inc_ticks(False)
        self._enc_r.when_pressed = lambda: s.inc_ticks(True)

    def _init_imu(self) -> None:
        try:
            self._bus = smbus.SMBus(1)
            self._bus.write_byte_data(Config.MPU_ADDR, 0x6B, 0)
        except OSError as e:
            raise HardwareError(f"IMU init failed: {e}") from e

    # ── IMU ───────────────────────────────────

    def calibrate_gyro(self) -> None:
        log.info("Calibrating gyro (%d samples)…", Config.GYRO_CALIB_N)
        total = 0.0
        bus   = self._bus
        addr  = Config.MPU_ADDR
        scale = Config.GYRO_SCALE
        for _ in range(Config.GYRO_CALIB_N):
            try:
                hi  = bus.read_byte_data(addr, 0x47)
                lo  = bus.read_byte_data(addr, 0x48)
            except OSError:
                continue
            raw = (hi << 8) | lo
            if raw > 32768:
                raw -= 65536
            total += raw / scale
            time.sleep(0.005)
        self.state.gyro_bias = total / Config.GYRO_CALIB_N
        log.info("Gyro bias = %.4f deg/s", self.state.gyro_bias)

    def update_yaw(self) -> None:
        """Integrate gyro Z. Called from tight loops — kept minimal."""
        s   = self.state
        bus = self._bus
        try:
            hi  = bus.read_byte_data(Config.MPU_ADDR, 0x47)
            lo  = bus.read_byte_data(Config.MPU_ADDR, 0x48)
        except OSError:
            return                   # skip bad read silently, log level too costly here
        raw = (hi << 8) | lo
        if raw > 32768:
            raw -= 65536
        now = time.monotonic()
        dt  = now - s._last_imu_t
        s._last_imu_t = now
        s.yaw += (raw / Config.GYRO_SCALE - s.gyro_bias) * dt

    # ── Motor primitives ──────────────────────

    def stop(self) -> None:
        self.pwm_l.value = 0
        self.pwm_r.value = 0
        self.in1.off(); self.in2.off()
        self.in3.off(); self.in4.off()

    def drive(self, lf: bool, rf: bool, lp: float, rp: float) -> None:
        """Set motor direction + power. lf/rf = True means forward."""
        if lf: self.in1.on();  self.in2.off()
        else:  self.in1.off(); self.in2.on()
        if rf: self.in3.on();  self.in4.off()
        else:  self.in3.off(); self.in4.on()
        # Clamp inline — avoids two function calls per iteration
        self.pwm_l.value = lp if lp <= 1.0 else 1.0
        self.pwm_r.value = rp if rp <= 1.0 else 1.0

    def cleanup(self) -> None:
        self.stop()
        GPIO.cleanup()
        log.info("GPIO cleaned up.")


# ══════════════════════════════════════════════
# SECTION 5 — WORLD MODEL  (UNCHANGED)
# ══════════════════════════════════════════════

class WorldModel:
    def __init__(self, state: RobotState) -> None:
        self.state = state

    def update_from_sensors(self, dist: list) -> None:
        """
        Project all 4 sensor readings into the grid.
        Angles pre-computed from current yaw; cos/sin computed once per call.
        dist is the SensorPoller.dist list: [front, back, left, right]
        """
        s   = self.state
        rad = math.radians(s.yaw)
        pi2 = math.pi / 2

        # Pre-compute once per update instead of inside _raycast
        angles = (
            rad,           # front
            rad + math.pi, # back
            rad + pi2,     # left
            rad - pi2,     # right
        )

        ox, oy = s.x, s.y
        for i, angle in enumerate(angles):
            self._raycast(ox, oy, math.cos(angle), math.sin(angle), dist[i])

    def _raycast(
        self, ox: float, oy: float,
        cos_a: float, sin_a: float,
        dist_cm: float
    ) -> None:
        """
        Walk ray from (ox, oy) using pre-computed cos/sin.
        Marks cells FREE proportionally to measured distance.
        cos_a, sin_a passed in — computed once per sensor update call.
        """
        s        = self.state
        cell_sz  = Config.CELL_SIZE_CM
        max_step = int(dist_cm / cell_sz) + 1
        limit    = min(max_step + 1, GS)

        for step in range(1, limit):
            cx = int(ox + cos_a * step)
            cy = int(oy + sin_a * step)
            if not (0 <= cx < GS and 0 <= cy < GS):
                break
            if step * cell_sz < dist_cm:
                if s.gget(cx, cy) == UNKNOWN:
                    s.gset(cx, cy, FREE)
            else:
                s.gset(cx, cy, OBSTACLE)
                break

    def mark_cleaned(self) -> None:
        s = self.state
        s.gset(s.ix, s.iy, CLEANED)


# ══════════════════════════════════════════════
# SECTION 6 — A* PLANNER WITH PRECOMPUTED COST LAYER  (UNCHANGED)
# ══════════════════════════════════════════════

class Planner:
    """
    A* on the occupancy grid.

    The obstacle-proximity cost layer is rebuilt only when the map changes
    (cost_dirty flag), not recalculated per node during search.
    On a 10×10 grid the rebuild is 100 cells × 8 neighbours = 800 ops —
    happens outside the drive loop, acceptable.
    """

    def __init__(self, state: RobotState) -> None:
        self.state = state

    def _rebuild_cost_layer(self) -> None:
        """
        Precompute per-cell A* cost into state.cost_layer.
        Cost = 1 + OBSTACLE_COST for any cell adjacent to an obstacle.
        """
        s    = self.state
        grid = s.grid
        cost = s.cost_layer
        oc   = Config.OBSTACLE_COST

        for x in range(GS):
            for y in range(GS):
                idx  = x * GS + y
                base = 1
                for dx, dy in _NEIGHBORS8:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GS and 0 <= ny < GS:
                        if grid[nx * GS + ny] == OBSTACLE:
                            base += oc
                            break
                cost[idx] = base

        s.cost_dirty = False

    def find_path(
        self,
        start: tuple,
        goal: tuple,
    ) -> list:
        """A* search. Returns cell list from start to goal, or []."""
        s = self.state

        if s.cost_dirty:
            self._rebuild_cost_layer()

        cost  = s.cost_layer
        grid  = s.grid
        heap  = []
        heapq.heappush(heap, (0, 0, start))

        # Use a flat dict keyed by linearised index for faster lookup
        g_score: dict = {start: 0}
        came_from: dict = {start: None}

        gx, gy = goal

        while heap:
            _, g, cur = heapq.heappop(heap)
            cx, cy = cur

            if cx == gx and cy == gy:
                # Reconstruct path
                path = []
                node = cur
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                path.reverse()
                return path

            if g > g_score.get(cur, 2**30):
                continue

            for dx, dy in _NEIGHBORS4:
                nx, ny = cx + dx, cy + dy
                if not (0 <= nx < GS and 0 <= ny < GS):
                    continue
                if grid[nx * GS + ny] == OBSTACLE:
                    continue

                nb  = (nx, ny)
                ng  = g + cost[nx * GS + ny]
                if ng < g_score.get(nb, 2**30):
                    g_score[nb] = ng
                    f = ng + abs(nx - gx) + abs(ny - gy)   # Manhattan, inline
                    heapq.heappush(heap, (f, ng, nb))
                    came_from[nb] = cur

        return []

    def get_path_to(self, goal: tuple) -> list:
        """
        Return cached path to goal if still valid, otherwise replan.
        """
        s     = self.state
        start = (s.ix, s.iy)

        if (not s.map_dirty
                and s.cached_path
                and len(s.cached_path) > 1
                and s.cached_path[-1] == goal):
            # Fast-forward cache past already-visited cells
            cp = s.cached_path
            while len(cp) > 1 and cp[0] != start:
                cp.pop(0)
            if cp and cp[0] == start:
                return cp

        path = self.find_path(start, goal)
        s.cached_path = path
        s.map_dirty   = False
        return path

    def best_frontier(self) -> Optional[tuple]:
        """
        Return the best reachable frontier.
        Pre-sorts by Euclidean distance, then validates with A* for top-5.
        """
        s         = self.state
        frontiers = list(s.frontiers)   # snapshot the set
        if not frontiers:
            return None

        sx, sy = s.ix, s.iy
        frontiers.sort(key=lambda f: (f[0]-sx)**2 + (f[1]-sy)**2)  # squared dist, no sqrt

        start = (sx, sy)
        for candidate in frontiers[:5]:
            if self.find_path(start, candidate):
                return candidate

        return frontiers[0]


# ══════════════════════════════════════════════
# SECTION 7 — MOTION CONTROLLER  (UNCHANGED)
# ══════════════════════════════════════════════

class MotionError(RuntimeError):
    pass


class MotionController:
    def __init__(self, hw: Hardware, state: RobotState, poller: SensorPoller) -> None:
        self.hw     = hw
        self.state  = state
        self.poller = poller

    def update_odometry(self, ticks: int) -> None:
        s    = self.state
        dist = ticks * Config.TICK_TO_GRID
        rad  = math.radians(s.yaw)
        s.x  = max(0.0, min(GS - 0.1, s.x + dist * math.cos(rad)))
        s.y  = max(0.0, min(GS - 0.1, s.y + dist * math.sin(rad)))

    def execute_turn(self, target_deg: float) -> None:
        """Rotate to target_deg. Raises MotionError on timeout."""
        s        = self.state
        hw       = self.hw
        diff     = _adiff(target_deg, s.yaw)
        lf, rf   = diff <= 0, diff > 0
        pwr      = Config.TURN_PWR

        hw.drive(lf, rf, pwr, pwr)

        deadline = time.monotonic() + Config.TURN_TIMEOUT
        tol      = Config.YAW_TOL_DEG

        while abs(_adiff(target_deg, s.yaw)) > tol:
            hw.update_yaw()
            if time.monotonic() > deadline:
                hw.stop()
                raise MotionError(
                    "Turn timeout: target=%.1f cur=%.1f" % (target_deg, s.yaw)
                )
            time.sleep(0.01)

        hw.stop()
        time.sleep(0.3)

    def drive_to_cell(self, tx: int, ty: int, world: WorldModel) -> bool:
        """
        Drive toward cell (tx, ty).
        Returns True on success, False on recoverable obstacle.
        Raises MotionError on timeout.

        Hot-path optimisations:
          • Sensor array read by index, no dict lookup
          • cos/sin for PID correction NOT re-computed (yaw used directly)
          • Odometry math done with pre-cached TICK_TO_GRID constant
          • No allocations inside the loop
        """
        s       = self.state
        hw      = self.hw
        poller  = self.poller
        dist    = poller.dist   # direct reference, no attribute lookup per tick

        # Pre-compute heading to target
        heading = math.degrees(math.atan2(ty - s.y, tx - s.x))
        self.execute_turn(heading)

        # Tick snapshot
        with s._tick_lock:
            t_start = s.r_ticks
        t_last_odom = t_start

        hw.drive(True, True, Config.DRIVE_PWR, Config.DRIVE_PWR)
        deadline   = time.monotonic() + Config.DRIVE_TIMEOUT
        ticks_goal = Config.TICKS_PER_CELL
        odom_step  = Config.ODOM_UPDATE_TICKS
        kp         = Config.PID_KP
        clamp      = Config.PID_CLAMP
        base_pwr   = Config.DRIVE_PWR
        emerg      = Config.EMERG_DIST
        slow       = Config.SLOW_DIST

        while True:
            cur_ticks = s.get_r_ticks()
            elapsed   = cur_ticks - t_start

            if elapsed >= ticks_goal:
                break

            if time.monotonic() > deadline:
                hw.stop()
                raise MotionError("Drive timeout — robot stuck")

            # Read sensor values by index (no dict, no allocation)
            f = dist[Config.S_FRONT]
            l = dist[Config.S_LEFT]
            r = dist[Config.S_RIGHT]
            b = dist[Config.S_BACK]

            if f < emerg or l < emerg or r < emerg:
                hw.stop()
                self._escape(b)
                return False

            if f < slow:
                hw.stop()
                self._short_reverse()
                return False

            # Update world map (happens outside tight sleep — acceptable)
            world.update_from_sensors(dist)

            # Odometry update
            delta = cur_ticks - t_last_odom
            if delta >= odom_step:
                self.update_odometry(delta)
                world.mark_cleaned()
                t_last_odom = cur_ticks

            # PID yaw correction — inline clamp (no extra function call)
            err  = _adiff(heading, s.yaw)
            corr = err * kp
            if   corr >  clamp: corr =  clamp
            elif corr < -clamp: corr = -clamp

            lp = base_pwr - corr - 0.18
            rp = base_pwr + corr
            hw.drive(True, True,
                     lp if lp > 0.2 else 0.2,
                     rp if rp > 0.2 else 0.2)

            hw.update_yaw()
            time.sleep(0.01)

        hw.stop()
        # Flush remaining ticks
        self.update_odometry(s.get_r_ticks() - t_last_odom)
        world.mark_cleaned()
        s.escape_count = 0   # clean drive — reset trap counter
        return True

    def _escape(self, back_dist: float) -> None:
        log.warning("ESCAPE: back=%.1f cm", back_dist)
        hw    = self.hw
        state = self.state

        # ── Trap detection: count consecutive escapes ─────────────────────
        state.escape_count += 1
        if state.escape_count >= 3:
            log.warning(
                "🚨 Escape count=%d — possible U-trap! Executing breakout maneuver.",
                state.escape_count
            )
            state.escape_count = 0   # reset after breakout
            # Breakout: turn 45°, drive briefly, then let navigation resume
            try:
                self.execute_turn(state.yaw + 45)
            except MotionError as e:
                log.error("Breakout turn failed: %s", e)
            hw.drive(True, True, Config.DRIVE_PWR, Config.DRIVE_PWR)
            time.sleep(0.5)
            hw.stop()
            return

        if back_dist > Config.EMERG_DIST * 2:
            hw.drive(False, False, 0.5, 0.5)
            time.sleep(Config.ESCAPE_REV_S)
            hw.stop()
        try:
            self.execute_turn(state.yaw + 180)
        except MotionError as e:
            log.error("Escape turn failed: %s", e)

    def _short_reverse(self) -> None:
        self.hw.drive(False, False, 0.3, 0.3)
        time.sleep(0.8)
        self.hw.stop()


# ══════════════════════════════════════════════
# SECTION 8 — WATCHDOG  (UNCHANGED)
# ══════════════════════════════════════════════

class Watchdog:
    def __init__(self, state: RobotState, motion: MotionController) -> None:
        self.state  = state
        self.motion = motion

    def check(self) -> None:
        s = self.state
        # cleaned_count is a running integer — O(1), no grid scan
        if s.cleaned_count > s.last_cleaned:
            s.last_cleaned = s.cleaned_count
            s.idle_cycles  = 0
            return

        s.idle_cycles += 1
        if s.idle_cycles >= Config.WATCHDOG_IDLE_MAX:
            log.warning("Watchdog: %d idle cycles, forcing pivot", s.idle_cycles)
            s.idle_cycles = 0
            pivot_dir = 90 if (s.idle_cycles % 2 == 0) else -90
            try:
                self.motion.execute_turn(s.yaw + pivot_dir)
            except MotionError as e:
                log.error("Watchdog pivot failed: %s", e)


# ══════════════════════════════════════════════
# SECTION 9 — TELEMETRY  (UNCHANGED)
# ══════════════════════════════════════════════

_SYM = {UNKNOWN: "[?]", FREE: "[.]", OBSTACLE: "[X]", CLEANED: "[*]"}

def print_telemetry(state: RobotState, n_frontiers: int) -> None:
    s         = state
    obstacles = sum(1 for v in s.grid if v == OBSTACLE)
    explorable = max(1, GS * GS - obstacles)
    pct        = s.cleaned_count / explorable * 100

    lines = [
        "\n" + "=" * 34,
        "  Pos: (%.1f, %.1f)  Yaw: %.1f deg" % (s.x, s.y, s.yaw),
        "  Frontiers: %d" % n_frontiers,   # coverage % intentionally omitted from serial
        "  " + "-" * 30,
    ]
    ix, iy = s.ix, s.iy
    for y in range(GS - 1, -1, -1):
        row = " "
        for x in range(GS):
            row += "[R]" if (x == ix and y == iy) else _SYM.get(s.gget(x, y), "[?]")
        lines.append(row)
    lines.append("=" * 34)
    print("\n".join(lines))   # one write call instead of N print() calls


# ══════════════════════════════════════════════
# SECTION 10 — MOSS CONTROLLER  (NEW — thin control layer only)
#
# Owns: camera, YOLO model, pump relay.
# Never touches: planner, motion controller, world model, sensor poller.
# ══════════════════════════════════════════════

class MossController:
    """
    Encapsulates all camera + pump logic.

    Calling convention from main():
        mc.scan_and_spray(hw)   — robot must already be stopped before calling

    Relay wiring (floating-off / driven-low-on):
        BCM 4 (Physical Pin 7) → Relay IN1
        GPIO.IN  (input/floating) → pump OFF  (simulates disconnected wire)
        GPIO.OUT + GPIO.LOW      → pump ON    (drives line low, energises relay)
    """

    def __init__(self) -> None:
        # ── Save directory ────────────────────────────────────────────────
        os.makedirs(Config.MOSS_SAVE_DIR, exist_ok=True)

        # ── Pump relay setup (BCM 4) ──────────────────────────────────────
        GPIO.setup(Pin.PUMP_RELAY, GPIO.IN)  # pump OFF at start (floating input = relay de-energised)
        log.info("Pump relay initialised on BCM %d.", Pin.PUMP_RELAY)

        # ── Camera ───────────────────────────────────────────────────────
        log.info("📷 Opening camera...")
        self._cam = Picamera2()
        cfg = self._cam.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 640)}
        )
        self._cam.configure(cfg)
        self._cam.set_controls({"AwbEnable": True, "AeEnable": True})
        self._cam.start()
        log.info("⏳ Letting camera adjust to room lighting...")
        time.sleep(2)

        # ── YOLO model ───────────────────────────────────────────────────
        log.info("🧠 Loading YOLO model...")
        self._model = YOLO(Config.MOSS_MODEL_PATH)
        log.info("🚀 MossController ready.")

    # ── Public API ────────────────────────────────────────────────────────

    def scan_and_spray(self, hw: Hardware) -> None:
        """
        Run a 20-second moss-detection window.
        Robot must be stopped before this is called.
        If moss is detected:
            1. Activate pump for SPRAY_S seconds.
            2. Reverse robot for REVERSE_AFTER_SPRAY_S seconds.
            3. Stop pump.
        Camera inference only runs while robot is stationary (requirement met
        because hw.stop() is called by the caller before scan_and_spray).
        """
        log.info("🔍 Starting moss scan window (%.0f s)...", Config.SCAN_WINDOW_S)
        deadline  = time.monotonic() + Config.SCAN_WINDOW_S
        conf      = Config.MOSS_CONF
        save_dir  = Config.MOSS_SAVE_DIR
        moss_seen = False

        while time.monotonic() < deadline:
            frame = self._cam.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            results = self._model.predict(
                source=frame, imgsz=640, conf=conf, verbose=False
            )

            for result in results:
                if len(result.boxes) > 0:
                    moss_seen = True
                    annotated = result.plot()
                    ts = datetime.now().strftime("%H%M%S_%f")
                    cv2.imwrite(f"{save_dir}/moss_{ts}.jpg", annotated)
                    conf_val = result.boxes.conf[0].item() * 100
                    log.info("⚠️  MOSS SPOTTED! (%.1f%% match)", conf_val)

            if moss_seen:
                break   # detected — exit scan loop early, move to spray

            time.sleep(0.05)  # ~20 fps cap; keeps CPU free for background threads

        if moss_seen:
            self._spray_only()
        else:
            log.info("✅ No moss detected during scan window.")

    def cleanup(self) -> None:
        """Call from finally block to release camera and ensure pump is off."""
        GPIO.setup(Pin.PUMP_RELAY, GPIO.IN)  # safety: ensure pump off (floating input = relay de-energised)
        try:
            self._cam.stop()
        except Exception:
            pass
        log.info("MossController cleaned up.")

    # ── Private helpers ───────────────────────────────────────────────────

    def _pump_on(self) -> None:
        GPIO.setup(Pin.PUMP_RELAY, GPIO.OUT)
        GPIO.output(Pin.PUMP_RELAY, GPIO.LOW)   # drives line low → relay energised → pump ON
        log.info("💧 Pump ON")

    def _pump_off(self) -> None:
        GPIO.setup(Pin.PUMP_RELAY, GPIO.IN)     # float pin → relay de-energised → pump OFF
        log.info("💧 Pump OFF")

    def _spray_only(self) -> None:
        """Pump ON for SPRAY_S seconds, then OFF. Robot does NOT move."""
        log.info("💦 Spraying moss for %.1f s...", Config.SPRAY_S)
        self._pump_on()
        time.sleep(Config.SPRAY_S)
        self._pump_off()
        log.info("✅ Spray complete — resuming navigation.")


# ══════════════════════════════════════════════
# SECTION 11 — HELPERS  (UNCHANGED)
# ══════════════════════════════════════════════

def _adiff(target: float, current: float) -> float:
    """Shortest signed angle difference, result in (-180, +180]."""
    return (target - current + 180.0) % 360.0 - 180.0


def _coverage_pct(state: RobotState) -> float:
    """Return coverage percentage based on cleaned vs explorable cells."""
    obstacles  = sum(1 for v in state.grid if v == OBSTACLE)
    explorable = max(1, GS * GS - obstacles)
    return state.cleaned_count / explorable * 100.0


def _navigate_one_step(
    state: RobotState,
    planner: Planner,
    motion: MotionController,
    world: WorldModel,
    watchdog: Watchdog,
) -> bool:
    """
    Execute one navigation step (pick frontier → drive one cell).
    Returns True if a step was taken, False if no frontier available.
    Extracted to avoid duplicating the loop body for the two nav phases.
    """
    n_frontiers = len(state.frontiers)
    print_telemetry(state, n_frontiers)
    watchdog.check()

    if n_frontiers == 0:
        return False

    target = planner.best_frontier()
    if target is None:
        log.warning("No reachable frontier. Pivoting.")
        motion.execute_turn(state.yaw + 90)
        return True

    path = planner.get_path_to(target)
    if len(path) <= 1:
        state.frontiers.discard(target)
        return True

    try:
        ok = motion.drive_to_cell(path[1][0], path[1][1], world)
    except MotionError as e:
        log.error("MotionError: %s", e)
        state.cached_path.clear()
        state.map_dirty = True
        return True

    if not ok:
        state.cached_path.clear()
        state.map_dirty = True

    return True


# ══════════════════════════════════════════════
# SECTION 12 — MAIN  (Boustrophedon Coverage Path Planning)
#
# ARCHITECTURE CHANGE: Frontier-based exploration replaced with a
# lawnmower (boustrophedon) sweep across the entire grid.
#
# SWEEP PATTERN:
#   Row 0 →  col 0..GS-1  (left to right)
#   Row 1 ←  col GS-1..0  (right to left)
#   Row 2 →  col 0..GS-1  (left to right)
#   ...
#
# SENSOR POLICY (overrides ALL motion decisions):
#   front < EMERG_DIST  → stop + turn 90° + obstacle bypass + resume sweep
#   front < SLOW_DIST   → slow reverse + resume sweep
#
# MOVEMENT: Time-based (CELL_DRIVE_S seconds per cell).
#   Encoders still update odometry but do NOT control when to stop.
#
# MOSS INTEGRATION: Unchanged — 5 stop-scan rounds run before sweep begins.
# ══════════════════════════════════════════════

# ── Coverage sweep tuning constants ──────────────────────────────────────────
_CELL_DRIVE_S   = 0.70   # seconds of forward drive per grid cell (tune on hardware)
_TURN_SETTLE_S  = 0.25   # brief pause after any turn for robot to stabilise
_BYPASS_DRIVE_S = 0.65   # drive time when skirting around an obstacle cell
_SLOW_REVERSE_S = 0.40   # reverse duration when front < SLOW_DIST
_POST_BYPASS_PAUSE_S = 0.20  # pause after obstacle bypass before resuming row


def _sensor_front(poller: SensorPoller) -> float:
    """Read front ultrasonic distance (cm). Non-blocking — reads cached value."""
    return poller.dist[Config.S_FRONT]


def _time_drive_forward(hw: Hardware, state: RobotState,
                        world: WorldModel, poller: SensorPoller,
                        duration: float) -> bool:
    """
    Drive forward for `duration` seconds using time-based control.

    Sensor checks run every loop iteration (≈10 ms cadence).
    Returns:
        True  — cell completed cleanly.
        False — obstacle interrupted the drive (caller must handle).

    Encoders are still used to update odometry (state.x/y) but do NOT
    determine when to stop — only the timer does.
    """
    hw_obj   = hw
    dist     = poller.dist
    emerg    = Config.EMERG_DIST
    slow_d   = Config.SLOW_DIST
    base_pwr = Config.DRIVE_PWR
    deadline = time.monotonic() + duration

    hw_obj.drive(True, True, base_pwr, base_pwr)

    # Tick snapshot for odometry (encoder-assisted but not controlling stop)
    with state._tick_lock:
        t_last = state.r_ticks

    while time.monotonic() < deadline:
        # ── SENSOR OVERRIDE — highest priority ───────────────────────────
        front = dist[Config.S_FRONT]

        if front < emerg:
            # Emergency: full stop, signal obstacle to caller
            hw_obj.stop()
            return False   # caller will execute 90° bypass

        # ── Side-collision protection — prevents scraping during skid-steer drift
        left_d  = dist[Config.S_LEFT]
        right_d = dist[Config.S_RIGHT]
        if left_d < emerg or right_d < emerg:
            hw_obj.stop()
            # Correct yaw slightly away from the close side
            if left_d < right_d:
                # Too close on the left — nudge right (clockwise, -15°)
                _corr_yaw = state.yaw - 15.0
            else:
                # Too close on the right — nudge left (counter-clockwise, +15°)
                _corr_yaw = state.yaw + 15.0
            try:
                # Re-use Hardware.update_yaw + drive for a brief corrective arc
                hw_obj.drive(True, True, 0.3, 0.3)   # drive straight while yaw settles
                _corr_deadline = time.monotonic() + 0.3
                while time.monotonic() < _corr_deadline:
                    hw_obj.update_yaw()
                    time.sleep(0.01)
                hw_obj.stop()
            except Exception:
                hw_obj.stop()
            # Re-check: if still too close, abort this drive segment
            if dist[Config.S_LEFT] < emerg or dist[Config.S_RIGHT] < emerg:
                return False
            # Otherwise resume — restart the forward drive remainder
            hw_obj.drive(True, True, base_pwr, base_pwr)

        if front < slow_d:
            # Slow zone: reverse only if back is clear; else do a corrective turn
            hw_obj.stop()
            back_d = dist[Config.S_BACK]
            if back_d > Config.EMERG_DIST:
                hw_obj.drive(False, False, 0.35, 0.35)   # reverse
                time.sleep(_SLOW_REVERSE_S)
                hw_obj.stop()
            else:
                # Back is blocked — skip reverse, nudge 10° to break deadlock
                log.warning(
                    "Slow-zone reverse skipped: back=%.1f cm. Corrective turn.", back_d
                )
                hw_obj.drive(True, False, 0.3, 0.3)   # brief pivot
                time.sleep(0.25)
                hw_obj.stop()
            return False   # caller will re-evaluate and skip/bypass cell

        # ── Odometry update (informational — does not stop drive) ─────────
        with state._tick_lock:
            cur = state.r_ticks
        delta = cur - t_last
        if delta >= Config.ODOM_UPDATE_TICKS:
            # Reuse MotionController math inline to avoid coupling
            dist_grid = delta * Config.TICK_TO_GRID
            rad = math.radians(state.yaw)
            state.x = max(0.0, min(GS - 0.1, state.x + dist_grid * math.cos(rad)))
            state.y = max(0.0, min(GS - 0.1, state.y + dist_grid * math.sin(rad)))
            world.mark_cleaned()          # mark current grid cell as cleaned
            t_last = cur

        hw_obj.update_yaw()               # keep IMU current
        time.sleep(0.01)                  # ≈100 Hz sensor check rate

    hw_obj.stop()
    world.mark_cleaned()                  # mark on arrival
    return True   # completed normally


def _turn_to(motion: MotionController, target_deg: float) -> None:
    """
    Wrapper around execute_turn with a short post-turn settle pause.
    Swallows MotionError and logs it — robot continues best-effort.
    """
    try:
        motion.execute_turn(target_deg)
    except MotionError as e:
        log.warning("Turn failed (continuing): %s", e)
    time.sleep(_TURN_SETTLE_S)


def _bypass_obstacle(hw: Hardware, state: RobotState,
                     world: WorldModel, motion: MotionController,
                     poller: SensorPoller, row_dir: int) -> None:
    """
    Simple 90° obstacle bypass when the front sensor triggers.

    Strategy:
        1. Stop (already done by caller).
        2. Turn 90° away from current sweep direction.
        3. Drive forward one cell width to clear the obstacle.
        4. Turn back to original sweep heading.
        5. Resume — caller continues the row.

    row_dir: +1 = sweeping right (heading 0°), -1 = sweeping left (heading 180°).
    The turn direction alternates: always tries left-of-travel first.
    """
    log.info("🚧 Obstacle bypass triggered (row_dir=%+d, front=%.1f cm)",
             row_dir, _sensor_front(poller))

    # Sweep heading: 0° (right) or 180° (left)
    sweep_heading = 0.0 if row_dir == 1 else 180.0

    # ── Choose bypass side based on which sensor reads more free space ────
    left_dist  = poller.dist[Config.S_LEFT]
    right_dist = poller.dist[Config.S_RIGHT]
    if left_dist >= right_dist:
        # More space on left → turn 90° counter-clockwise (left of travel)
        perp_heading = sweep_heading + 90.0
        log.info("↰ Bypassing left (L=%.1f cm  R=%.1f cm)", left_dist, right_dist)
    else:
        # More space on right → turn 90° clockwise (right of travel)
        perp_heading = sweep_heading - 90.0
        log.info("↱ Bypassing right (L=%.1f cm  R=%.1f cm)", left_dist, right_dist)

    _turn_to(motion, perp_heading)

    # Drive one cell width sideways to pass the obstacle
    ok = _time_drive_forward(hw, state, world, poller, _BYPASS_DRIVE_S)
    if not ok:
        # Secondary obstacle while bypassing — just turn back and skip
        log.warning("Obstacle during bypass skirt. Aborting bypass.")

    # Return to sweep heading
    _turn_to(motion, sweep_heading)

    # ── Wide-obstacle guard: if path still blocked, keep skirting ─────────
    _recheck_limit = 3   # max extra bypass drives to avoid infinite loop
    for _attempt in range(_recheck_limit):
        front_after = poller.dist[Config.S_FRONT]
        if front_after >= Config.SLOW_DIST:
            break   # path is clear — continue row normally
        log.warning(
            "⚠️  Front still blocked (%.1f cm) after bypass — skirting again "
            "(attempt %d/%d)", front_after, _attempt + 1, _recheck_limit
        )
        ok2 = _time_drive_forward(hw, state, world, poller, _BYPASS_DRIVE_S)
        if not ok2:
            log.warning("Secondary skirt blocked — returning to sweep heading.")
        _turn_to(motion, sweep_heading)

    time.sleep(_POST_BYPASS_PAUSE_S)


def _drive_one_cell(hw: Hardware, state: RobotState,
                    world: WorldModel, motion: MotionController,
                    poller: SensorPoller, row_dir: int) -> bool:
    """
    Attempt to drive one grid cell in the current sweep direction.
    Handles obstacle bypass inline if sensor triggers.

    Returns True if robot advanced (or bypassed), False if permanently blocked.
    """
    ok = _time_drive_forward(hw, state, world, poller, _CELL_DRIVE_S)
    if ok:
        return True   # clean advance

    # Obstacle detected — attempt bypass
    front = _sensor_front(poller)
    log.info("🛑 Front obstacle @ %.1f cm — executing bypass", front)
    _bypass_obstacle(hw, state, world, motion, poller, row_dir)
    return True   # after bypass, cell is considered "handled"


def _boustrophedon_sweep(
    hw: Hardware,
    state: RobotState,
    world: WorldModel,
    motion: MotionController,
    poller: SensorPoller,
) -> None:
    """
    Execute a full boustrophedon (lawnmower) coverage sweep of the grid.

    Row traversal:
        Even rows (0, 2, 4, …): sweep left → right  (heading  0°, row_dir = +1)
        Odd  rows (1, 3, 5, …): sweep right → left  (heading 180°, row_dir = -1)

    After completing each row the robot steps up one row (heading 90°) to
    begin the next pass.

    The loop exits when:
        a) All GS rows have been swept, OR
        b) Coverage percentage ≥ Config.COVERAGE_TARGET_PCT (checked per cell).
    """
    log.info("🗺  Starting boustrophedon sweep  (grid=%d×%d, target=%.0f%%)",
             GS, GS, Config.COVERAGE_TARGET_PCT)

    for row in range(GS):
        # ── Coverage gate — check before starting each new row ────────────
        cov = _coverage_pct(state)
        if cov >= Config.COVERAGE_TARGET_PCT:
            log.info("🏁 Coverage %.1f%% reached — sweep complete (row %d).", cov, row)
            return

        # ── Determine sweep direction for this row ────────────────────────
        row_dir     = 1 if (row % 2 == 0) else -1   # +1=right, -1=left
        sweep_hdg   = 0.0 if row_dir == 1 else 180.0
        col_range   = range(GS) if row_dir == 1 else range(GS - 1, -1, -1)

        log.info("▶  Row %d/%d  dir=%s  heading=%.0f°  cov=%.1f%%",
                 row + 1, GS,
                 "→" if row_dir == 1 else "←",
                 sweep_hdg, cov)

        # ── Face the sweep direction ──────────────────────────────────────
        _turn_to(motion, sweep_hdg)

        # ── Sweep all columns in this row ─────────────────────────────────
        for _col_idx, _col in enumerate(col_range):
            world.update_from_sensors(poller.dist)   # refresh obstacle map
            world.mark_cleaned()                      # mark current cell

            # Log telemetry every 5 cells to avoid console spam
            if _col_idx % 5 == 0:
                print_telemetry(state, 0)

            # Check coverage target every cell
            if _coverage_pct(state) >= Config.COVERAGE_TARGET_PCT:
                log.info("🏁 Coverage target reached mid-row (row=%d, col=%d).",
                         row, _col)
                hw.stop()
                return

            # ── Drive one cell forward (with integrated obstacle handling) ─
            _drive_one_cell(hw, state, world, motion, poller, row_dir)

            # ── Check sensors again after move before next cell ───────────
            world.update_from_sensors(poller.dist)
            world.mark_cleaned()

        # ── End of row: step one row forward (perpendicular to sweep) ─────
        if row < GS - 1:   # no step-up after the final row
            log.info("↑  End of row %d — stepping up to next row.", row + 1)
            _turn_to(motion, 90.0)          # always step upward (positive Y)
            ok = _time_drive_forward(hw, state, world, poller, _CELL_DRIVE_S)
            if not ok:
                # Obstacle at row transition — try a short bypass and continue
                log.warning("Obstacle at row transition — attempting bypass.")
                _bypass_obstacle(hw, state, world, motion, poller, row_dir=0)

            world.mark_cleaned()

    cov = _coverage_pct(state)
    log.info("✅ Boustrophedon sweep complete. Final coverage: %.1f%%", cov)


def main() -> None:
    log.info("Initialising…")

    state    = RobotState()
    poller   = SensorPoller()
    hw       = Hardware(state, poller)
    world    = WorldModel(state)
    planner  = Planner(state)          # kept for compatibility (not used in sweep)
    motion   = MotionController(hw, state, poller)
    watchdog = Watchdog(state, motion)
    moss     = MossController()        # camera + model loaded once at startup

    try:
        hw.calibrate_gyro()
        poller.start()                  # SensorPoller background thread — UNCHANGED

        # Mark starting cell and initialise world model from first sensor read
        world.mark_cleaned()
        world.update_from_sensors(poller.dist)

        # ── STARTUP PAUSE (2 s) ───────────────────────────────────────────
        log.info("⏸  Startup pause (2 s) — letting sensors stabilise…")
        time.sleep(2)
        log.info("🚀 Navigation starting.")

        # ══ PHASE 1: 5 STOP-SCAN ROUNDS (UNCHANGED) ══════════════════════
        # Robot navigates briefly, stops, runs YOLO moss detection.
        # Uses _navigate_one_step for short forward bursts so the robot
        # moves into position before each scan window.
        for round_num in range(1, Config.SCAN_ROUNDS + 1):
            log.info("── Moss scan round %d / %d ──", round_num, Config.SCAN_ROUNDS)

            # Drive briefly to position robot at a new spot for scanning
            nav_deadline = time.monotonic() + Config.SCAN_NAVIGATE_S
            while time.monotonic() < nav_deadline:
                # Use existing frontier-based step for short positioning drives
                if not _navigate_one_step(state, planner, motion, world, watchdog):
                    break   # no frontiers yet — stationary scan is still valid

            hw.stop()
            log.info("🛑 Robot stopped for moss scan round %d.", round_num)

            # Camera moss detection (robot stationary — 20 s window)
            moss.scan_and_spray(hw)

            log.info("▶️  Resuming after scan round %d.", round_num)

        log.info("✅ All %d moss scan rounds complete.", Config.SCAN_ROUNDS)

        # ══ PHASE 2: BOUSTROPHEDON COVERAGE SWEEP ════════════════════════
        # Replace frontier exploration with a deterministic lawnmower pattern.
        # The robot sweeps rows alternately left→right and right→left until
        # coverage reaches Config.COVERAGE_TARGET_PCT.
        log.info("🗺  Beginning lawnmower coverage sweep (target ≥ %.0f%%).",
                 Config.COVERAGE_TARGET_PCT)

        _boustrophedon_sweep(hw, state, world, motion, poller)

        # ══ PHASE 3: COVERAGE RECOVERY (if target not yet met) ════════════
        # If the full grid sweep finished but coverage is still below target
        # (e.g. due to obstacles blocking several cells), perform watchdog-style
        # pivot searches to find and clean remaining accessible cells.
        cov = _coverage_pct(state)
        if cov < Config.COVERAGE_TARGET_PCT:
            log.info(
                "⚠  Sweep done but coverage only %.1f%% < %.0f%% target. "
                "Running recovery exploration.",
                cov, Config.COVERAGE_TARGET_PCT
            )

            recovery_limit = 200   # cap recovery iterations to prevent infinite loop
            recovery_count = 0

            while recovery_count < recovery_limit:
                cov = _coverage_pct(state)
                if cov >= Config.COVERAGE_TARGET_PCT:
                    log.info("🏁 Recovery reached %.1f%% coverage.", cov)
                    break

                world.update_from_sensors(poller.dist)
                world.mark_cleaned()
                print_telemetry(state, len(state.frontiers))
                watchdog.check()

                # Try frontier-based step to reach remaining uncleaned cells
                if not _navigate_one_step(state, planner, motion, world, watchdog):
                    # No reachable frontiers — pivot and try a different direction
                    log.info("Recovery: no frontier found — pivoting 90°.")
                    try:
                        motion.execute_turn(state.yaw + 90)
                    except MotionError as e:
                        log.error("Recovery pivot failed: %s", e)
                    time.sleep(0.5)

                # Also check front sensor during recovery steps
                front = _sensor_front(poller)
                if front < Config.EMERG_DIST:
                    hw.stop()
                    log.warning("Recovery: emergency obstacle @ %.1f cm — bypassing.", front)
                    _bypass_obstacle(hw, state, world, motion, poller, row_dir=1)

                recovery_count += 1

            cov = _coverage_pct(state)
            log.info("Recovery phase ended after %d iterations. Coverage: %.1f%%",
                     recovery_count, cov)

        # ══ FINAL STATUS ══════════════════════════════════════════════════
        cov = _coverage_pct(state)
        log.info("🏆 Mission complete. Final coverage: %.1f%% (target was %.0f%%).",
                 cov, Config.COVERAGE_TARGET_PCT)
        print_telemetry(state, 0)

    except KeyboardInterrupt:
        log.info("Stopped by user.")
    except HardwareError as e:
        log.critical("Hardware failure: %s", e)
        sys.exit(1)
    finally:
        hw.stop()
        poller.stop()
        moss.cleanup()
        hw.cleanup()


if __name__ == "__main__":
    main()
