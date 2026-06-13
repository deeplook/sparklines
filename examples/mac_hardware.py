"""Mac hardware sensor dashboard — sparklines for Apple Silicon sensors.

Displays live sparklines for whatever sensors respond on the current Mac.
All sensor types are attempted on every model; only those that succeed appear.

    MacBook Pro/Air M2+  →  ACCEL X/Y/Z, LID ANG, ALS, FAN, DISPLAY
    MacBook M1 or older  →  FAN, DISPLAY  (no SPU / accelerometer)
    Mac Mini / Studio    →  FAN, DISPLAY  (no lid, no accelerometer)

Mac model identifiers changed format around 2022 (e.g. "Mac16,10" for a
MacBook Pro M4 Pro), so hardware detection is done by probing each sensor
directly rather than by parsing the model string.

The script auto-elevates to root via sudo (required for IOKit HID access).

Architecture:
    SensorReader runs a daemon thread that opens SPUReportStream instances for
    each SPU sensor (accelerometer, lid angle, ALS) in the same thread so they
    share a CFRunLoop — one poll() call drains events for all three devices.
    Fan speed and display brightness are read synchronously on each tick via
    FanSpeedController and DisplayBrightnessController from lib.hardware.

Sensor display (height adapts to what is available):
    ACCEL X/Y/Z   — bipolar sparklines (2 rows each, ±g); at rest the Z axis
                    shows ~±1 g (gravity) while X and Y stay near 0 g.
                    M2+ MacBook only.
    LID ANG       — positive sparkline, 0–180° hinge angle.  MacBook only.
    Ambient Light — positive sparkline, 0–1 ambient light intensity.  MacBook only.
    FAN L/R       — positive sparklines, RPM relative to the fan's rated maximum.
    Brightness    — positive sparkline, 0–1 display brightness.

Run with:
    uv run --with mac-hardware-toys,textual python examples/mac_hardware.py
"""

import math
import struct
import threading
from collections import deque

from textual.app import App, ComposeResult
from textual.widgets import Header, Static

from sparklines import sparklines


HISTORY = 30

_IMU_LEN = 22  # expected byte length of accelerometer HID report
_IMU_OFF = 6  # byte offset of the first XYZ int32 in that report
_ACCEL_SCALE = 65536.0  # raw int32 → g-force


def _parse_imu(report: bytes, scale: float) -> tuple[float, float, float] | None:
    """Parse an IMU HID report and return (x, y, z) scaled to physical units."""
    if len(report) != _IMU_LEN:
        return None
    x = struct.unpack_from("<i", report, _IMU_OFF)[0] / scale
    y = struct.unpack_from("<i", report, _IMU_OFF + 4)[0] / scale
    z = struct.unpack_from("<i", report, _IMU_OFF + 8)[0] / scale
    return x, y, z


class SensorReader:
    """Probes all known Mac sensors; exposes only those that responded."""

    def __init__(self) -> None:
        """Initialise controllers and start the SPU background thread."""
        self._lock = threading.Lock()

        # SPU sensor state (MacBook M2+)
        self._accel: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._lid: float = 0.0
        self._als: float = 0.0

        # Synchronous controllers (all Macs)
        self._fan_ctrl: object | None = None
        self._bright_ctrl: object | None = None
        self.fan_max: float = 4000.0

        self.available: set[str] = set()
        self.errors: list[str] = []  # diagnostic messages
        self._running = True

        self._init_sync_sensors()

        # SPU thread always starts; exits after logging if no SPU devices found
        self._spu_thread = threading.Thread(target=self._run_spu, daemon=True)
        self._spu_thread.start()

    def _init_sync_sensors(self) -> None:
        """Open fan-speed and display-brightness controllers (all Mac models)."""
        try:
            from lib.hardware import FanSpeedController, DisplayBrightnessController  # type: ignore[import-untyped]

            fc = FanSpeedController()
            if fc.available:
                self._fan_ctrl = fc
                self.available.add("fan")
                limits = fc.limits()
                if limits:
                    self.fan_max = max(limits[0][1], limits[1][1])
            bc = DisplayBrightnessController()
            if bc.available:
                self._bright_ctrl = bc
                self.available.add("brightness")
        except Exception as exc:
            self.errors.append(f"hardware init: {exc}")

    def _run_spu(self) -> None:
        """Open SPU HID streams and poll them until stopped (background thread)."""
        try:
            from lib.sensor_tone import SPUReportStream  # type: ignore[import-untyped]
        except Exception as exc:
            self.errors.append(f"SPUReportStream import: {exc}")
            return

        # All streams share this thread's CFRunLoop; one poll() drains all.
        streams: dict[str, object] = {}
        for name, page, usage in [
            ("accel", 0xFF00, 3),
            ("lid", 0x0020, 0x8A),
            ("als", 0xFF00, 4),
        ]:
            try:
                streams[name] = SPUReportStream(usage_page=page, usage=usage)
                self.available.add(name)
            except Exception as exc:  # noqa: PERF203
                self.errors.append(f"{name}: {exc}")

        if not streams:
            return

        try:
            primary = next(iter(streams.values()))
            while self._running:
                primary.poll(0.05)
                for name, stream in streams.items():
                    for _, report in stream.pop_reports():
                        self._handle_spu(name, bytes(report))
        except Exception as exc:
            self.errors.append(f"SPU poll loop: {exc}")

    def _handle_spu(self, name: str, report: bytes) -> None:
        """Parse one raw HID report and update the corresponding sensor state."""
        if name == "accel":
            xyz = _parse_imu(report, _ACCEL_SCALE)
            if xyz:
                with self._lock:
                    self._accel = xyz
        elif name == "lid":
            if len(report) >= 3 and report[0] == 1:
                angle = float(int(report[1]) | ((int(report[2]) & 0x01) << 8))
                with self._lock:
                    self._lid = angle
        elif name == "als":
            if len(report) >= 44:
                try:
                    raw = struct.unpack_from("<f", report, 40)[0]
                    if math.isfinite(raw):
                        with self._lock:
                            self._als = max(0.0, min(1.0, raw))
                except struct.error:
                    pass

    @property
    def accel(self) -> tuple[float, float, float]:
        """Latest accelerometer reading in g-force: (x, y, z)."""
        with self._lock:
            return self._accel

    @property
    def lid(self) -> float:
        """Latest lid hinge angle in degrees (0 = closed, ~180 = fully open)."""
        with self._lock:
            return self._lid

    @property
    def als(self) -> float:
        """Latest ambient light intensity in the range 0–1."""
        with self._lock:
            return self._als

    def fan_speed(self) -> tuple[float, float] | None:
        """Return (left_rpm, right_rpm), or None if the controller is unavailable."""
        if self._fan_ctrl is None:
            return None
        try:
            return self._fan_ctrl.get()  # type: ignore[union-attr]
        except Exception:
            return None

    def brightness(self) -> float | None:
        """Return display brightness in the range 0–1, or None if unavailable."""
        if self._bright_ctrl is None:
            return None
        try:
            return self._bright_ctrl.get()  # type: ignore[union-attr]
        except Exception:
            return None

    def stop(self) -> None:
        """Signal the SPU polling thread to exit."""
        self._running = False


def _bipolar_rows(data: list[float], bound: float) -> tuple[str, str]:
    """Return (upper_row, lower_row) strings for a bipolar sparkline."""
    rows = sparklines(data, minimum=-bound, maximum=bound)
    while len(rows) < 2:
        rows = [" " * len(data)] + rows
    return rows[0], rows[1]


class HardwareBar(Static, can_focus=False):
    """Bottom-docked bar showing live sensor sparklines."""

    DEFAULT_CSS = """
    HardwareBar {
        dock: bottom;
        height: auto;
        padding: 0 1;
        background: $panel-darken-1;
        color: $text;
    }
    """

    def __init__(self, reader: SensorReader) -> None:
        """Initialise rolling history deques for every sensor channel."""
        super().__init__()
        self._reader = reader
        z = [0.0] * HISTORY
        self._ax: deque[float] = deque(z, maxlen=HISTORY)
        self._ay: deque[float] = deque(z, maxlen=HISTORY)
        self._az: deque[float] = deque(z, maxlen=HISTORY)
        self._lid: deque[float] = deque([0.0] * HISTORY, maxlen=HISTORY)
        self._als: deque[float] = deque(z, maxlen=HISTORY)
        self._fan_l: deque[float] = deque(z, maxlen=HISTORY)
        self._fan_r: deque[float] = deque(z, maxlen=HISTORY)
        self._bright: deque[float] = deque(z, maxlen=HISTORY)

    def on_mount(self) -> None:
        """Start the 1 Hz refresh timer."""
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        """Sample all sensors, append to history, and redraw sparklines."""
        av = self._reader.available
        na = "─" * HISTORY  # placeholder sparkline for unavailable sensors
        lines: list[str] = []

        # Accel X/Y/Z (bipolar, ±g) — MacBook M2+
        if "accel" in av:
            ax, ay, az = self._reader.accel
            self._ax.append(ax)
            self._ay.append(ay)
            self._az.append(az)
        for label, deq in [
            ("ACCEL X", self._ax),
            ("ACCEL Y", self._ay),
            ("ACCEL Z", self._az),
        ]:
            if "accel" in av:
                data = list(deq)
                bound = max((abs(v) for v in data), default=1.0) or 1.0
                top, bot = _bipolar_rows(data, bound)
                val = f"{data[-1]:+.2f} g"
            else:
                top = bot = na
                val = "   N/A "
            lines.append(f"{label:<13}  {top}  {val}")
            lines.append(f"{'':15}{bot}")

        # Lid angle (0–180°) — MacBook only
        if "lid" in av:
            self._lid.append(self._reader.lid)
        if "lid" in av:
            data = list(self._lid)
            spark = sparklines(data, minimum=0, maximum=180)[0]
            val = f"{data[-1]:5.1f}°"
        else:
            spark, val = na, "   N/A "
        lines.append(f"{'LID ANG':<13}  {spark}  {val}")

        # Ambient light (0–1) — MacBook only
        if "als" in av:
            self._als.append(self._reader.als)
        if "als" in av:
            data = list(self._als)
            spark = sparklines(data, minimum=0, maximum=1)[0]
            val = f"  {data[-1]:.3f}"
        else:
            spark, val = na, "   N/A "
        lines.append(f"{'Ambient Light':<13}  {spark}  {val}")

        # Fan speed — all Macs with fans
        if "fan" in av:
            speeds = self._reader.fan_speed()
            if speeds:
                self._fan_l.append(speeds[0])
                self._fan_r.append(speeds[1])
        fan_max = self._reader.fan_max
        for label, deq in [("FAN L", self._fan_l), ("FAN R", self._fan_r)]:
            if "fan" in av:
                data = list(deq)
                spark = sparklines(data, minimum=0, maximum=fan_max)[0]
                val = f"{data[-1]:5.0f} RPM"
            else:
                spark, val = na, "    N/A"
            lines.append(f"{label:<13}  {spark}  {val}")

        # Display brightness (0–1)
        if "brightness" in av:
            b = self._reader.brightness()
            if b is not None:
                self._bright.append(b)
        if "brightness" in av:
            data = list(self._bright)
            spark = sparklines(data, minimum=0, maximum=1)[0]
            val = f"  {data[-1]:.3f}"
        else:
            spark, val = na, "   N/A "
        lines.append(f"{'Brightness':<13}  {spark}  {val}")

        hint = "q: quit"
        w = max(40, (self.size.width or 80) - 2)
        lines[0] = lines[0] + " " * max(0, w - len(lines[0]) - len(hint)) + hint

        self.update("\n".join(lines))


class MacHardwareApp(App):
    """Live Mac hardware sensor dashboard using sparklines."""

    TITLE = "Mac Hardware Sensors"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self) -> None:
        """Create the sensor reader before the TUI starts."""
        super().__init__()
        self._reader = SensorReader()

    def compose(self) -> ComposeResult:
        """Lay out the header and sensor bar."""
        yield Header()
        yield HardwareBar(self._reader)

    def on_unmount(self) -> None:
        """Stop the background polling thread on exit."""
        self._reader.stop()


if __name__ == "__main__":
    from lib.bootstrap import require_root  # type: ignore[import-untyped]

    require_root(__file__)
    MacHardwareApp().run()
