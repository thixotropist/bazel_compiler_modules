# generating a new compiler suite Bazel module

This file shows how to generate a new Bazel module encapsulating a GCC compiler suite.
For this example, we want to build from the stable releases and the development tips of
`binutils`, `gcc`, and `glibc`
for x86_64 and riscv architectures.

We'll use the x86_64 architecture's development tip as an example, versioning it as `15.0.0`.

## update the source directories

The source git repos are stored locally under `/home2/vendor`.  We want to verify we are
on the master or main branch of each, then update with a `git pull`.

```console
$ cd /home2/vendor/binutils-gdb
$ git status
$ git pull
$ cd ../gcc
$ git status
$ git pull
$ cd ../glibc
$ git status
```

## create the build directories

We build outside of the source directories

```console
$ cd /home2
$ mkdir build_x86x
$ cd build_x86x
$ mkdir -p binutils gcc glibc
```

## create the new install directory

```console
$ mkdir -p /opt/x86_64x/sysroot
```

## configure, build, and install

### binutils needs to be first

```console
$ cd /home2/build_x86x/binutils
$ ../../vendor/binutils-gdb/configure --prefix=/opt/x86_64x/sysroot --with-sysroot=/opt/x86_64x/sysroot --target=x86_64-pc-linux-gnu
$ make
$ make install
$ $ tree /opt/x86_64x/sysroot/bin
/opt/x86_64x/sysroot/bin
├── addr2line
├── ar
├── as
├── c++filt
├── elfedit
├── gcore
├── gdb
├── gdb-add-index
├── gdbserver
├── gp-archive
├── gp-collect-app
├── gp-display-html
├── gp-display-src
├── gp-display-text
├── gprof
├── gprofng
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

We need to add previous-generation files before gcc will completely build

```console
$ /home2/vendor/gcc/configure --prefix=/opt/x86_64x/sysroot \
      --enable-languages=c,c++ \
      --disable-multilib \
      --with-sysroot=/opt/x86_64x/sysroot \
      --target=x86_64-pc-linux-gnu
$ make
...
The directory (BUILD_SYSTEM_HEADER_DIR) that should contain system headers does not exist:
  /opt/x86_64x/sysroot/usr/include
$ mkdir -p /opt/x86_64x/sysroot/usr/include
$ meld /opt/x86_64x/sysroot/usr/include /opt/x86_64/sysroot/usr/include
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
│   ├── aliases.h
│   ├── alloca.h
│   ├── a.out.h
│   ├── argp.h
│   ├── argz.h
│   ├── ar.h
│   ├── arpa
│   ├── asm
│   ├── asm-generic
│   ├── assert.h
│   ├── bits
│   ├── btparse.h
│   ├── byteswap.h
│   ├── complex.h
│   ├── cpio.h
│   ├── crypt.h
│   ├── ctype.h
│   ├── cursesapp.h
│   ├── cursesf.h
│   ├── curses.h
│   ├── cursesm.h
│   ├── cursesp.h
│   ├── cursesw.h
│   ├── cursslk.h
│   ├── dirent.h
│   ├── dlfcn.h
│   ├── elf.h
│   ├── endian.h
│   ├── envz.h
│   ├── err.h
│   ├── errno.h
│   ├── error.h
│   ├── eti.h
│   ├── etip.h
│   ├── execinfo.h
│   ├── expat_config.h
│   ├── expat_external.h
│   ├── expat.h
│   ├── fcntl.h
│   ├── features.h
│   ├── features-time64.h
│   ├── fenv.h
│   ├── fmtmsg.h
│   ├── fnmatch.h
│   ├── form.h
│   ├── fpu_control.h
│   ├── fstab.h
│   ├── fts.h
│   ├── ftw.h
│   ├── gconv.h
│   ├── gelf.h
│   ├── getopt.h
│   ├── glob.h
│   ├── gmp.h
│   ├── gmp-mparam.h
│   ├── gmp-mparam-x86_64.h
│   ├── gmp-x86_64.h
│   ├── gmpxx.h
│   ├── gnu
│   ├── gnumake.h
│   ├── gnu-versions.h
│   ├── grp.h
│   ├── gshadow.h
│   ├── gtest
│   ├── hwloc.h
│   ├── iconv.h
│   ├── isl
│   ├── ieee754.h
│   ├── ifaddrs.h
│   ├── inttypes.h
│   ├── jconfig.h
│   ├── jerror.h
│   ├── jmorecfg.h
│   ├── jpegint.h
│   ├── jpeglib.h
│   ├── langinfo.h
│   ├── lastlog.h
│   ├── libelf.h
│   ├── libgen.h
│   ├── libintl.h
│   ├── librsync_export.h
│   ├── librsync.h
│   ├── libsync.h
│   ├── limits.h
│   ├── link.h
│   ├── linux
│   ├── locale.h
│   ├── mad.h
│   ├── malloc.h
│   ├── math.h
│   ├── mcheck.h
│   ├── memory.h
│   ├── menu.h
│   ├── mntent.h
│   ├── monetary.h
│   ├── mpc.h
│   ├── mpf2mpfr.h
│   ├── mpfr.h
│   ├── mqueue.h
│   ├── ncurses_dll.h
│   ├── ncurses.h -> curses.h
│   ├── net
│   ├── netax
│   ├── netipx
│   ├── netrom
│   ├── netdb.h
│   ├── netinet
│   ├── nlist.h
│   ├── nl_types.h
│   ├── nss.h
│   ├── numacompat1.h
│   ├── numa.h
│   ├── numaif.h
│   ├── obstack.h
│   ├── panel.h
│   ├── paths.h
│   ├── pcap-bpf.h
│   ├── pcap.h
│   ├── pcap-namedb.h
│   ├── pciaccess.h
│   ├── pngconf.h -> libpng16/pngconf.h
│   ├── png.h -> libpng16/png.h
│   ├── pnglibconf.h -> libpng16/pnglibconf.h
│   ├── poll.h
│   ├── printf.h
│   ├── proc_service.h
│   ├── pthread.h
│   ├── pty.h
│   ├── pwd.h
│   ├── re_comp.h
│   ├── regex.h
│   ├── regexp.h
│   ├── resolv.h
│   ├── rpc
│   ├── ruby.h
│   ├── sched.h
│   ├── scsi
│   ├── search.h
│   ├── semaphore.h
│   ├── setjmp.h
│   ├── sgtty.h
│   ├── shadow.h
│   ├── signal.h
│   ├── spawn.h
│   ├── stab.h
│   ├── stdbit.h
│   ├── stdc-predef.h
│   ├── stdint.h
│   ├── stdio_ext.h
│   ├── stdio.h
│   ├── stdlib.h
│   ├── string.h
│   ├── strings.h
│   ├── sys
│   ├── syscall.h
│   ├── sysexits.h
│   ├── syslog.h
│   ├── tar.h
│   ├── termcap.h
│   ├── term_entry.h
│   ├── term.h
│   ├── termio.h
│   ├── termios.h
│   ├── tgmath.h
│   ├── thread_db.h
│   ├── threads.h
│   ├── time.h
│   ├── ttyent.h
│   ├── uchar.h
│   ├── ucontext.h
│   ├── ulimit.h
│   ├── unctrl.h
│   ├── unistd.h
│   ├── utime.h
│   ├── utmp.h
│   ├── utmpx.h
│   ├── values.h
│   ├── wait.h
│   ├── wchar.h
│   ├── wctype.h
│   ├── wordexp.h
│   ├── xf86drm.h
│   ├── xf86drmMode.h
│   ├── zconf.h
│   ├── zdict.h
│   ├── zipconf.h
│   ├── zip.h
│   ├── zlib.h
│   ├── zlib_name_mangling.h
│   ├── zstd_errors.h
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

This process collects both compiler dependencies and system dependencies under sysroot.
If we this example was for a riscv crosscompiler running on an x86_64 host, that means
our sysroot will have a mix of x86_64 and riscv sharable libraries

After iterating with `make` until we get a clean build we can install gcc to our sysroot directory with

```console
$ make install
```

### glibc

>Note: the steps below build glibc using the native host compiler, not the gcc version we just built.

```console

$ cd /home2/build_x86x/glibc
$ /home2/vendor/glibc/configure --prefix=/opt/x86_64x/sysroot --with-sysroot=/opt/x86_64x/sysroot --target=x86_64-pc-linux-gnu
$ make
$ make install
```

### glibc for riscv

```console 
 $ cd /home2/build/riscvx/glibc
 ../../vendor/glibc/configure riscv64-unknown-linux-gnu \
 CC=/opt/riscvx/sysroot/bin/riscv64-unknown-linux-gnu-gcc \
 LD=/opt/riscvx/sysroot/bin/riscv64-unknown-linux-gnu-ld \
 AR=/opt/riscvx/sysroot/bin/riscv64-unknown-linux-gnu-ar \
 --prefix=/opt/riscvx/sysroot \
 --with-headers=/opt/riscvx/sysroot/usr/include \
 --disable-multilib
 $ make
 $ make install
 ```

### cleanup

First look for any loader scripts which use absolute paths rather than relative paths.

```console
$ cd /opt/x86_64x
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
GROUP ( /opt/x86_64x/sysroot/lib/libc.so.6 /opt/x86_64x/sysroot/lib/libc_nonshared.a  AS_NEEDED ( /opt/x86_64x/sysroot/lib/ld-linux-x86-64.so.2 ) )
```

Edit these to use only relative paths.  For `libc.so`, this should be:

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

Binutils:

```console
$ /home2/vendor/binutils-gdb/configure --prefix=/opt/riscvx/sysroot --with-sysroot=/opt/riscvx/sysroot --target=riscv64-unknown-linux-gnu
```

gcc:

```console
$ ../../vendor/glibc/configure --prefix=/opt/riscvx/sysroot --target=riscv64-unknown-linux-gnu --with-headers=/opt/riscvx/sysroot/usr/include --disable-multilib
```

glibc:

```console
$ ../../vendor/glibc/configure riscv64-unknown-linux-gnu CC=/opt/riscvx/sysroot/bin/riscv64-unknown-linux-gnu-gcc LD=/opt/riscvx/sysroot/bin/riscv64-unknown-linux-gnu-ld AR=/opt/riscvx/sysroot/bin/riscv64-unknown-linux-gnu-ar --prefix=/opt/riscvx/sysroot --with-headers=/opt/riscvx/sysroot/usr/include --disable-multilib
```

### cleanup

Find any `*.so` loader script files using absolute paths, and convert them to relative paths as for the x86_example.

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
