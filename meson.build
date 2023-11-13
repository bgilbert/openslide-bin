project(
  'openslide-bin',
  'c',
  version : run_command(
    files('utils/get-version.py'),
    capture : true,
    check : true
  ).stdout().strip(),
  license : 'LGPL-2.1-only',
  meson_version : '>=1.2',
  default_options : [
    'buildtype=plain',
    'default_library=static',
    'wrap_mode=nofallback',
  ],
)

system = host_machine.system()

if get_option('pep517')
  # openslide-bin builds OpenSlide and all its dependencies in a controlled
  # environment:
  #
  # - Linux builds are linked against an EL 8 glibc for maximum compatibility.
  # - macOS builds run Meson twice, for x86_64 and arm64, and then merge the
  #   results into a universal build.
  # - Windows builds link against the UCRT, and use a GCC compiled for Win32
  #   threads to avoid producing a dependency on the winpthreads DLL.
  #
  # If we wanted to support building via PEP 517, we'd need to run the entire
  # build from inside a PEP 517 backend (such as meson-python) which isn't
  # designed to emit arbitrary artifacts.  And even that wouldn't be enough,
  # since the only way to get correct wheel tags is to fix the tags *after*
  # the PEP 517 build finishes, e.g. with auditwheel on Linux.
  #
  # Since our actual wheel is very simple, and building a wheel isn't the main
  # purpose of openslide-bin, it's not worth the extra complexity to support
  # pip builds from source.  And so, while the PyPI source package contains
  # exactly the bits that built the binary, the binary build itself has to be
  # performed by directly invoking our build tooling.
  error('Binaries are not available for your platform. Install OpenSlide from source.')
endif

subdir('deps')
subdir('artifacts')
