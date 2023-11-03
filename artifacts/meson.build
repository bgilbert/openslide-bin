env = {
  # Meson doesn't pass MESONINTROSPECT to custom targets
  # https://github.com/mesonbuild/meson/issues/12492
  'MESONINTROSPECT': run_command(
    files('get-introspect-command.py'),
    capture : true,
    check : true,
  ).stdout().strip(),
  # nor MESON_SOURCE_ROOT
  'MESON_SOURCE_ROOT': meson.project_source_root(),
  'LD': find_program('ld').full_path(),
}
if system == 'linux'
  env += {
    'PATCHELF': find_program('patchelf').full_path(),
  }
endif
if system == 'darwin'
  env += {
    'DSYMUTIL': find_program('dsymutil').full_path(),
    'DYLD_INFO': find_program('dyld_info').full_path(),
    'INSTALL_NAME_TOOL': find_program('install_name_tool').full_path(),
    'OTOOL': find_program('otool').full_path(),
    'STRIP': find_program('strip').full_path(),
  }
else
  env += {
    'OBJCOPY': find_program('objcopy').full_path(),
    'OBJDUMP': find_program('objdump').full_path(),
  }
endif

libopenslide = openslide.get_variable('libopenslide')
artifacts = [
  custom_target(
    'VERSIONS.md',
    command : [find_program('write-project-versions.py'), '-o', '@OUTPUT@'],
    output : 'VERSIONS.md',
    # ensure we regenerate after dependency updates
    build_always_stale : true,
    env : env,
  ),
  custom_target(
    'licenses',
    command : [find_program('write-licenses.py'), '@OUTPUT@'],
    output : 'licenses',
    # ensure we regenerate after dependency updates.  we know what source
    # files we used, so could generate a depfile instead, but it isn't worth
    # the effort
    build_always_stale : true,
    env : env,
  ),
  openslide.get_variable('openslide_headers'),
  openslide_java.get_variable('openslide_jar'),
]

if system == 'windows'
  artifacts += custom_target(
    'libopenslide.lib',
    command : [
      find_program('write-import-library.py'), '@INPUT@', '@OUTPUT@'
    ],
    input : libopenslide,
    output : 'libopenslide.lib',
  )
endif

fs = import('fs')
postprocess = find_program('postprocess-binary.py')
foreach bin : [
  libopenslide,
  openslide.get_variable('slidetool'),
  openslide_java.get_variable('openslide_jni'),
]
  name = fs.name(bin.full_path())
  artifacts += custom_target(
    bin.name(),
    command : [postprocess, '@INPUT@', '-o', '@OUTPUT0@', '-d', '@OUTPUT1@'],
    input : bin,
    output : [name, name + (system == 'darwin' ? '.dSYM' : '.debug')],
    env : env,
  )
endforeach

distfile = '@0@-@1@-@2@.@3@'.format(
  meson.project_name(),
  meson.get_external_property('openslide_bin_platform'),
  meson.project_version(),
  system == 'windows' ? 'zip' : 'tar.xz'
)
custom_target(
  distfile,
  command : [
    find_program('write-bdist.py'), '-o', '@OUTPUT@', '@INPUT@'
  ],
  input : artifacts,
  output : distfile,
  env : env,
  build_by_default : true,
)
