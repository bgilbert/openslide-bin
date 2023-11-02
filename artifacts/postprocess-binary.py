#!/usr/bin/env python3
#
# Tools for building OpenSlide and its dependencies
#
# Copyright (c) 2011-2015 Carnegie Mellon University
# Copyright (c) 2022-2023 Benjamin Gilbert
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
import re
import subprocess

from common import *

def library_symbols(args):
    if host == 'linux':
        out = subprocess.check_output([
            os.environ['OBJDUMP'], '-T', args.file
        ]).decode()
        return [
            l.split()[6] for l in out.split('\n') if '.text' in l
        ]
    elif host == 'darwin':
        out = subprocess.check_output([
            os.environ['DYLD_INFO'], '-exports', args.file
        ]).decode()
        return [
            l.split()[1].lstrip('_') for l in out.split('\n') if ' 0x' in l
        ]
    elif host == 'windows':
        out = subprocess.check_output([
            os.environ['OBJDUMP'], '-p', args.file
        ]).decode()
        active = False
        syms = []
        for line in out.split('\n'):
            if active:
                if not line.strip():
                    return syms
                syms.append(line.split()[2])
            elif 'Ordinal/Name Pointer' in line:
                active = True
                continue


parser = argparse.ArgumentParser(
    'postprocess-binary', description='Mangle shared library or executable.'
)
parser.add_argument(
    '-o', '--output', required=True, help='output file'
)
parser.add_argument(
    '-d', '--debuginfo', required=True, help='output debug symbols'
)
parser.add_argument(
    'file', help='input file'
)
args = parser.parse_args()
host = meson_host()

# split debuginfo
if host == 'darwin':
    subprocess.check_call([
        os.environ['DSYMUTIL'], '-o', args.debuginfo, args.file
    ])
    subprocess.check_call([
        os.environ['STRIP'], '-u', '-r', '-o', args.output, args.file
    ])
else:
    objcopy = os.environ['OBJCOPY']
    subprocess.check_call([
        objcopy, '--only-keep-debug', args.file, args.debuginfo
    ])
    os.chmod(args.debuginfo, 0o644)
    parent = Path(args.debuginfo).parent
    assert parent == Path(args.output).parent
    # debuglink without a directory path enables search semantics
    subprocess.check_call([
        objcopy, '-S', f'--add-gnu-debuglink={Path(args.debuginfo).name}',
        Path(args.file).absolute(), Path(args.output).absolute(),
    ], cwd=parent)

# check for extra symbol exports
if re.search('\\.(dll|dylib|so[.0-9]*)$', args.file):
    syms = library_symbols(args)
    if not syms:
        raise Exception(f"Couldn't find exported symbols in {args.file}")
    syms = [
        # filter out acceptable symbols
        s for s in syms if not s.startswith('openslide_') and s != 'JNI_OnLoad'
    ]
    if syms:
        raise Exception(f'Unexpected exports in {args.file}: {syms}')

# update rpath
if host == 'linux' and not re.match('.so[.0-9]*$', args.file):
    subprocess.check_call([
        os.environ['PATCHELF'], '--set-rpath', '$ORIGIN/../lib', args.output
    ])
elif host == 'darwin' and not args.file.endswith('.dylib'):
    out = subprocess.check_output([
        os.environ['OTOOL'], '-l', args.output
    ]).decode()
    active = False
    for line in out.split('\n'):
        if 'cmd LC_RPATH' in line:
            active = True
        elif active:
            words = line.split()
            if words[0] == 'path':
                old_rpath = words[1]
                break
    else:
        raise Exception("Couldn't read LC_RPATH")
    if args.file.endswith('.jnilib'):
        new_rpath = '@loader_path'
    else:
        new_rpath = '@loader_path/../lib'
    subprocess.check_call([
        os.environ['INSTALL_NAME_TOOL'], '-rpath', old_rpath, new_rpath,
        args.output
    ])
