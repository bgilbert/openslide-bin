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
from pathlib import Path
import shlex
import subprocess

class Project:
    def __init__(self, id, display, marker=''):
        self.id = id
        self.display = display
        self.marker = marker

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


# All projects in VERSIONS.md order
_PROJECTS = (
    Project(
        id='openslide', display='OpenSlide', marker='**',
    ),
    Project(
        id='openslide-java', display='OpenSlide Java', marker='**',
    ),
    Project(
        id='zlib', display='zlib',
    ),
    Project(
        id='libpng', display='libpng',
    ),
    Project(
        id='libjpeg-turbo', display='libjpeg-turbo',
    ),
    Project(
        id='libtiff', display='libtiff',
    ),
    Project(
        id='libopenjp2', display='OpenJPEG',
    ),
    Project(
        id='sqlite3', display='SQLite',
    ),
    Project(
        id='proxy-libintl', display='proxy-libintl',
    ),
    Project(
        id='libffi', display='libffi',
    ),
    Project(
        id='pcre2', display='PCRE2',
    ),
    Project(
        id='glib', display='glib',
    ),
    Project(
        id='gdk-pixbuf', display='gdk-pixbuf',
    ),
    Project(
        id='pixman', display='pixman',
    ),
    Project(
        id='cairo', display='cairo',
    ),
    Project(
        id='libxml2', display='libxml2',
    ),
    Project(
        id='uthash', display='uthash',
    ),
    Project(
        id='libdicom', display='libdicom',
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
