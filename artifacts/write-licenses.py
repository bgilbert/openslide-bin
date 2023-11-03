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
from pathlib import Path

from common import *

parser = argparse.ArgumentParser(
    'write-licenses', description='Write licenses directory.'
)
parser.add_argument(
    'dir', help='output directory'
)
args = parser.parse_args()

root = Path(args.dir)
if root.exists():
    shutil.rmtree(root)
for proj in Project.get_enabled():
    proj.write_licenses(root / proj.display)
