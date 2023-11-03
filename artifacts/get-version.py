#!/usr/bin/env python3
#
# Tools for building OpenSlide and its dependencies
#
# Copyright (c) 2023 Benjamin Gilbert
# All rights reserved.
#
# This script is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License, version 2.1,
# as published by the Free Software Foundation.
#
# This script is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this script. If not, see <http://www.gnu.org/licenses/>.
#

import os

from common import *

# passed-in version has priority
ver = os.environ.get('OPENSLIDE_BIN_VERSION')
# then the one pinned by 'meson dist'
# append "-local" if there's no suffix, to distinguish from official builds
if not ver:
    try:
        ver = (meson_source_root() / 'version').read_text().strip()
        if '-' not in ver:
            ver += '-local'
    except FileNotFoundError:
        pass
# finally, the default
if not ver:
    ver = default_version()
print(ver)
