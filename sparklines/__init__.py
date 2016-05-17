#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

if sys.version_info.major >= 3:
	from sparklines.sparklines import *
else:
	from sparklines import *

del sys
