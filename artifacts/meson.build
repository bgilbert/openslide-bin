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

fs = import('fs')
openslide_jar = openslide_java.get_variable('openslide_jar')
artifact_dir = get_option('prefix') / 'artifacts'
artifacts = [
  custom_target(
    'VERSIONS.md',
    command : [find_program('write-project-versions.py'), '-o', '@OUTPUT@'],
    output : 'VERSIONS.md',
    # ensure we regenerate after dependency updates
    build_always_stale : true,
    env : env,
    install : true,
    install_dir : get_option('datadir'),
  ),
  custom_target(
    'openslide.jar',
    command : ['cp', '@INPUT@', '@OUTPUT@'],
    input : openslide_jar,
    output : fs.name(openslide_jar.full_path()),
    install : true,
    install_dir : artifact_dir,
  ),
]

postprocess = find_program('postprocess-binary.py')
foreach bin : [
  openslide.get_variable('libopenslide'),
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
    install : true,
    install_dir : artifact_dir,
  )
endforeach
