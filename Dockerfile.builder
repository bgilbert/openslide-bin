FROM registry.fedoraproject.org/fedora:36
RUN dnf -y install ant cmake gcc gettext-devel glib2-devel java-devel-openjdk \
    meson mingw{32,64}-gcc-c++ nasm zip && \
    dnf clean all
