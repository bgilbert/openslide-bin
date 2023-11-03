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
from contextlib import closing
import os
from pathlib import Path
import re
import tarfile
import time
import zipfile

from common import *

class ZipArchive:
    def __init__(self, fh):
        self._zip = zipfile.ZipFile(
            fh, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9
        )

    def write_file(self, arcpath, fspath):
        self._zip.write(fspath, arcpath)

    def write_dir(self, arcpath):
        self._zip.writestr(arcpath.as_posix() + '/', b'')

    def write_symlink(self, arcpath, target):
        raise Exception('Symlinks not supported in ZIP')

    def close(self):
        self._zip.close()


class TarArchive:
    def __init__(self, fh):
        self._tar = tarfile.open(
            fileobj=fh, mode='w:xz', format=tarfile.PAX_FORMAT, preset=9
        )
        self._now = int(time.time())

    def write_file(self, arcpath, fspath):
        with open(fspath, 'rb') as fh:
            info = self._tar.gettarinfo(arcname=arcpath, fileobj=fh)
            info.mode = info.mode & ~0o022 | 0o644
            info.uid = 0
            info.gid = 0
            info.uname = 'root'
            info.gname = 'root'
            self._tar.addfile(info, fh)

    def write_dir(self, arcpath):
        info = tarfile.TarInfo(arcpath.as_posix())
        info.mtime = self._now
        info.mode = 0o755
        info.type = tarfile.DIRTYPE
        info.uname = 'root'
        info.gname = 'root'
        self._tar.addfile(info)

    def write_symlink(self, arcpath, target):
        info = tarfile.TarInfo(arcpath.as_posix())
        info.mtime = self._now
        info.mode = 0o777
        info.type = tarfile.SYMTYPE
        info.linkname = target
        info.uname = 'root'
        info.gname = 'root'
        self._tar.addfile(info)

    def close(self):
        self._tar.close()


class Archive:
    def __init__(self, fh):
        self.base = get_archive_base_path(fh.name)
        self._paths = {self.base: None}
        self._symlinks = set()
        self._fh = fh

    def add_file(self, arcpath, fspath):
        assert arcpath not in self._paths
        self._paths[arcpath] = fspath
        while True:
            arcpath = arcpath.parent
            if arcpath == self.base:
                return
            assert self._paths.get(arcpath) is None
            self._paths[arcpath] = None

    def add_symlink(self, arcpath, target):
        self.add_file(arcpath, target)
        self._symlinks.add(arcpath)

    def save(self, verbose=False):
        if meson_host() == 'windows':
            arc = ZipArchive(self._fh)
        else:
            arc = TarArchive(self._fh)
        with closing(arc):
            for arcpath, fspath in sorted(self._paths.items()):
                if verbose:
                    print(arcpath)
                if fspath is None:
                    arc.write_dir(arcpath)
                elif arcpath in self._symlinks:
                    arc.write_symlink(arcpath, fspath)
                else:
                    arc.write_file(arcpath, fspath)


parser = argparse.ArgumentParser(
    'write-bdist', description='Write bdist archive.'
)
parser.add_argument(
    '-o', '--output', type=argparse.FileType('wb'), required=True,
    help='output file'
)
parser.add_argument(
    '-v', '--verbose', action='store_true', help='print archive paths',
)
parser.add_argument(
    'artifact', nargs='+', help='built artifact'
)
args = parser.parse_args()

arc = Archive(args.output)

for fspath in sorted(args.artifact):
    fspath = Path(fspath)
    name = fspath.name
    if re.search(
        '\\.(lib|(dylib|jnilib)(\\.dSYM)?|so[.0-9]*(\\.debug)?)$', name
    ):
        arcdir = arc.base / 'lib'
    elif name.endswith('.h'):
        arcdir = arc.base / 'include/openslide'
    elif name.endswith('.jar'):
        if meson_host() == 'windows':
            arcdir = arc.base / 'bin'
        else:
            arcdir = arc.base / 'lib'
    elif name in ('README.md', 'VERSIONS.md', 'licenses'):
        arcdir = arc.base
    else:
        arcdir = arc.base / 'bin'

    if fspath.is_dir():
        def walkerr(e):
            raise e
        for dpath, _, fnames in os.walk(fspath, onerror=walkerr):
            dpath = Path(dpath)
            for fname in fnames:
                arc.add_file(
                    arcdir / dpath.relative_to(fspath.parent) / fname,
                    dpath / fname
                )
    else:
        arc.add_file(arcdir / name, fspath)
        if re.search('\\.so(\\.[0-9]+){3}$', name):
            for pat in '(\\.[0-9]+){2}$', '(\\.[0-9]+)+$':
                lname = re.sub(pat, '', name)
                arc.add_symlink(arcdir / lname, name)
        elif re.search('\\.[0-9]+\\.dylib$', name):
            lname = re.sub('\\.[0-9]+(\\.dylib)$', lambda m: m.group(1), name)
            arc.add_symlink(arcdir / lname, name)

# special case: copy OpenSlide README to root
openslide_src = Project.get('openslide').get_source_dir()
arc.add_file(arc.base / 'README.md', openslide_src / 'README.md')

arc.save(verbose=args.verbose)
