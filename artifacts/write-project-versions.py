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
import re
import subprocess
import sys

from common import *

MINGW_VERSION_CHECK_HDR = b'''
#include <_mingw_mac.h>
#define s(v) #v
#define ss(v) s(v)
ss(__MINGW64_VERSION_MAJOR).ss(__MINGW64_VERSION_MINOR).ss(__MINGW64_VERSION_BUGFIX)
'''

parser = argparse.ArgumentParser(
    'write-project-versions', description='Write subproject version list.'
)
parser.add_argument(
    '-o', '--output', type=argparse.FileType('w'), default=sys.stdout,
    help='output file'
)
args = parser.parse_args()

env_info = {}
compiler = meson_introspect('compilers')['host']['c']
if meson_host() == 'windows':
    out = subprocess.Popen(
        compiler['exelist'] + ['-E', '-'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE
    ).communicate(MINGW_VERSION_CHECK_HDR)[0]
    env_info['MinGW-w64'] = [
        l for l in out.decode().split('\n')
        if l.strip() and not l.startswith('#')
    ][0].replace('"', '')
if compiler['id'] == 'gcc':
    env_info['GCC'] = re.match('[^ ]+ (.+)', compiler['full_version'])[1]
    env_info['Binutils'] = subprocess.check_output(
        [os.environ['LD'], '--version']
    ).decode().split('\n')[0]
elif compiler['id'] == 'clang':
    env_info['Clang'] = re.sub('.* version ', '', compiler['full_version'])

with args.output as fh:
    write_project_versions(fh, env_info)
