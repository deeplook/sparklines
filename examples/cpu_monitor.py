"""Live CPU and memory monitor — bottom-bar sparklines with textual + sparklines.

Two sliding 20-second sparklines are shown at the bottom of the screen:

  CPU  — percentage utilisation (0–100 %), always positive, single row.

  MEM  — memory pressure in MB/s: the rate of change of resident memory use.
         Positive values mean the system is allocating (memory pressure rising);
         negative values mean memory is being freed (pressure falling).
         Because the signal is bipolar the sparkline auto-splits into an upper
         row (allocating) and a lower inverted row (freeing), using the mixed
         positive/negative rendering built into the sparklines package.

Run with:
    uv run --with psutil,textual python examples/cpu_monitor.py
"""

from collections import deque

import psutil
from textual.app import App, ComposeResult
from textual.widgets import Static

from sparklines import sparklines


HISTORY = 20


class MonitorBar(Static, can_focus=False):
    """Bottom-docked bar showing CPU and memory-delta sparklines."""

    DEFAULT_CSS = """
    MonitorBar {
        dock: bottom;
        height: 3;
        padding: 0 1;
        background: $panel-darken-1;
        color: $text;
    }
    """

    def __init__(self) -> None:  # noqa: D107
        super().__init__()
        self._cpu: deque[float] = deque([0.0] * HISTORY, maxlen=HISTORY)
        self._mem: deque[float] = deque([0.0] * HISTORY, maxlen=HISTORY)
        self._prev_mem: float = psutil.virtual_memory().used / 1024**2

    def on_mount(self) -> None:  # noqa: D102
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        self._cpu.append(psutil.cpu_percent(interval=None))

        curr_mb = psutil.virtual_memory().used / 1024**2
        self._mem.append(curr_mb - self._prev_mem)
        self._prev_mem = curr_mb

        cpu_spark = sparklines(list(self._cpu), minimum=0, maximum=100)[0]

        mem_list = list(self._mem)
        bound = max((abs(v) for v in mem_list), default=1.0) or 1.0
        mem_rows = sparklines(mem_list, minimum=-bound, maximum=bound)
        while len(mem_rows) < 2:
            mem_rows = [" " * HISTORY] + mem_rows

        hint = "q: quit"
        cpu_label = f"CPU  {cpu_spark}  {self._cpu[-1]:5.1f}%"
        width = (self.size.width or 80) - 2  # account for padding: 0 1
        cpu_line = cpu_label + " " * max(0, width - len(cpu_label) - len(hint)) + hint

        self.update(
            f"{cpu_line}\n"
            f"MEM  {mem_rows[0]}  {self._mem[-1]:+6.1f} MB/s\n"
            f"     {mem_rows[1]}"
        )


class CPUMonitorApp(App):
    """Terminal app showing sliding CPU load and memory delta sparklines."""

    TITLE = "CPU / Memory Monitor"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:  # noqa: D102  # skipcq: PYL-R0201
        yield MonitorBar()


if __name__ == "__main__":
    CPUMonitorApp().run()
