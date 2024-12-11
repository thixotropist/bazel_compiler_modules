#!/usr/bin/python
"""
Convert the released riscv compiler suite into a Bazel module
"""
from compiler_suite_generator import Generator

MOD_NAME = 'gcc_riscv_suite'
MOD_VERSION = '15.0.0.1'
GCC_VERSION = '15.0.0'
MOD_TARGET = 'riscv64-unknown-linux-gnu'

RSYNC_FILES= f"""
# Include files
+ usr
+ usr/include
+ usr/include/**
- usr/lib
+ include
+ include/**

# binaries used within the toolchain, running on the host and generating or manipulating
# binaries on the target architecture.
# exclude for now gdb and lto binaries
+ bin
+ bin/{MOD_TARGET}-addr2line
+ bin/{MOD_TARGET}-ar
+ bin/{MOD_TARGET}-as
+ bin/{MOD_TARGET}-c++
+ bin/{MOD_TARGET}-c++filt
+ bin/{MOD_TARGET}-cpp
+ bin/{MOD_TARGET}-elfedit
+ bin/{MOD_TARGET}-g++
+ bin/{MOD_TARGET}-gcc
+ bin/{MOD_TARGET}-gcc-{GCC_VERSION}
+ bin/{MOD_TARGET}-gcc-ar
+ bin/{MOD_TARGET}-gcc-nm
+ bin/{MOD_TARGET}-gcc-ranlib
+ bin/{MOD_TARGET}-ld
+ bin/{MOD_TARGET}-ld.bfd
+ bin/{MOD_TARGET}-nm
+ bin/{MOD_TARGET}-objcopy
+ bin/{MOD_TARGET}-objdump
+ bin/{MOD_TARGET}-ranlib
+ bin/{MOD_TARGET}-readelf
+ bin/{MOD_TARGET}-size
+ bin/{MOD_TARGET}-strings
+ bin/{MOD_TARGET}-strip

# lib and lib64 exclude most .a files
+ lib
+ lib/libc_nonshared.a
- lib/lib*.a
+ lib/gcc
+ lib/gcc/{MOD_TARGET}
+ lib/gcc/{MOD_TARGET}/{GCC_VERSION}
+ lib/gcc/{MOD_TARGET}/{GCC_VERSION}/libgcc*.a
- lib/gcc/{MOD_TARGET}/{GCC_VERSION}/lib*.a
+ lib/gcc/{MOD_TARGET}/{GCC_VERSION}/**
+ lib/**

# lib64, excluding compiler support libraries and .a archives
+ lib64
+ lib64/libc_nonshared.a
- lib64/lib*.a
- lib64/libgomp.*
- lib64/libitm.*
- lib64/libquadmath.*
+ lib64/**

# libexec other files needed by the compiler toolchain
+ libexec
+ libexec/gcc
+ libexec/gcc/{MOD_TARGET}
+ libexec/gcc/{MOD_TARGET}/{GCC_VERSION}
- libexec/gcc/{MOD_TARGET}/{GCC_VERSION}/lto1
- libexec/gcc/{MOD_TARGET}/{GCC_VERSION}/lto-wrapper
+ libexec/gcc/{MOD_TARGET}/{GCC_VERSION}/**

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
+ {MOD_TARGET}/lib64
+ {MOD_TARGET}/lib64/**
+ {MOD_TARGET}/include
+ {MOD_TARGET}/include/c++
+ {MOD_TARGET}/include/c++/{GCC_VERSION}
+ {MOD_TARGET}/include/c++/{GCC_VERSION}/**

# skip everything else
- **
"""

STRIP_FILES = f"""bin/{MOD_TARGET}-addr2line
bin/{MOD_TARGET}-ar
bin/{MOD_TARGET}-as
bin/{MOD_TARGET}-c++
bin/{MOD_TARGET}-c++filt
bin/{MOD_TARGET}-cpp
bin/{MOD_TARGET}-elfedit
bin/{MOD_TARGET}-g++
bin/{MOD_TARGET}-gcc
bin/{MOD_TARGET}-gcc-ar
bin/{MOD_TARGET}-gcc-nm
bin/{MOD_TARGET}-gcc-ranlib
bin/{MOD_TARGET}-ld
bin/{MOD_TARGET}-ld.bfd
bin/{MOD_TARGET}-nm
bin/{MOD_TARGET}-objcopy
bin/{MOD_TARGET}-objdump
bin/{MOD_TARGET}-ranlib
bin/{MOD_TARGET}-readelf
bin/{MOD_TARGET}-size
bin/{MOD_TARGET}-strings
bin/{MOD_TARGET}-strip
bin/{MOD_TARGET}-c++
bin/{MOD_TARGET}-gcc-{GCC_VERSION}
lib64/libcc1.so.0.0.0
lib/gcc/{MOD_TARGET}/{GCC_VERSION}/plugin/libcc1plugin.so.0.0.0
lib/gcc/{MOD_TARGET}/{GCC_VERSION}/plugin/libcp1plugin.so.0.0.0
libexec/gcc/{MOD_TARGET}/{GCC_VERSION}/liblto_plugin.so
libexec/gcc/{MOD_TARGET}/{GCC_VERSION}/cc1
libexec/gcc/{MOD_TARGET}/{GCC_VERSION}/cc1plus
libexec/gcc/{MOD_TARGET}/{GCC_VERSION}/collect2
libexec/gcc/{MOD_TARGET}/{GCC_VERSION}/g++-mapper-server
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

STRIP_TARGET_FILES = f"""lib/libm.so.6
lib/libc.so.6
lib/libpthread.so.0
lib/libgcc_s.so.1
{MOD_TARGET}/lib/libgcc_s.so.1
{MOD_TARGET}/lib/libasan.so.8.0.0
{MOD_TARGET}/lib/libatomic.so.1.2.0
{MOD_TARGET}/lib/liblsan.so.0.0.0
{MOD_TARGET}/lib/libssp.so.0.0.0
{MOD_TARGET}/lib/libstdc++.so.6.0.34
{MOD_TARGET}/lib/libtsan.so.2.0.0
{MOD_TARGET}/lib/libubsan.so.1.0.0
"""

generator = Generator(MOD_NAME, MOD_VERSION, MOD_TARGET)
generator.set_target_prefix('/opt/riscvx/sysroot/bin/riscv64-unknown-linux-gnu-')
generator.clean_mod_src()
generator.rsync_to_mod_src('/opt/riscvx/sysroot', RSYNC_FILES)
generator.copy_bazel_files()
generator.strip_binaries(STRIP_FILES)
generator.strip_target_binaries(STRIP_TARGET_FILES)
generator.remove_duplicates()
generator.make_tarball()
