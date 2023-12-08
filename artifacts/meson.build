env = environment()
env.prepend('PYTHONPATH', meson.project_source_root())
# Meson doesn't pass MESONINTROSPECT to custom targets
# https://github.com/mesonbuild/meson/issues/12492
mesonintrospect = run_command(
  files('get-introspect-command.py'),
  capture : true,
  check : true,
).stdout().strip()
env.set('MESONINTROSPECT', mesonintrospect)
# nor MESON_SOURCE_ROOT
env.set('MESON_SOURCE_ROOT', meson.project_source_root())
env.set('LD', find_program('ld').full_path())
if system == 'linux'
  env.set('PATCHELF', find_program('patchelf').full_path())
endif
if system == 'darwin'
  env.set('DSYMUTIL', find_program('dsymutil').full_path())
  env.set('DYLD_INFO', find_program('dyld_info').full_path())
  env.set('INSTALL_NAME_TOOL', find_program('install_name_tool').full_path())
  env.set('OTOOL', find_program('otool').full_path())
  env.set('STRIP', find_program('strip').full_path())
else
  env.set('OBJCOPY', find_program('objcopy').full_path())
  env.set('OBJDUMP', find_program('objdump').full_path())
endif

meson.add_dist_script(
  files('postprocess-sdist.py'), '-i', mesonintrospect
)

artifacts = [
  custom_target(
    command : [find_program('write-project-versions.py'), '-o', '@OUTPUT@'],
    output : 'VERSIONS.md',
    # ensure we regenerate after dependency updates
    build_always_stale : true,
    env : env,
  ),
  openslide.get_variable('openslide_headers'),
  openslide_java.get_variable('openslide_jar'),
  meson.project_source_root() / 'CHANGELOG.md',
]

licenses = custom_target(
  command : [find_program('write-licenses.py'), '@OUTPUT@'],
  output : 'licenses',
  # ensure we regenerate after dependency updates
  build_always_stale : true,
  env : env,
)
artifacts += licenses

libopenslide = openslide.get_variable('libopenslide')
if system == 'windows'
  artifacts += custom_target(
    command : [
      find_program('write-import-library.py'), '@INPUT@', '@OUTPUT@'
    ],
    input : libopenslide,
    output : 'libopenslide.lib',
    env : env,
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
    command : [postprocess, '@INPUT@', '-o', '@OUTPUT0@', '-d', '@OUTPUT1@'],
    input : bin,
    output : [name, name + (system == 'darwin' ? '.dSYM' : '.debug')],
    env : env,
  )
endforeach

custom_target(
  command : [
    find_program('write-bdist.py'), '-o', '@OUTPUT@', '@INPUT@'
  ],
  input : artifacts,
  output : '@0@-@1@-@2@.@3@'.format(
    meson.project_name(),
    meson.project_version(),
    meson.get_external_property('openslide_bin_platform'),
    system == 'windows' ? 'zip' : 'tar.xz'
  ),
  env : env,
  build_by_default : true,
)