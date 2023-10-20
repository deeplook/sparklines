#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

if sys.version_info.major >= 3:
    from sparklines.sparklines import *  # noqa: F403
else:
    from sparklines import *  # noqa: F403

del sys
