# Sparklines

[![Build](https://img.shields.io/github/actions/workflow/status/deeplook/sparklines/lint-test.yml)](https://pypi.org/project/sparklines)
[![Python versions](https://img.shields.io/pypi/pyversions/sparklines.svg)](https://pypi.org/project/sparklines)
[![PyPI version](https://img.shields.io/pypi/v/sparklines.svg)](https://pypi.org/project/sparklines/)
[![Downloads](https://static.pepy.tech/badge/sparklines/month)](https://pepy.tech/project/sparklines)
[![Status](https://img.shields.io/pypi/status/sparklines.svg)](https://pypi.org/project/sparklines)
[![Format](https://img.shields.io/pypi/format/sparklines.svg)](https://pypi.org/project/sparklines)
[![License](https://img.shields.io/pypi/l/sparklines.svg)](https://pypi.org/project/sparklines)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/deeplook)

This Python package implements Edward Tufte's concept of [sparklines], but
limited to text only e.g. like this: ▃▁▄▁▅█▂▅ (this might not be displayed
correctly in every browser). You can find more information about sparklines
[on Wikipedia]. This code was mainly developed for running simple
plausibility tests in sensor networks as shown in fig. 1 below:

<p align="center">
  <img src="https://raw.githubusercontent.com/deeplook/sparklines/main/example_sensors.png" width="75%" alt="example usecase with sensor values">
  <br>
  <em>Fig. 1: Example usecase for such "sparklines" on the command-line,
  showing IoT sensor values (generating code not included here).</em>
</p>

This works best when all values are positive, though negative values are
fully supported: mixed data auto-splits into two rows, all-negative data
renders as inverted (downward) bars (see [Mixed and negative datasets] below). True
sparklines that look more like lines and less like bars are a real challenge,
because they would need multiple characters with a single horizontal line on
different vertical positions. This would work only with a dedicated font,
which is way beyond the scope of this tool and which would significantly
complicate its usage. So we stick to these characters: "▁▂▃▄▅▆▇█", and use a
blank for missing values.


## Sample output

This is a recorded sample session illustrating how to use `sparklines` (as
GitHub doesn't render embedded [Asciinema] recordings you'll see here an image
pointing to the respective
[asciicast](https://asciinema.org/a/5xwfvcrrk09fy3ml3a8n67hep)):

[![asciicast](https://asciinema.org/a/5xwfvcrrk09fy3ml3a8n67hep.png)](https://asciinema.org/a/5xwfvcrrk09fy3ml3a8n67hep)

Here is some example output on the command-line (please note that in some
browsers the vertical alignment of these block characters might be displayed
slightly wrong, the same effect can be seen for other repos referenced below):

Examples for the code below:

```bash
$ sparklines 2 7 1 8 2 8 1 8
▂▇▁█▂█▁█
$ echo 2 7 1 8 2 8 1 8 | sparklines
▂▇▁█▂█▁█
$ sparklines < numbers.txt
▂▇▁█▂█▁█
$ sparklines 0 2. 1e0
▁█▅
```


## Installation

**From PyPI (Recommended)**

You can install this package from the [Python Package Index] using pip:

```bash
pip install sparklines
```

**On macOS with Homebrew**

If you prefer Homebrew on macOS, tap the formula and install it with:

```bash
brew tap deeplook/sparklines
brew install sparklines
```

**With uv**

If you use [uv], you can run sparklines without a permanent install:

```bash
uvx sparklines 2 7 1 8 2 8 1 8
```

Or install it into your `uv` tool environment:

```bash
uv tool install sparklines
```

**From Source**

To install from source, clone this repository and install it:

```bash
git clone https://github.com/deeplook/sparklines.git
cd sparklines
pip install .
```

**Development Installation**

For development work, install in editable mode with development dependencies:

```bash
git clone https://github.com/deeplook/sparklines.git
cd sparklines
pip install -e ".[dev]"
```

After installing, you will have access system-wide (or in your virtual environment
if you have used one) to the `sparklines` command-line tool, as well as the Python
module for programmatic use.


## Test

To run the test suite, download and unpack this repository or clone it,
and run the command `pytest tests` in the unpacked archive in the downloaded
repository root folder.


## Usage

Please note that the samples below might look a little funky (misaligned or
even colored) in some browsers, but it should be totally fine when you print
this in your terminal, Python or IPython session or your Python IDE of choice.
Figure 2 below might show better what you should expect than the copied sample
code thereafter:

<p align="center">
  <img src="https://raw.githubusercontent.com/deeplook/sparklines/main/example_python.png" width="65%" alt="example interactive invocation">
  <br>
  <em>Fig. 2: Example invocation from a Python and an IPython session.</em>
</p>


### Command-Line

Here are two sample invocations from the command-line, copied into this README:

```console
$ sparklines 1 2 3 4 5.0 null 3 2 1
▁▃▅▆█ ▅▃▁

$ sparklines -n 2 1 2 3 4 5.0 null 3 2 1
  ▁▅█ ▁
▁▅███ █▅▁
```


### Programmatic

And here are sample invocations from interactive Python sessions, copied into
this README. The main function to use programmatically is
`sparklines.sparklines()`:

```python
In [1]: from sparklines import sparklines

In [2]: for line in sparklines([1, 2, 3, 4, 5.0, None, 3, 2, 1]):
   ...:     print(line)
   ...:
▁▃▅▆█ ▅▃▁

In [3]: for line in sparklines([1, 2, 3, 4, 5.0, None, 3, 2, 1], num_lines=2):
   ...:     print(line)
   ...:
  ▁▅█ ▁
▁▅███ █▅▁
```


### Mixed and negative datasets

When your data contains both positive and negative values, `sparklines`
automatically renders a proportional split: upward bars for positives on top,
downward bars for negatives below. No flags needed:

```python
In [1]: from sparklines import sparklines

In [2]: data = [50, 30, 80, -20, -60, -10, 40, 10]
   ...: for line in sparklines(data):
   ...:     print(line)
   ...:
▅▃█   █▁
   ▂▆▁
```

All-negative data is rendered automatically as inverted (downward) bars.

**Row count: -n / --num-lines**

The `-n` argument accepts three forms:

- Integer (default `1`): total rows, split proportionally between positive
  and negative halves. Both halves share a common scale maximum.
- `auto`: smallest total row count that gives a true proportional split
  (`pos_rows / total == pos_max / range`).
- `up:down` (e.g. `2:1`): explicit per-side layout; each half is scaled
  independently to its own maximum.

```console
$ sparklines -n auto 1 2 3 -1 -2 -3 0 4 5 6
$ sparklines -n 2:1  1 2 3 -1 -2 -3 0 4 5 6
```

**Zero handling: --zero**

- `--zero up` (default): zeros sit on the positive baseline.
- `--zero none`: zeros are rendered as gaps on both sides.

```console
$ sparklines --zero up   0 1 2 -1 -2 0
$ sparklines --zero none 0 1 2 -1 -2 0
```

Downward bars use ANSI reverse video with the complement block character for
full 8-level resolution, matching upward bars. When `NO_COLOR`,
`ANSI_COLORS_DISABLED`, or `TERM=dumb` is set, they fall back to top-fill
Unicode characters (`▔▀█`) at reduced resolution.


## References

This code was inspired by Zach Holman's [spark](https://github.com/holman/spark),
converted to a Python module by Kenneth Reitz as
[spark.py](https://raw.githubusercontent.com/kennethreitz/spark.py/master/spark.py)
and by RegKrieg to a Python package named
[pysparklines](https://github.com/RedKrieg/pysparklines).
And Roger Allen provides an even
[shorter spark.py](https://gist.githubusercontent.com/rogerallen/1368454/raw/b17e96b56ae881621a9f3b1508ca2e7fde3ec93e/spark.py).

But since it is so short and easy to code in Python we can add a few nice
extra features I was missing, like:

- increasing resolution with multiple output lines per sparkline
- showing gaps in input numbers for missing data
- automatic split rendering for mixed positive/negative datasets (no flags needed)
- all-negative data rendered as inverted (downward) bars automatically
- proportional row allocation (`-n auto`) keeps the zero line meaningful
- explicit per-side layout with `-n up:down` and independent scaling
- zero handling via `--zero up` (baseline) or `--zero none` (gap)
- highlighting values exceeding some threshold with a different color
- wrapping long sparklines at some max. length
- (todo) adding separator characters like `:` at regular intervals

[Asciinema]: https://asciinema.org
[Python Package Index]: https://pypi.python.org/pypi/sparklines/
[uv]: https://docs.astral.sh/uv/
[sparklines]: http://www.edwardtufte.com/bboard/q-and-a-fetch-msg?msg_id=0001OR
[on Wikipedia]: https://en.wikipedia.org/wiki/Sparkline
[Mixed and negative datasets]: #mixed-and-negative-datasets
