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

import configparser
from datetime import date
import json
import os
from pathlib import Path, PurePath
import re
import shlex
import shutil
import subprocess

class Project:
    def __init__(self, id, display, licenses, marker=''):
        self.id = id
        self.display = display
        self.licenses = licenses
        self.marker = marker

    @staticmethod
    def get(id):
        for p in _PROJECTS:
            if p.id == id:
                return p
        raise KeyError

    @staticmethod
    def get_enabled():
        enabled = set(
            s['name'] for s in meson_introspect('projectinfo')['subprojects']
        )
        ret = [p for p in _PROJECTS if p.id in enabled]
        unknown = enabled - _PROJECTS_IGNORE - set([p.id for p in ret])
        if unknown:
            raise Exception(f'Unknown projects: {unknown}')
        return ret

    def get_wrap_file(self):
        path = meson_source_root() / 'subprojects' / f'{self.id}.wrap'
        with open(path) as fh:
            wrap = configparser.RawConfigParser()
            wrap.optionxform = str
            wrap.read_file(fh)
            return wrap

    def get_wrap_version(self):
        try:
            # get the wrapdb_version, including the package revision
            wrap = self.get_wrap_file()
            ver = wrap.get('wrap-file', 'wrapdb_version', fallback=None)
            if not ver:
                # older or non-wrapdb wrap; parse the directory name
                ver = wrap.get('wrap-file', 'directory').split('-')[-1]
            return ver
        except FileNotFoundError:
            # overridden source directory; ask the subproject (may not be
            # as reliable, e.g. proxy-libintl)
            for sub in meson_introspect('projectinfo')['subprojects']:
                if sub['name'] == self.id:
                    return sub['version']
            raise Exception(f'Missing project info for {self.id}')

    def get_source_dir(self):
        try:
            dirname = self.get_wrap_file().get('wrap-file', 'directory')
        except FileNotFoundError:
            # overridden source directory
            dirname = self.id
        return meson_source_root() / 'subprojects' / dirname

    def write_licenses(self, dir):
        dir.mkdir(parents=True)
        for license in self.licenses:
            if hasattr(license, '__call__'):
                name, contents = license(self)
                with open(dir / name, 'w') as fh:
                    fh.write(contents)
            else:
                shutil.copy2(
                    self.get_source_dir() / license,
                    dir / Path(license).name
                )


def sqlite3_license(proj):
    '''Extract public-domain dedication from the top of sqlite3.h'''
    with open(proj.get_source_dir() / 'sqlite3.h') as fh:
        ret = []
        for line in fh:
            if not line.startswith('**'):
                continue
            if line.startswith('*****'):
                return 'PUBLIC-DOMAIN.txt', ''.join(ret)
            ret.append(line)


# All projects in VERSIONS.md order
_PROJECTS = (
    Project(
        id='openslide', display='OpenSlide', marker='**',
        licenses=['COPYING.LESSER'],
    ),
    Project(
        id='openslide-java', display='OpenSlide Java', marker='**',
        licenses=['COPYING.LESSER'],
    ),
    Project(
        id='zlib', display='zlib',
        licenses=['README'],
    ),
    Project(
        id='libpng', display='libpng',
        licenses=['LICENSE'],
    ),
    Project(
        id='libjpeg-turbo', display='libjpeg-turbo',
        licenses=['LICENSE.md', 'README.ijg'],
    ),
    Project(
        id='libtiff', display='libtiff',
        licenses=['LICENSE.md'],
    ),
    Project(
        id='libopenjp2', display='OpenJPEG',
        licenses=['LICENSE'],
    ),
    Project(
        id='sqlite3', display='SQLite',
        licenses=[sqlite3_license],
    ),
    Project(
        id='proxy-libintl', display='proxy-libintl',
        licenses=['COPYING'],
    ),
    Project(
        id='libffi', display='libffi',
        licenses=['LICENSE'],
    ),
    Project(
        id='pcre2', display='PCRE2',
        licenses=['LICENCE'],
    ),
    Project(
        id='glib', display='glib',
        licenses=['COPYING'],
    ),
    Project(
        id='gdk-pixbuf', display='gdk-pixbuf',
        licenses=['COPYING'],
    ),
    Project(
        id='pixman', display='pixman',
        licenses=['COPYING'],
    ),
    Project(
        id='cairo', display='cairo',
        licenses=['COPYING', 'COPYING-LGPL-2.1', 'COPYING-MPL-1.1'],
    ),
    Project(
        id='libxml2', display='libxml2',
        licenses=['Copyright'],
    ),
    Project(
        id='uthash', display='uthash',
        licenses=['LICENSE'],
    ),
    Project(
        id='libdicom', display='libdicom',
        licenses=['LICENSE'],
    ),
)

# gvdb is a copylib bundled with glib, without a stable API
_PROJECTS_IGNORE = set(['gvdb'])


def meson_source_root():
    return Path(os.environ['MESON_SOURCE_ROOT'])


def meson_introspect(keyword):
    cmd = shlex.split(os.environ['MESONINTROSPECT']) + [f'--{keyword}']
    return json.loads(subprocess.check_output(cmd))


def meson_host():
    return meson_introspect('machines')['host']['system']


def default_version():
    return date.today().strftime('%Y%m%d') + '-local'


def write_project_versions(fh, env_info={}):
    def line(name, version, marker=''):
        print('| {:20} | {:53} |'.format(
            f'{marker}{name}{marker}', f'{marker}{version}{marker}'
        ), file=fh)
    line('Software', 'Version')
    line('--------', '-------')
    for proj in Project.get_enabled():
        line(proj.display, proj.get_wrap_version(), proj.marker)
    for software, version in env_info.items():
        line(software, version, '_')


def get_archive_base_path(path):
    return PurePath(re.sub('\\.(tar\\.(gz|xz)|zip)$', '', PurePath(path).name))
