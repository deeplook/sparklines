# Sparklines

[![Build](https://img.shields.io/github/actions/workflow/status/deeplook/sparklines/lint-test.yml)](https://pypi.org/project/sparklines)
[![Python versions](https://img.shields.io/pypi/pyversions/sparklines.svg)](https://pypi.org/project/sparklines)
[![PyPI version](https://img.shields.io/pypi/v/sparklines.svg)](https://pypi.org/project/sparklines/)
[![Downloads](https://static.pepy.tech/badge/sparklines/month)](https://pepy.tech/project/sparklines)
[![Status](https://img.shields.io/pypi/status/sparklines.svg)](https://pypi.org/project/sparklines)
[![Format](https://img.shields.io/pypi/format/sparklines.svg)](https://pypi.org/project/sparklines)
[![License](https://img.shields.io/pypi/l/sparklines.svg)](https://pypi.org/project/sparklines)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/deeplook)

Sparklines brings Edward Tufte's [sparklines] to your terminal — compact Unicode bar charts like ▃▁▄▁▅█▂▅, right in your shell or Python code. Originally built for sanity-checking sensor data in IoT networks, it works anywhere you need a quick visual summary of a sequence of numbers.

<p align="center">
  <img src="https://raw.githubusercontent.com/deeplook/sparklines/main/example_sensors.png" width="75%" alt="example usecase with sensor values">
  <br>
  <em>Example usecase for such "sparklines" on the command-line,
  showing IoT sensor values (generating code not included here).</em>
</p>

Positive values work best, but negatives are fully supported: mixed data auto-splits into two rows, all-negative data renders as downward bars (see [Mixed and negative datasets] below). True line-style sparklines would require a dedicated font — out of scope here. We use "▁▂▃▄▅▆▇█" for values and a blank for missing ones.

## Sample output

A recorded demo session — click the image to play it on [Asciinema]:

[![asciicast](https://asciinema.org/a/5xwfvcrrk09fy3ml3a8n67hep.png)](https://asciinema.org/a/5xwfvcrrk09fy3ml3a8n67hep)

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

**From PyPI**

```bash
pip install sparklines
```

**On macOS with Homebrew**

```bash
brew tap deeplook/sparklines
brew install sparklines
```

**With uv**

```bash
uvx sparklines 2 7 1 8 2 8 1 8
```

Or install it into your `uv` tool environment:

```bash
uv tool install sparklines
```

**From Source**

```bash
git clone https://github.com/deeplook/sparklines.git
cd sparklines
pip install .
```

**Development**

```bash
git clone https://github.com/deeplook/sparklines.git
cd sparklines
pip install -e ".[dev]"
pytest tests
```


## Usage

Please note that the samples below might look a little funky (misaligned or
even colored) in some browsers, but it should be totally fine when you print
this in your terminal, Python or IPython session or your Python IDE of choice.
The figure below might show better what you should expect than the copied sample
code thereafter:

<p align="center">
  <img src="https://raw.githubusercontent.com/deeplook/sparklines/main/example_python.png" width="65%" alt="example interactive invocation">
  <br>
  <em>Example invocation from a Python and an IPython session.</em>
</p>


### Python

```python
from sparklines import sparklines

for line in sparklines([1, 2, 3, 4, 5.0, None, 3, 2, 1]):
    print(line)
# ▁▃▅▆█ ▅▃▁

for line in sparklines([1, 2, 3, 4, 5.0, None, 3, 2, 1], num_lines=2):
    print(line)
#   ▁▅█ ▁
# ▁▅███ █▅▁
```


### Mixed and negative datasets

Mixed positive/negative data is split automatically — no flags needed:

```python
from sparklines import sparklines

data = [50, 30, 80, -20, -60, -10, 40, 10]
for line in sparklines(data):
    print(line)
# ▅▃█   █▁
#    ▂▆▁
```

All-negative data renders as inverted (downward) bars automatically.

**`-n` / `--num-lines`**

| Form | Behaviour |
|------|-----------|
| integer (default `1`) | total rows, split proportionally; shared scale |
| `auto` | smallest row count for an exact proportional split |
| `up:down` (e.g. `2:1`) | explicit per-side layout; independent scaling |

```console
$ sparklines -n auto 1 2 3 -1 -2 -3 0 4 5 6
$ sparklines -n 2:1  1 2 3 -1 -2 -3 0 4 5 6
```

**`--zero`**: `up` (default) places zeros on the positive baseline; `none` renders them as gaps.

```console
$ sparklines --zero up   0 1 2 -1 -2 0
$ sparklines --zero none 0 1 2 -1 -2 0
```

Downward bars use ANSI reverse video for full 8-level resolution. Falls back to `▔▀█` when `NO_COLOR`, `ANSI_COLORS_DISABLED`, or `TERM=dumb` is set.


References

Inspired by Zach Holman's [spark](https://github.com/holman/spark), with prior Python ports by Kenneth Reitz ([spark.py](https://raw.githubusercontent.com/kennethreitz/spark.py/master/spark.py)), RedKrieg ([pysparklines](https://github.com/RedKrieg/pysparklines)), and Roger Allen ([shorter spark.py](https://gist.githubusercontent.com/rogerallen/1368454/raw/b17e96b56ae881621a9f3b1508ca2e7fde3ec93e/spark.py)).

This package adds:

- multi-line rendering for higher resolution (-n)
- gaps for missing values (None)
- auto-split for mixed positive/negative data
- inverted bars for all-negative data
- proportional row allocation (-n auto)
- explicit per-side layout (-n up:down)
- zero handling (--zero up / --zero none)
- colour emphasis via --emphasize
- line wrapping via --wrap

[Asciinema]: https://asciinema.org
[Python Package Index]: https://pypi.python.org/pypi/sparklines/
[uv]: https://docs.astral.sh/uv/
[sparklines]: http://www.edwardtufte.com/bboard/q-and-a-fetch-msg?msg_id=0001OR
[Mixed and negative datasets]: #mixed-and-negative-datasets
