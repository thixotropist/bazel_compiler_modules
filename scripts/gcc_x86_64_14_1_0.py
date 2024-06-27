#!/usr/bin/python
"""
Convert the released x86_64 compiler suite into a Bazel module
"""
from compiler_suite_generator import Generator

MOD_NAME = 'gcc_x86_64_suite'
MOD_VERSION = '14.1.0'
MOD_TARGET = 'x86_64-pc-linux-gnu'

RSYNC_FILES= f"""
# Include files
+ usr
+ usr/include
+ usr/include/**
+ include
+ include/**

# binaries used within the toolchain, running on the host and generating or manipulating
# binaries on the target architecture.
# exclude for now gdb and lto binaries
+ bin
+ bin/addr2line
+ bin/ar
+ bin/as
+ bin/c++
+ bin/c++filt
+ bin/cpp
+ bin/elfedit
+ bin/g++
+ bin/gcc
+ bin/gcc-ar
+ bin/gcc-nm
+ bin/gcc-ranlib
+ bin/gcore
+ bin/iconv
+ bin/ld
+ bin/ld.bfd
+ bin/nm
+ bin/objcopy
+ bin/objdump
+ bin/ranlib
+ bin/readelf
+ bin/size
+ bin/sotruss
+ bin/strings
+ bin/strip
+ bin/tzselect
+ bin/{MOD_TARGET}-c++
+ bin/{MOD_TARGET}-g++
+ bin/{MOD_TARGET}-gcc
+ bin/{MOD_TARGET}-gcc-{MOD_VERSION}
+ bin/{MOD_TARGET}-gcc-ar
+ bin/{MOD_TARGET}-gcc-nm
+ bin/{MOD_TARGET}-gcc-ranlib

# lib and lib64 exclude most .a files
+ lib
+ lib/libc_nonshared.a
- lib/lib*.a
+ lib/gcc
+ lib/gcc/{MOD_TARGET}
+ lib/gcc/{MOD_TARGET}/{MOD_VERSION}
+ lib/gcc/{MOD_TARGET}/{MOD_VERSION}/libgcc*.a
- lib/gcc/{MOD_TARGET}/{MOD_VERSION}/lib*.a
+ lib/gcc/{MOD_TARGET}/{MOD_VERSION}/**
- lib/gprofng
- lib/gprofng.la
- lib/libpthread.so.0
+ lib/**

# lib64, excluding compiler support libraries and .a archives
+ lib64
+ lib64/libc_nonshared.a
- lib64/lib*.a
- lib64/libgomp.*
- lib64/libitm.*
- lib64/libquadmath.*
+ lib64/**

+ usr/lib
- usr/lib/libpthread.so.0
+ usr/lib/**

+ usr/lib64
+ usr/lib64/libm.so
+ usr/lib64/libm.so.6

# libexec other files needed by the compiler toolchain
+ libexec
+ libexec/gcc
+ libexec/gcc/{MOD_TARGET}
+ libexec/gcc/{MOD_TARGET}/{MOD_VERSION}
- libexec/gcc/{MOD_TARGET}/{MOD_VERSION}/lto1
- libexec/gcc/{MOD_TARGET}/{MOD_VERSION}/lto-wrapper
+ libexec/gcc/{MOD_TARGET}/{MOD_VERSION}/**

+ {MOD_TARGET}
+ {MOD_TARGET}/bin
+ {MOD_TARGET}/bin/ar
+ {MOD_TARGET}/bin/as
+ {MOD_TARGET}/bin/ld
+ {MOD_TARGET}/bin/ld.bfd
+ {MOD_TARGET}/bin/nm
+ {MOD_TARGET}/bin/objcopy
+ {MOD_TARGET}/bin/objdump
+ {MOD_TARGET}/bin/ranlib
+ {MOD_TARGET}/bin/readelf
+ {MOD_TARGET}/bin/strip
+ {MOD_TARGET}/lib
+ {MOD_TARGET}/lib/ldscripts
+ {MOD_TARGET}/lib/ldscripts/**

# skip everything else
- **
"""

STRIP_FILES = f"""bin/addr2line
bin/ar
bin/as
bin/c++filt
bin/cpp
bin/elfedit
bin/g++
bin/gcc
bin/gcc-ar
bin/gcc-nm
bin/gcc-ranlib
bin/ld
bin/ld.bfd
bin/nm
bin/objcopy
bin/objdump
bin/ranlib
bin/readelf
bin/size
bin/strings
bin/strip
bin/{MOD_TARGET}-c++
bin/{MOD_TARGET}-g++
bin/{MOD_TARGET}-gcc
bin/{MOD_TARGET}-gcc-{MOD_VERSION}
bin/{MOD_TARGET}-gcc-ar
bin/{MOD_TARGET}-gcc-nm
bin/{MOD_TARGET}-gcc-ranlib
lib/gcc/{MOD_TARGET}/{MOD_VERSION}/plugin/libcc1plugin.so.0.0.0
lib/gcc/{MOD_TARGET}/{MOD_VERSION}/plugin/libcp1plugin.so.0.0.0
lib/libc.so.6
lib/libinproctrace.so
lib/libm.so.6
lib/libmvec.so.1
lib64/libasan.so.8.0.0
lib64/libatomic.so.1.2.0
lib64/libc.so.6
lib64/libcc1.so.0.0.0
lib64/libstdc++.so.6.0.33
lib64/libtsan.so.2.0.0
lib64/libgcc_s.so.1
lib64/libhwasan.so.0.0.0
lib64/liblsan.so.0.0.0
lib64/libpthread.so.0
lib64/libssp.so.0.0.0
lib64/libubsan.so.1.0.0
usr/lib64/libm.so.6
libexec/gcc/{MOD_TARGET}/{MOD_VERSION}/liblto_plugin.so
libexec/gcc/{MOD_TARGET}/{MOD_VERSION}/cc1
libexec/gcc/{MOD_TARGET}/{MOD_VERSION}/cc1plus
libexec/gcc/{MOD_TARGET}/{MOD_VERSION}/collect2
libexec/gcc/{MOD_TARGET}/{MOD_VERSION}/g++-mapper-server
{MOD_TARGET}/bin/ar
{MOD_TARGET}/bin/as
{MOD_TARGET}/bin/ld
{MOD_TARGET}/bin/ld.bfd
{MOD_TARGET}/bin/objcopy
{MOD_TARGET}/bin/objdump
{MOD_TARGET}/bin/ranlib
{MOD_TARGET}/bin/readelf
{MOD_TARGET}/bin/strip
"""

generator = Generator(MOD_NAME, MOD_VERSION, MOD_TARGET)
generator.clean_mod_src()
generator.rsync_to_mod_src('/opt/x86_64/sysroot', RSYNC_FILES)
generator.strip_binaries(STRIP_FILES)
generator.remove_duplicates()
generator.make_tarball()
