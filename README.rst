Sparklines
==========

.. image:: https://img.shields.io/github/actions/workflow/status/deeplook/sparklines/lint-test.yml
  :target: https://pypi.org/project/sparklines

.. image:: https://img.shields.io/pypi/pyversions/sparklines.svg
  :target: https://pypi.org/project/sparklines
  
.. image:: https://img.shields.io/pypi/v/sparklines.svg
  :target: https://pypi.org/project/sparklines/

.. image:: https://static.pepy.tech/badge/sparklines/month
  :target: https://pepy.tech/project/sparklines

.. image:: https://img.shields.io/pypi/status/sparklines.svg
  :target: https://pypi.org/project/sparklines

.. image:: https://img.shields.io/pypi/format/sparklines.svg
  :target: https://pypi.org/project/sparklines

.. image:: https://img.shields.io/pypi/l/sparklines.svg
  :target: https://pypi.org/project/sparklines
  
This Python package implements Edward Tufte's concept of sparklines_, but
limited to text only e.g. like this: ▃▁▄▁▅█▂▅ (this I likely not displayed
correctly in every browser). You can find more information about sparklines
`on Wikipedia`_. This code was mainly developed for running simple
plausibility tests in sensor networks as shown in fig. 1 below:

.. figure:: https://raw.githubusercontent.com/deeplook/sparklines/main/example_sensors.png
   :width: 75%
   :alt: example usecase with sensor values
   :align: center

   Fig. 1: Example usecase for such "sparklines" on the command-line,
   showing IoT sensor values (generating code not included here).

Due to limitations of available Unicode characters this works best when all
values are positive. And even then true sparklines that look more like lines
and less like bars are a real challenge, because they would need multiple
characters with a single horizontal line on different vertical positions. This
would work only with a dedicated font, which is way beyond the scope of this
tool and which would significantly complicate its usage. So we stick to these
characters: "▁▂▃▄▅▆▇█", and use a blank for missing values.

Sample output
-------------

This is a recorded sample session illustrating how to use ``sparklines`` (as
GitHub doesn't render embedded Asciinema_ recordings you'll see here an image
pointing to the respective
`asciicast <https://asciinema.org/a/5xwfvcrrk09fy3ml3a8n67hep>`_):

.. image:: https://asciinema.org/a/5xwfvcrrk09fy3ml3a8n67hep.png
   :target: https://asciinema.org/a/5xwfvcrrk09fy3ml3a8n67hep

Here is some example output on the command-line (please note that in some
browsers the vertical alignment of these block characters might be displayed
slightly wrong, the same effect can be seen for other repos referenced below):

Examples for the code below:

.. code-block:: bash

    $ sparklines 2 7 1 8 2 8 1 8
    ▂▇▁█▂█▁█
    $ echo 2 7 1 8 2 8 1 8 | sparklines
    ▂▇▁█▂█▁█
    $ sparklines < numbers.txt
    ▂▇▁█▂█▁█
    $ sparklines 0 2. 1e0
    ▁█▅


Installation
------------

**From PyPI (Recommended)**

You can install this package from the `Python Package Index`_ using pip:

.. code-block:: bash

    pip install sparklines

**From Source**

To install from source, clone this repository and install it:

.. code-block:: bash

    git clone https://github.com/deeplook/sparklines.git
    cd sparklines
    pip install .

**Development Installation**

For development work, install in editable mode with development dependencies:

.. code-block:: bash

    git clone https://github.com/deeplook/sparklines.git
    cd sparklines
    pip install -e ".[dev]"

After installing, you will have access system-wide (or in your virtual environment
if you have used one) to the ``sparklines`` command-line tool, as well as the Python
module for programmatic use.


Test
----

To run the test suite, download and unpack this repository or clone it,
and run the command ``pytest tests`` in the unpacked archive in the downloaded
repository root folder.


Usage
-----

Please note that the samples below might look a little funky (misaligned or 
even colored) in some browsers, but it should be totally fine when you print
this in your terminal, Python or IPython session or your Python IDE of choice.
Figure 2 below might show better what you should expect than the copied sample
code thereafter:

.. figure:: https://raw.githubusercontent.com/deeplook/sparklines/main/example_python.png
   :width: 65%
   :alt: example interactive invocation
   :align: center

   Fig. 2: Example invocation from a Python and an IPython session.


Command-Line
............

Here are two sample invocations from the command-line, copied into this README:

.. code-block:: console

    $ sparklines 1 2 3 4 5.0 null 3 2 1
    ▁▃▅▆█ ▅▃▁

    $ sparklines -n 2 1 2 3 4 5.0 null 3 2 1
      ▁▅█ ▁  
    ▁▅███ █▅▁


Programmatic
............

And here are sample invocations from interactive Python sessions, copied into
this README. The main function to use programmatically is 
``sparklines.sparklines()``:

.. code-block:: python

    In [1]: from sparklines import sparklines

    In [2]: for line in sparklines([1, 2, 3, 4, 5.0, None, 3, 2, 1]):
       ...:     print(line)
       ...:     
    ▁▃▅▆█ ▅▃▁

    In [3]: for line in sparklines([1, 2, 3, 4, 5.0, None, 3, 2, 1], num_lines=2):
        print(line)
       ...:     
      ▁▅█ ▁  
    ▁▅███ █▅▁


References
----------

This code was inspired by Zach Holman's `spark 
<https://github.com/holman/spark>`_, converted to a Python module 
by Kenneth Reitz as `spark.py 
<https://raw.githubusercontent.com/kennethreitz/spark.py/master/spark.py>`_ 
and by RegKrieg to a Python package named `pysparklines <https://github.com/RedKrieg/pysparklines>`_.
And Roger Allen provides an even `shorter spark.py 
<https://gist.githubusercontent.com/rogerallen/1368454/raw/b17e96b56ae881621a9f3b1508ca2e7fde3ec93e/spark.py>`_.

But since it is so short and easy to code in Python we can add a few nice
extra features I was missing, like:

- increasing resolution with multiple output lines per sparkline
- showing gaps in input numbers for missing data
- issuing warnings for negative values (allowed, but misleading)
- highlighting values exceeding some threshold with a different color
- wrapping long sparklines at some max. length
- (todo) adding separator characters like ``:`` at regular intervals

.. _Asciinema: https://asciinema.org
.. _Python Package Index: https://pypi.python.org/pypi/sparklines/
.. _sparklines: http://www.edwardtufte.com/bboard/q-and-a-fetch-msg?msg_id=0001OR
.. _on Wikipedia: https://en.wikipedia.org/wiki/Sparkline
