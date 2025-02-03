#!/usr/bin/python
"""
Convert a riscv compiler suite into a Bazel module
"""
from compiler_suite_generator import Generator

MOD_NAME = "gcc_riscv_suite"
MOD_VERSION = "15.0.1.0"
GCC_VERSION = "15.0.1"
MOD_TARGET = "riscv64-unknown-linux-gnu"
# crosscompilers often need a prefix, native compilers often don't
TARGET_PREFIX = "riscv64-unknown-linux-gnu-"

RSYNC_FILES= f"""
# Include files
+ usr
+ usr/include
+ usr/include/**
+ include
+ include/**

# binaries used within the toolchain, running on the host and generating or manipulating
# binaries on the target architecture.
# exclude for now gdb, gprof, and lto binaries
+ bin
+ bin/{TARGET_PREFIX}addr2line
+ bin/{TARGET_PREFIX}ar
+ bin/{TARGET_PREFIX}as
+ bin/{TARGET_PREFIX}c++filt
+ bin/{TARGET_PREFIX}cpp
+ bin/{TARGET_PREFIX}elfedit
+ bin/{TARGET_PREFIX}g++
+ bin/{TARGET_PREFIX}gcc
+ bin/{TARGET_PREFIX}gcc-ar
+ bin/{TARGET_PREFIX}gcc-nm
+ bin/{TARGET_PREFIX}gcc-ranlib
+ bin/{TARGET_PREFIX}ld
+ bin/{TARGET_PREFIX}ld.bfd
+ bin/{TARGET_PREFIX}ldd
+ bin/{TARGET_PREFIX}nm
+ bin/{TARGET_PREFIX}objcopy
+ bin/{TARGET_PREFIX}objdump
+ bin/{TARGET_PREFIX}ranlib
+ bin/{TARGET_PREFIX}readelf
+ bin/{TARGET_PREFIX}size
+ bin/{TARGET_PREFIX}strings
+ bin/{TARGET_PREFIX}strip

# lib and lib64 exclude most .a files
+ lib
+ lib/libc_nonshared.a
+ lib/ld-linux-riscv64-lp64d.so.1
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
+ {MOD_TARGET}/lib/libasan.so
+ {MOD_TARGET}/lib/libasan.so.8
+ {MOD_TARGET}/lib/libasan.so.8.0.0
+ {MOD_TARGET}/lib/libatomic.so
+ {MOD_TARGET}/lib/libatomic.so.1
+ {MOD_TARGET}/lib/libatomic.so.1.2.0
+ {MOD_TARGET}/lib/liblsan.so
+ {MOD_TARGET}/lib/liblsan.so.0
+ {MOD_TARGET}/lib/liblsan.so.0.0.0
+ {MOD_TARGET}/lib/libstdc++.so
+ {MOD_TARGET}/lib/libstdc++.so.6
+ {MOD_TARGET}/lib/libstdc++.so.6.0.34
+ {MOD_TARGET}/lib/libssp.so
+ {MOD_TARGET}/lib/libssp.so.0
+ {MOD_TARGET}/lib/libssp.so.0.0.0
+ {MOD_TARGET}/lib/libtsan.so
+ {MOD_TARGET}/lib/libtsan.so.2
+ {MOD_TARGET}/lib/libtsan.so.2.0.0
+ {MOD_TARGET}/lib/libubsan.so
+ {MOD_TARGET}/lib/libubsan.so.1
+ {MOD_TARGET}/lib/libubsan.so.1.0.0
+ {MOD_TARGET}/lib/ldscripts
+ {MOD_TARGET}/lib/ldscripts/**
+ {MOD_TARGET}/lib64
+ {MOD_TARGET}/lib64/**
+ {MOD_TARGET}/include
+ {MOD_TARGET}/include/c++
+ {MOD_TARGET}/include/c++/{GCC_VERSION}
+ {MOD_TARGET}/include/c++/{GCC_VERSION}/**
+ {MOD_TARGET}/sys-include
+ {MOD_TARGET}/sys-include/**

# skip everything else
- **
"""

STRIP_FILES = f"""bin/{TARGET_PREFIX}addr2line
bin/{TARGET_PREFIX}ar
bin/{TARGET_PREFIX}as
bin/{TARGET_PREFIX}c++filt
bin/{TARGET_PREFIX}cpp
bin/{TARGET_PREFIX}elfedit
bin/{TARGET_PREFIX}g++
bin/{TARGET_PREFIX}gcc
bin/{TARGET_PREFIX}gcc-ar
bin/{TARGET_PREFIX}gcc-nm
bin/{TARGET_PREFIX}gcc-ranlib
bin/{TARGET_PREFIX}ld
bin/{TARGET_PREFIX}ld.bfd
bin/{TARGET_PREFIX}nm
bin/{TARGET_PREFIX}objcopy
bin/{TARGET_PREFIX}objdump
bin/{TARGET_PREFIX}ranlib
bin/{TARGET_PREFIX}readelf
bin/{TARGET_PREFIX}size
bin/{TARGET_PREFIX}strings
bin/{TARGET_PREFIX}strip
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
generator.set_target_prefix("/opt/riscv/sysroot/bin/riscv64-unknown-linux-gnu-")
generator.clean_mod_src()
generator.rsync_to_mod_src("/opt/riscv/sysroot", RSYNC_FILES)
generator.copy_bazel_files()
generator.strip_binaries(STRIP_FILES)
generator.strip_target_binaries(STRIP_TARGET_FILES)
generator.remove_duplicates()
generator.make_tarball()
