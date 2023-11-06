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
import copy
import functools
from io import BytesIO
import os
from pathlib import Path, PurePath
import re
import tarfile
import tempfile

from common import *

DSYM_ARCHES = set(['aarch64', 'x86_64'])

def all_of(items, func):
    return all(func(item) for item in items)


def all_equal(items):
    return all_of(items, lambda item: item == items[0])


def addfile_from(tar, info, data=None):
    info = copy.copy(info)
    info.name = PurePath.joinpath(
        get_archive_base_path(tar.fileobj._fp.name),
        *PurePath(info.name).parts[1:]
    ).as_posix()
    # clear extended headers that may contradict the new name
    info.pax_headers = {}
    if data is not None:
        info.size = len(data)
        data = BytesIO(data)
    tar.addfile(info, data)


class Tars:
    def __init__(self, files):
        self.tars = [tarfile.open(fileobj=fh) for fh in files]

    def __iter__(self):
        while True:
            infos = [tar.next() for tar in self.tars]
            if not any(infos):
                return
            yield FileSet(self.tars, infos)


class FileSet:
    def __init__(self, tars, infos):
        self.tars = tars
        self.infos = infos
        self.relpaths = [
            PurePath(*PurePath(info.name).parts[1:]) for info in self.infos
        ]

    @functools.cached_property
    def datas(self):
        ret = []
        for tar, info in zip(self.tars, self.infos):
            with tar.extractfile(info) as fh:
                ret.append(fh.read())
        return ret

    def merge_into(self, out):
        if not all_equal(self.relpaths):
            # path mismatch, which we only allow for dSYM relocations.
            # ensure we have a path component which is a dSYM arch
            if not all_of(
                self.relpaths, lambda p: DSYM_ARCHES.intersection(p.parts)
            ):
                raise Exception(f'Path mismatch: {self.relpaths}')
            if all_of(self.infos, lambda i: i.type == tarfile.DIRTYPE):
                for info in self.infos:
                    addfile_from(out, info)
            elif all_of(self.infos, lambda i: i.type == tarfile.REGTYPE):
                for info, data in zip(self.infos, self.datas):
                    addfile_from(out, info, data)
            else:
                raise Exception(
                    f'Unknown/mismatched types for relocations: {self.relpaths}'
                )
        elif all_of(self.infos, lambda info: info.type == tarfile.DIRTYPE):
            addfile_from(out, self.infos[0])
        elif (
            all_of(self.infos, lambda info: info.type == tarfile.SYMTYPE)
            and all_equal([info.linkname for info in self.infos])
        ):
            addfile_from(out, self.infos[0])
        elif all_of(self.infos, lambda info: info.type == tarfile.REGTYPE):
            if self.datas[0][0:4] == b'\xcf\xfa\xed\xfe':
                data = self._merge_macho()
            elif fs.relpaths[0].suffix == '.jar':
                # non-reproducible build; pick one
                data = self.datas[0]
            elif all_equal(fs.datas):
                data = self.datas[0]
            else:
                raise Exception(f'Contents mismatch: {self.relpaths}')
            addfile_from(out, self.infos[0], data)
        else:
            raise Exception(f'Unknown/mismatched types: {self.relpaths}')

    def _merge_macho(self):
        with tempfile.TemporaryDirectory(prefix='bdist-') as dir:
            dir = Path(dir)
            inpaths = []
            for i, data in enumerate(self.datas):
                inpath = dir / str(i)
                inpath.write_bytes(data)
                inpaths.append(inpath)
            outpath = dir / 'out'
            subprocess.check_call(
                ['lipo', '-create', '-output', outpath] + inpaths
            )
            return outpath.read_bytes()


parser = argparse.ArgumentParser(
    'write-universal-bdist', description='Write macOS universal bdist archive.'
)
parser.add_argument(
    '-o', '--output', type=argparse.FileType('wb'), required=True,
    help='output file'
)
parser.add_argument(
    'bdist', nargs='+', type=argparse.FileType('rb'), help='input file'
)
args = parser.parse_args()

with tarfile.open(
    fileobj=args.output, mode='w:xz', format=tarfile.PAX_FORMAT, preset=9
) as out:
    for fs in Tars(args.bdist):
        fs.merge_into(out)
