# Changelog

> **Note:** Not all versions listed here were published as GitHub releases.
> PyPI remains the authoritative source for all released versions.

## 1.0.0

- Mixed positive/negative data is now auto-detected and rendered as a
  proportional split sparkline automatically — no flags required. Upward bars
  appear on top, downward bars below.
- All-negative data now renders as inverted (downward) bars automatically.
- New -n / --num-lines accepts three forms: a positive integer (total rows,
  allocated proportionally), 'auto' (smallest proportional row count), or
  'up:down' (explicit per-side layout). Integer and auto modes use a shared
  max scale; up:down uses independent per-side scaling.
- New --zero flag: 'up' (default) places zeros on the positive baseline;
  'none' omits zeros from both sides.
- Removed inverted=True / -i/--inverted and split=True / -s/--split from the
  public API. Inverted rendering is now an internal implementation detail.
- Removed -v/--verbose CLI flag and verbose= parameter (were no-ops since
  introduction; never produced any output).
- Proportional row allocation: up_rows/total == pos_max/range, so the zero
  line stays meaningful as the visual boundary between halves.
- ANSI reverse video with complement block characters gives full 8-level
  resolution for downward bars. Falls back to top-fill Unicode characters
  (▔▀█) when NO_COLOR, ANSI_COLORS_DISABLED, or TERM=dumb is set.
- Fixed: color emphasis (-e) in mixed positive/negative sparklines is now
  evaluated against the original values, not the abs-converted partition.
  Conditions like "blue:lt:0" now correctly match negative bars.
- New index-slice form for -e/--emphasize: "color:[start:stop:step]" selects
  bars by position rather than value, using standard Python slice syntax
  (e.g. "red:[0:3]", "blue:[::2]", "yellow:[-1:]"). Value and slice
  expressions can be mixed freely.
- Fixed: --wrap with mixed positive/negative data now correctly interleaves
  the positive and negative rows per window, rather than emitting all positive
  windows followed by all negative windows.

## 0.7.0

- Changed license from GPL to MIT starting with version 0.7.0

## 0.6.0

- Move from setup.py and setup.cfg to pyproject.toml
- Add workflow for test releases on test.pypi.org
- Various updates in github workflow files
- Add type annotations
- Drop support for Python 3.8

## 0.5.0

- Dropped Python 2 support
- Replaced Travis build with GitHub build action
- Removed minified pytest code
- Added a fix regarding regex for Python 3.12

## 0.4.2

- Fixed a buglet preventing pip install without future already installed

## 0.4.1

- Improved command-line option -e/--emphasize to take only one argument,
  but can be used repeatedly now, which reduces unexpected behaviour

## 0.4.0

- Made rounding consistent across Python 2 and 3 (bankers' rounding)
- Added future dependency for this kind of rounding in Python 2
- Added filter to unclutter input numbers (remove commas, etc.)
- Added tox support
- Added more tests
- Added asciicast to README

## 0.3.0

- Removed typos related to singular/plural forms of "sparkline/s"
- Added color emphasis in output using "termcolor" package (if present)

## 0.2.0

- Increased resolution with multiple output lines per sparkline
- Show gaps in input numbers for missing data
- Issue warnings for negative values (allowed, but misleading)
- Tested on Python 2 and 3
- Packaged code

## 0.1.0 — unreleased
