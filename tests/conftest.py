"""Keep tests deterministic across terminal color environments."""

import pytest


@pytest.fixture(autouse=True)
def enable_ansi_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear user color-suppression settings unless a test opts into them."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("ANSI_COLORS_DISABLED", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
