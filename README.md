# generating a new compiler suite Bazel module

This file shows how to generate a new Bazel module encapsulating a GCC compiler suite.
For this example, we want to build from the stable releases and the development tips of
`binutils`, `gcc`, and `glibc` for x86_64 and riscv architectures.

We'll use the x86_64 and riscv-64 compiler suite development tips as examples.  These will become the `gcc_x86_64_suite` and the `gcc_riscv_suite` Bazel Modules.
These modules will use Bazel module versioning, with a patch number following the GCC version number.  For the example below, we will be creating
`gcc_x86_64_suite` and `gcc_riscv_suite` version 15.0.1.0 using a snapshot of GCC 15.0.1 as the baseline source.

It takes several steps to generate each Bazel crosscompiler toolchain:

1. Git pull or clone sources for binutils, gcc, and glibc.  For this example, these are found under `/home2/vendor`.
2. Configure and compile those sources into `/home2/build_riscv` and `/home2/build_x86`.  The configuration step specifies intermediate
   install directories `/opt/riscv/sysroot` and `/opt/x86_64/sysroot`.
3. Install the crosscompiler suites into `/opt`.  The tools will have many hard-coded paths dependent on the local host's `/opt`.  We want portable toolchains that don't
   reference `/opt` or local host toolchain components.
4. Review the intermediate install directories under `/opt` to remove older files (needed for bootstrapping the compilers) and remove any
   absolute paths to `/opt/...`, `/usr`, etc.
5. Identify the subset of files in the intermediate install directories intended for the Bazel tarballs. These files are specified in
   python scripts like `script/gcc_riscv.py`.  The files and their locations depend
   on specific suite releases, so these scripts likely need to be updated.
6. Run the desired script to collect needed files, strip unnecessary debugging information, replace duplicates with hard links, and
   generate the compressed Bazel module tarballs.  The scripts will install the new Bazel modules (tarball plus metadata) under
   `/opt/bazel/bzlmod/`.
7. Test the new modules to verify all desired files are present and nothing references host directories like `/usr/` or `/opt/riscv64`.
   This is usually an iterative process, especially making sure that all of the obscure files needed by the linker/loader are present
   and on a relative file path.
8. Move the installation directory `/opt/riscv/` to `/opt/riscv_save` and `/opt/x86_64/` to `/opt/x86_64_save` before exercising the new
   modules within Bazel.  This helps test hermeticity, so that `bazel build` can never directly use the local compiler suite components.

## update the source directories

The source git repos are stored locally under `/home2/vendor`.  We want to verify we are
on the master or main branch of each, then update with a `git pull`.

```console
$ cd /home2/vendor/binutils-gdb
$ git status
$ git remote -v
origin	https://sourceware.org/git/binutils-gdb.git (fetch)
$ git pull
# select the most recent release
$ git checkout binutils-2_44
$ cd ../gcc
$ git status
$ git remote -v
origin	git://gcc.gnu.org/git/gcc.git (fetch)
$ git pull
$ cd ../glibc
$ git status
$ git remote -v
origin	https://sourceware.org/git/glibc.git (fetch)
$ git pull
```

## create the build directories

We build outside of the source directories

```console
$ cd /home2
$ mkdir build_x86
$ cd build_x86
$ mkdir -p binutils gcc glibc
$ mkdir build_riscv
$ cd build_riscv
$ mkdir -p binutils gcc glibc
```

## x86_64 compiler suite build

### create the new install directory

>Note: The `sysroot` directory holds files provided by the kernel.  We need something generic here to
>      bootstrap our compiler build.

```console
$ mkdir -p /opt/x86_64/sysroot
```

## configure, build, and install

### binutils needs to be first

```console
$ cd /home2/build_x86/binutils
$ ../../vendor/binutils-gdb/configure --prefix=/opt/x86_64/sysroot --with-sysroot=/opt/x86_64/sysroot --target=x86_64-pc-linux-gnu
$ make
$ make install
$ tree /opt/x86_64/sysroot/bin
/opt/x86_64/sysroot/bin
├── addr2line
├── ar
├── as
...
├── ld
├── ld.bfd
├── nm
├── objcopy
├── objdump
├── ranlib
├── readelf
├── size
├── strings
└── strip
```

### gcc is next, but it needs bootstrapping

We need to add previous-generation or generic kernel files before gcc will completely build

```console
$ /home2/vendor/gcc/configure --prefix=/opt/x86_64/sysroot \
      --enable-languages=c,c++ \
      --disable-multilib \
      --with-sysroot=/opt/x86_64/sysroot \
      --target=x86_64-pc-linux-gnu
$ make
```

The directory (BUILD_SYSTEM_HEADER_DIR) that should contain system headers does not exist:
  /opt/x86_64/sysroot/usr/include

```
$ mkdir -p /opt/x86_64/sysroot/usr/include
$ meld /opt/x86_64/sysroot/usr/include /usr/include
```

Iterate with `make`, adding include files and other bootstrap files like `libc.*`, `crti.o`, and
especially `crt1.o` and `libpthread*`.

You may need to repeat the `/home2/vendor/gcc/configure` step so that the Makefile system recognizes
critical dependencies are present.

At this point our bootstrap sysroot directory looks like this:

```console
$ tree -L 2 usr
usr
├── include
│   ├── aio.h
...
│   ├── stdbit.h
│   ├── stdc-predef.h
│   ├── stdint.h
│   ├── stdio_ext.h
│   ├── stdio.h
│   ├── stdlib.h
│   ├── string.h
│   ├── strings.h
│   ├── sys
│...
│   └── zstd.h
├── lib
└── lib64
    ├── libgmp.so
    ├── libgmp.so.10
    ├── libgmp.so.10.4.1
    ├── libisl.so
    ├── libisl.so.15
    ├── libisl.so.15.1.1
    ├── libmpc.so
    ├── libmpc.so.3
    ├── libmpc.so.3.3.1
    ├── libmpfr.so
    ├── libmpfr.so.6
    ├── libmpfr.so.6.2.1
    ├── libm.so
    └── libm.so.6
$ tree -L 2 lib
lib
├── bfd-plugins
│   └── libdep.so
├── crt1.o
├── crti.o
├── crtn.o
├── gprofng
│   ├── libgp-collectorAPI.a
│   ├── libgp-collectorAPI.la
│   ├── libgp-collectorAPI.so
│   ├── libgp-collector.so
│   ├── libgp-heap.so
│   ├── libgp-iotrace.so
│   └── libgp-sync.so
├── ld-linux-x86-64.so.2
├── libbfd.a
├── libbfd.la
├── libc.a
├── libc_nonshared.a
├── libc.so
├── libc.so.6
├── libctf.a
├── libctf.la
├── libctf-nobfd.a
├── libctf-nobfd.la
├── libgprofng.a
├── libgprofng.la
├── libinproctrace.so
├── libmvec.so.1
├── libopcodes.a
├── libopcodes.la
├── libpthread.a
├── libsframe.a
└── libsframe.la
$ tree -L 2 lib64
lib64
├── crt1.o
├── crti.o
├── crtn.o
├── ld-linux-x86-64.so.2
├── libc_nonshared.a
├── libc.so
├── libc.so.6
├── libmvec.so.1
└── libpthread.so.0
```

This process collects both compiler dependencies and system dependencies under `/opt/x86_64/sysroot`.
If this example was for a riscv crosscompiler running on an x86_64 host, that means
our `sysroot` will have a mix of x86_64 and riscv sharable libraries

After iterating with `make` until we get a clean build we can install gcc to our `sysroot` directory with

```console
$ make install
```

### glibc

>Note: the steps below build glibc using the native host compiler, not the gcc version we just built.  A production system would likely alter `configure` step to use the new
`gcc` with an architecture definition taking advantage of the target system's ISA extensions.

```console
$ cd /home2/build_x86/glibc
$ /home2/vendor/glibc/configure --prefix=/opt/x86_64/sysroot --with-sysroot=/opt/x86_64/sysroot --target=x86_64-pc-linux-gnu
$ make
$ make install
```

### cleanup

The compiler suite is very large and non-portable.  We need to replace absolute
path references to `/opt` or `/usr` with relative paths, remove older files
used for bootstrapping, strip binaries and libraries, and delete larger tools
we don't want for the deployed compiler suite, such as `lto`, `gprof`, and others.

First look for any loader scripts which use absolute paths rather than relative paths.
These are very short `*.so` files holding loader scripts rather than binaries or
symbolic links.

```console
$ cd /opt/x86_64
$ find . -name \*.so -size -10b -ls | grep -v '\->'
303 Jun 24 15:58 ./sysroot/lib/libc.so
146 Jun 24 15:59 ./sysroot/lib/libm.so
100 Jun 24 12:15 ./sysroot/usr/lib64/libm.so
234 Jun 24 11:38 ./sysroot/lib64/libc.so
132 Jun 24 15:45 ./sysroot/lib64/libgcc_s.so

$ cat sysroot/lib/libc.so
/* GNU ld script
   Use the shared library, but some functions are only in
   the static library, so try that secondarily.  */
OUTPUT_FORMAT(elf64-x86-64)
GROUP ( /opt/x86_64/sysroot/lib/libc.so.6 /opt/x86_64/sysroot/lib/libc_nonshared.a  AS_NEEDED ( /opt/x86_64/sysroot/lib/ld-linux-x86-64.so.2 ) )
```

Edit these to use only relative paths.  For `libc.so`, this will become:

```console
$ cat sysroot/lib/libc.so
/* GNU ld script
   Use the shared library, but some functions are only in
   the static library, so try that secondarily.  */
OUTPUT_FORMAT(elf64-x86-64)
GROUP ( ./libc.so.6 ./libc_nonshared.a  AS_NEEDED ( ./ld-linux-x86-64.so.2 ) )
```

## Repeat for riscv

### configuration

binutils:

```console
$ /home2/vendor/binutils-gdb/configure --prefix=/opt/riscv/sysroot --with-sysroot=/opt/riscv/sysroot --target=riscv64-unknown-linux-gnu
```

gcc:

```console
$ ../../vendor/gcc/configure --prefix=/opt/riscv/sysroot --with-sysroot=/opt/riscv/sysroot --target=riscv64-unknown-linux-gnu --disable-multilib --enable-languages=c,c++
```

glibc:

```console
$ ../../vendor/glibc/configure riscv64-unknown-linux-gnu CC=/opt/riscv/sysroot/bin/riscv64-unknown-linux-gnu-gcc LD=/opt/riscv/sysroot/bin/riscv64-unknown-linux-gnu-ld AR=/opt/riscv/sysroot/bin/riscv64-unknown-linux-gnu-ar --prefix=/opt/riscv/sysroot --with-headers=/opt/riscv/sysroot/usr/include --disable-multilib
```

### build

The build steps for riscv follow the same sequence as for x86_64.

## Testing and cleanup

Find the gcc executables now installed in `/opt/x86_64` and `/opt/riscv`, then check their version numbers:

```console
$ find x86_64 riscv -name \*gcc -ls
 18495440  17872 -rwxr-xr-x 18298344 Jan 22 18:57 x86_64/sysroot/bin/gcc
 18495440  17872 -rwxr-xr-x 18298344 Jan 22 18:57 x86_64/sysroot/bin/x86_64-pc-linux-gnu-gcc
 14473792      0 drwxr-xr-x       38 May 14  2024 x86_64/sysroot/lib/gcc
 14473788      0 drwxr-xr-x       38 May 14  2024 x86_64/sysroot/libexec/gcc
 18510386  16784 -rwxr-xr-x 17186336 Jan 23 09:31 riscv/sysroot/bin/riscv64-unknown-linux-gnu-gcc
 18506773      0 drwxr-xr-x       50 Jan 23 07:16 riscv/sysroot/lib/gcc
 18508221      0 drwxr-xr-x       50 Jan 23 07:16 riscv/sysroot/libexec/gcc

$ x86_64/sysroot/bin/gcc --version
gcc (GCC) 15.0.1 20250122 (experimental)
...
$ riscv/sysroot/bin/riscv64-unknown-linux-gnu-gcc --version
riscv64-unknown-linux-gnu-gcc (GCC) 15.0.1 20250122 (experimental)
...
```

### Pruning sysroot

We used older versions of key files to bootstrap the crosscompiler build.  Now we want to locate many of those old files and remove them, so that the compiler
and loader only find the newer versions.  We need to do this without removing critical files not supplied by `binutils`, `gcc`, or `glibc`.

Start pruning with the riscv directory.

The previous crosscompiler build identified itself as GCC version 15.0.0.  This build identifies as version 15.0.1, so we can delete:
   * `riscv/sysroot/libexec/gcc/riscv64-unknown-linux-gnu/15.0.0`
   * `riscv/sysroot/riscv64-unknown-linux-gnu/include/c++/15.0.0`
   * `riscv/sysroot/lib/gcc/riscv64-unknown-linux-gnu/15.0.0`
   * `riscv/sysroot/share/gcc-15.0.0`
   * `riscv/sysroot/bin/riscv64-unknown-linux-gnu-gcc-15.0.0`

Pruning `include` files requires an understanding of the current compiler's search path.

```console
riscv/sysroot/bin/riscv64-unknown-linux-gnu-gcc -v -E  - < /dev/null 2>&1 
Using built-in specs.
COLLECT_GCC=riscv/sysroot/bin/riscv64-unknown-linux-gnu-gcc
Target: riscv64-unknown-linux-gnu
Configured with: /home2/vendor/gcc/configure --prefix=/opt/riscv/sysroot --with-sysroot=/opt/riscv/sysroot --enable-languages=c,c++ --disable-multilib --target=riscv64-unknown-linux-gnu
Thread model: posix
Supported LTO compression algorithms: zlib zstd
gcc version 15.0.1 20250122 (experimental) (GCC) 
COLLECT_GCC_OPTIONS='-v' '-E' '-march=rv64imafdc_zicsr_zifencei_zaamo_zalrsc' '-mabi=lp64d' '-misa-spec=20191213' '-mtls-dialect=trad' '-march=rv64imafdc_zicsr_zifencei_zmmul_zaamo_zalrsc_zca_zcd'
 /opt/riscv/sysroot/libexec/gcc/riscv64-unknown-linux-gnu/15.0.1/cc1 -E -quiet -v -imultilib . - -march=rv64imafdc_zicsr_zifencei_zaamo_zalrsc -mabi=lp64d -misa-spec=20191213 -mtls-dialect=trad -march=rv64imafdc_zicsr_zifencei_zmmul_zaamo_zalrsc_zca_zcd -dumpbase -
ignoring nonexistent directory "/opt/riscv/sysroot/usr/local/include"
#include "..." search starts here:
#include <...> search starts here:
 /opt/riscv/sysroot/lib/gcc/riscv64-unknown-linux-gnu/15.0.1/include
 /opt/riscv/sysroot/lib/gcc/riscv64-unknown-linux-gnu/15.0.1/include-fixed
 /opt/riscv/sysroot/lib/gcc/riscv64-unknown-linux-gnu/15.0.1/../../../../riscv64-unknown-linux-gnu/include
 /opt/riscv/sysroot/usr/include
End of search list.
```

This means we are likely to have older files in `/opt/riscv/sysroot/usr/include` that should be replaced by files in `/opt/riscv/sysroot/lib/gcc/riscv64-unknown-linux-gnu/15.0.1/include`

Find any `*.so` loader script files using absolute paths, and edit them to convert the paths to relative paths.

```console
$ find riscv -name \*.so -size -10 -type f -ls
 18511003      4 -rw-r--r-- 132 Jan 23 09:31 riscv/sysroot/riscv64-unknown-linux-gnu/lib/libgcc_s.so
 18507397      4 -rw-r--r-- 132 Jan 23 07:16 riscv/sysroot/lib/libgcc_s.so
 18512000      4 -rw-r--r-- 309 Jan 23 09:47 riscv/sysroot/lib/libc.so
```

For example, `riscv/sysroot/lib/libc.so` includes absolute path references:

```text
GROUP ( /opt/riscv/sysroot/lib/libc.so.6 /opt/riscv/sysroot/lib/libc_nonshared.a  AS_NEEDED ( /opt/riscv/sysroot/lib/ld-linux-riscv64-lp64d.so.1 ) )
```

This line must be edited to use relative paths:

```text
GROUP ( ./libc.so.6 ./libc_nonshared.a  AS_NEEDED ( ./ld-linux-riscv64-lp64d.so.1 ) )
```

The actual selection of files to be packaged in our compiler toolchain modules will be made later, so we don't have to be too aggressive in
pruning the directory in which we installed the compiler suite.

Moving to the x86_64 directory, we can delete any version 15.0.0 or 14.* directories.

Next look for any sysroot bootstrap files that may not have been replaced during the installation.
Use `find` to locate any crt*.o or libc.so* files that may remain from the bootstrap.

You can screen for some compiled files remaining from the bootstrap sysroot by checking a newly built and linked
executable for earlier GCC tags:

```console
$ strings riscv64/exemplars/whisper_cpp_vector|grep GCC
GCC_3.0
GCC: (GNU) 15.0.0 20240620 (experimental)
_Unwind_Resume@GCC_3.0
```

If any references like `GCC: (GNU) 14.1.0` exist, that likely means a sysroot file like `crt1.o` remains from the bootstrap.

## Adding Bazel metadata

A compiler suite module includes a tarball holding a subset of crosscompiler files plus two
Bazel files.  These are collected under the `src` directory, for our example that's `src/gcc_riscv_suite`.

The first file is `MODULE.bazel`, naming and versioning the module and declaring `fedora_syslibs` as
a dependency holding the dynamic libraries needed to execute the crosscompiler and other suite tools.

```text
module(
    name = "gcc_riscv_suite",
    version = "15.0.1.0",
)
bazel_dep(name = "fedora_syslibs", version="41.0.1")
```

The second file is `BUILD`, which identifies the subset of compiler suite files to be made available
to Bazel build systems.

```text
package(default_visibility = ["//visibility:public"])

GCC_VERSION = "15.0.1"

# Assign names to different crosscompiler components

filegroup(
    name = "std_includes",
    srcs = glob(["usr/include/**"]),
)

filegroup(
    name = "libexec",
    srcs = glob(["libexec/gcc/riscv64-unknown-linux-gnu/{}/**".format(GCC_VERSION)]),
)
...
filegroup(
    name = "compiler_files",
    srcs = [
        "bin/riscv64-unknown-linux-gnu-ar",
        "bin/riscv64-unknown-linux-gnu-as",
        "bin/riscv64-unknown-linux-gnu-cpp",
        "bin/riscv64-unknown-linux-gnu-gcc",
        "bin/riscv64-unknown-linux-gnu-ld",
        "bin/riscv64-unknown-linux-gnu-ld.bfd",
        "bin/riscv64-unknown-linux-gnu-objdump",
        "bin/riscv64-unknown-linux-gnu-ranlib",
        "bin/riscv64-unknown-linux-gnu-strip",
        "bin/riscv64-unknown-linux-gnu-readelf",
        ":c++_std_includes",
        ":lib",
        ":libexec",
        ":std_includes",
        "@fedora_syslibs//:common_compiler_ldd_dependencies",
    ],
)
```

Other files may be included in the compiler suite tarball, but these will not be
available within the Bazel hermetic sandbox without identification here.


## Generating the Bazel compiler suite module

For toolchain files to be available for users they must satisfy at least these conditions:

1. They must be built and installed into `/opt/...`.
2. They must be identified by name or glob in the `rsync` portion of the python script `src/gcc_*.py`
3. They must be collected into named Bazel file groups in the module's `BUILD` file.
4. The file groups must be referenced by name in a toolchain or project `BUILD` file.

The next step selects and strips files from the crosscompiler suite install directory `/opt/riscv`
into `src/gcc_riscv_suite` for inclusion in the compiler suite tarball.  The python script
`scripts/gcc_riscv.py` identifies these files, strips them with an x86 or riscv `strip` utility,
generates the tarball and its sha-256 hash, then installs the tarball and its metadata in the local
Bzlmod repository.  A production shop would then expose the Bzlmod repo as a https or nfs networked
resource - we'll just keep it local for now.

```console
$ scripts/gcc_riscv.py
...
INFO:root:tempfile name = /tmp/tmp5wxq1cpy
...
sending incremental file list

sent 86,610 bytes  received 203 bytes  173,626.00 bytes/sec
total size is 1,588,065,603  speedup is 18,292.95

INFO:root:selectively imported /opt/riscv/sysroot into /home/thixotropist/projects/github/bazel_compiler_modules/src/gcc_riscv_suite
copying Bazel BUILD and MODULE.bazel files from /home/thixotropist/projects/github/bazel_compiler_modules/src/gcc_riscv_suite to /opt/bazel/bzlmod/src/gcc_riscv_suite/15.0.1.0
copying Bazel MODULE.bazel files from /home/thixotropist/projects/github/bazel_compiler_modules/src/gcc_riscv_suite to /opt/bazel/bzlmod/modules/gcc_riscv_suite/15.0.1.0
...
INFO:root:stripped binary bin/riscv64-unknown-linux-gnu-addr2line
INFO:root:stripped binary bin/riscv64-unknown-linux-gnu-ar
INFO:root:stripped binary bin/riscv64-unknown-linux-gnu-as
INFO:root:stripped binary bin/riscv64-unknown-linux-gnu-c++
INFO:root:stripped binary bin/riscv64-unknown-linux-gnu-c++filt
INFO:root:stripped binary bin/riscv64-unknown-linux-gnu-cpp
INFO:root:removed duplicates from /home/thixotropist/projects/github/bazel_compiler_modules/src/gcc_riscv_suite
INFO:root:Removing previous tarball
INFO:root:Generating tarball - this will take a while
INFO:root:generated tarball /opt/bazel/bzlmod/tarballs/gcc_riscv_suite-15.0.1.0.tar.xz
INFO:root:generated sha256 digest 8zKnVAyzUKPHECjmNZwbSKkS21+U9HdRXQDd7Bo5jis=
INFO:root:updated module source.json with new digest 8zKnVAyzUKPHECjmNZwbSKkS21+U9HdRXQDd7Bo5jis=
INFO:root:copied MODULE.bazel from source to bzlmod repo
```

The two bzlmod tarballs should be about 50 MB in size compressed or about 240 MB when loaded into
a Bazel externals cache directory like `/run/user/1000/bazel/external/gcc_riscv_suite+`.

## Testing the Bazel compiler suite module

The `examples` directory holds a reference toolchain we can use to test the compiler suite module.

The module we just built can be accessed via `examples/MODULE.bazel`:

```py
module(
    name = "bazel_compiler_modules_examples",
    version = "0.1",
)

bazel_dep(name="gcc_riscv_suite", version="15.0.1.0")
bazel_dep(name="gcc_x86_64_suite", version="15.0.1.0")
# The two gcc crosscompiler suites depend on the following for sharable object libraries
bazel_dep(name="fedora_syslibs", version="41.0.1")

register_toolchains(
    # currently gcc-riscv64 with most of the rva23 extensions (vector, bit manipulation, ...)
    "//toolchains/riscv:riscv64-rva23",
    # a generic x86_64 toolchain useful for unit testing
    "//toolchains/x86:x86_64-native",
)
```

>Note: the Bazel-enabled GCC toolchain suite  must be identified within `examples/toolchains/build`.
>      for this example, that's `SUITE_MODULE = "gcc_riscv_suite"` and `SUITE_VERSION = "15.0.1.0"`

```console
$ cd examples
$ bazel shutdown
$ bazel clean
$ bazel build --platforms=//platforms:riscv64 helloworld
Target //:helloworld up-to-date:
  bazel-bin/helloworld
INFO: Elapsed time: 6.694s, Critical Path: 0.02s
INFO: 1 process: 6 action cache hit, 1 internal.
INFO: Build completed successfully, 1 total action
$ file bazel-bin/helloworld
bazel-bin/helloworld: ELF 64-bit LSB executable, UCB RISC-V, RVC, double-float ABI, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-riscv64-lp64d.so.1, for GNU/Linux 4.15.0, not stripped
```

Our local x86_64 host happens to include a qemu user-space emulator, so we can execute our new RISCV binary:

```console
# Identify the RISCV processor ISA so that any vector instructions are emulated
$ export QEMU_CPU=rv64,zba=true,zbb=true,v=true,vlen=128,vext_spec=v1.0,rvv_ta_all_1s=true,rvv_ma_all_1s=true
$ qemu-riscv64-static -L /opt/riscv/sysroot -E LD_LIBRARY_PATH=/opt/riscv/sysroot/riscv64-unknown-linux-gnu/lib/ bazel-bin/helloworld
Hello World!
```

## System Library Dependencies

The host crosscompiler components expect to find a number of shared libraries at runtime.  If we want a portable
toolchain, we need those to be found in a portable system Bazel module, not from the local host system.

For example, the compiler component `cc1` depends on these system libraries at specific versions:

* libisl.so.15
* libmpc.so.3
* libmpfr.so.6
* libgmp.so.10
* libzstd.so.1
* libstdc++.so.6
* libm.so.6
* libgcc_s.so.1
* libc.so.6

These versions are those found on a Fedora 41 workstation at the time the compiler suites were built.
We need to package these as a Bazel module and register that module as a dependency of any compiler suites
built together.  

```py
bazel_dep(name="fedora_syslibs", version="41.0.1")
```

Each of the toolchain wrappers should use these libraries.  For example, toolchains/riscv/gcc-risc/imported/gcc:

```bash
#!/bin/bash
set -euo pipefail
LD_LIBRARY_PATH=external/fedora_syslibs+:/lib64 \
  external/gcc_riscv_suite+/bin/riscv64-unknown-linux-gnu-gcc "$@"
```
