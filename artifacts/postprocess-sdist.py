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

import argparse
import os
from pathlib import Path

from common import *

parser = argparse.ArgumentParser(
    'postprocess-dist', description='Modify dist directory before packing.'
)
parser.add_argument(
    '-i', '--introspect', help='Meson introspect command'
)
args = parser.parse_args()
root = Path(os.environ['MESON_DIST_ROOT'])
os.environ['MESONINTROSPECT'] = args.introspect

# pin openslide-bin version
(root / 'version').write_text(
    meson_introspect('projectinfo')['version'] + '\n'
)

# write versions of all projects, not just the ones for a particular platform
with open(root / 'VERSIONS.md', 'w') as fh:
    write_project_versions(fh)
