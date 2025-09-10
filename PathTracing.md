# Path tracing and dependency analysis

Most serious errors are due to misunderstanding or misconfiguring the search paths for toolchain elements.
We want a hermetic build, with almost all components imported from the toolchain modules and only
kernel-dependent components loaded from the local workstation or server.

The compiler `gcc` must find the appropriate preprocessor (it may be internal to `gcc` itself), and the preprocessor must search through
include files in the proper order.  The compiler then has to find the appropriate assembler `as` and linker
`ld`, then the linker must find the appropriate linker scripts and kernel-provided infrastructure for
a successful build.

We also need to scrub the `sysroot` directory of files no longer needed for the toolchain, especially older
files added during bootstrapping that may conflict with the files installed during the `binutils`, `gcc`,
and `glibc` toolchain build.

Let's start with a 'simple' gcc compilation and linking of `helloworld.c` into `a.out`.

```console
$ strace -f -o /tmp/trace_native.log gcc examples/helloworld.c
$ grep -P 'openat|execve'  /tmp/trace_native.log
3342829 execve("/usr/bin/gcc", ["gcc", "helloworld.c"], 0x7ffd66868d50 /* 56 vars */) = 0
3342829 openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
3342829 openat(AT_FDCWD, "/lib64/libm.so.6", O_RDONLY|O_CLOEXEC) = 3
3342829 openat(AT_FDCWD, "/lib64/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3342829 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3342829 openat(AT_FDCWD, "/usr/share/locale/locale.alias", O_RDONLY|O_CLOEXEC) = 3
3342829 openat(AT_FDCWD, "/usr/share/locale/en_US.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342829 openat(AT_FDCWD, "/usr/share/locale/en_US.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342829 openat(AT_FDCWD, "/usr/share/locale/en_US/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342829 openat(AT_FDCWD, "/usr/share/locale/en.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342829 openat(AT_FDCWD, "/usr/share/locale/en.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342829 openat(AT_FDCWD, "/usr/share/locale/en/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342829 openat(AT_FDCWD, "/tmp/ccVYkTL0.s", O_RDWR|O_CREAT|O_EXCL, 0600) = 3
3342830 execve("/usr/libexec/gcc/x86_64-redhat-linux/15/cc1", ["/usr/libexec/gcc/x86_64-redhat-l"..., "-quiet", "helloworld.c", "-quiet", "-dumpdir", "a-", "-dumpbase", "helloworld.c", "-dumpbase-ext", ".c", "-mtune=generic", "-march=x86-64", "-o", "/tmp/ccVYkTL0.s"], 0x24b35c90 /* 61 vars */ <unfinished ...>
3342830 <... execve resumed>)           = 0
3342830 openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
3342830 openat(AT_FDCWD, "/lib64/libmpc.so.3", O_RDONLY|O_CLOEXEC) = 3
3342830 openat(AT_FDCWD, "/lib64/libmpfr.so.6", O_RDONLY|O_CLOEXEC) = 3
3342830 openat(AT_FDCWD, "/lib64/libgmp.so.10", O_RDONLY|O_CLOEXEC) = 3
3342830 openat(AT_FDCWD, "/lib64/libz.so.1", O_RDONLY|O_CLOEXEC) = 3
3342830 openat(AT_FDCWD, "/lib64/libzstd.so.1", O_RDONLY|O_CLOEXEC) = 3
3342830 openat(AT_FDCWD, "/lib64/libm.so.6", O_RDONLY|O_CLOEXEC) = 3
3342830 openat(AT_FDCWD, "/lib64/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3342830 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3342830 openat(AT_FDCWD, "/usr/share/locale/locale.alias", O_RDONLY|O_CLOEXEC) = 3
3342830 openat(AT_FDCWD, "/usr/share/locale/en_US.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/share/locale/en_US.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/share/locale/en_US/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/share/locale/en.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/share/locale/en.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/share/locale/en/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "helloworld.c", O_RDONLY|O_NOCTTY) = 3
3342830 openat(AT_FDCWD, "/tmp/ccVYkTL0.s", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 3
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/stdc-predef.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/stdc-predef.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/stdc-predef.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/stdio.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/stdio.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/stdio.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/libc-header-start.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/libc-header-start.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/libc-header-start.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/features.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/features.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/features.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/features-time64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/features-time64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/features-time64.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/timesize.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/timesize.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/timesize.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/sys/cdefs.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/sys/cdefs.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/sys/cdefs.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/long-double.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/long-double.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/long-double.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/gnu/stubs.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/gnu/stubs.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/gnu/stubs.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/gnu/stubs-64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/gnu/stubs-64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/gnu/stubs-64.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/stddef.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/stdarg.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/types.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/types.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/types.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/include/bits/timesize.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/typesizes.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/typesizes.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/typesizes.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/time64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/time64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/time64.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/types/__fpos_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/types/__fpos_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/types/__fpos_t.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/types/__mbstate_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/types/__mbstate_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/types/__mbstate_t.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/types/__fpos64_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/types/__fpos64_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/types/__fpos64_t.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/types/__FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/types/__FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/types/__FILE.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/types/FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/types/FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/types/FILE.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/types/struct_FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/types/struct_FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/types/struct_FILE.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/types/cookie_io_functions_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/types/cookie_io_functions_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/types/cookie_io_functions_t.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/stdio_lim.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/stdio_lim.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/stdio_lim.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/floatn.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/floatn.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/floatn.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/include/bits/floatn-common.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/local/include/bits/floatn-common.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3342830 openat(AT_FDCWD, "/usr/include/bits/floatn-common.h", O_RDONLY|O_NOCTTY) = 4
3342830 openat(AT_FDCWD, "/usr/include/bits/long-double.h", O_RDONLY|O_NOCTTY) = 4
3342829 openat(AT_FDCWD, "/tmp/ccLuHthu.o", O_RDWR|O_CREAT|O_EXCL, 0600) = 3
3342831 execve("/home/thixotropist/.local/bin/as", ["as", "--64", "-o", "/tmp/ccLuHthu.o", "/tmp/ccVYkTL0.s"], 0x24b35c90 /* 61 vars */) = -1 ENOENT (No such file or directory)
3342831 execve("/home/thixotropist/bin/as", ["as", "--64", "-o", "/tmp/ccLuHthu.o", "/tmp/ccVYkTL0.s"], 0x24b35c90 /* 61 vars */) = -1 ENOENT (No such file or directory)
3342831 execve("/usr/local/bin/as", ["as", "--64", "-o", "/tmp/ccLuHthu.o", "/tmp/ccVYkTL0.s"], 0x24b35c90 /* 61 vars */) = -1 ENOENT (No such file or directory)
3342831 execve("/usr/local/sbin/as", ["as", "--64", "-o", "/tmp/ccLuHthu.o", "/tmp/ccVYkTL0.s"], 0x24b35c90 /* 61 vars */) = -1 ENOENT (No such file or directory)
3342831 execve("/usr/bin/as", ["as", "--64", "-o", "/tmp/ccLuHthu.o", "/tmp/ccVYkTL0.s"], 0x24b35c90 /* 61 vars */ <unfinished ...>
3342831 <... execve resumed>)           = 0
3342831 openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
3342831 openat(AT_FDCWD, "/lib64/libbfd-2.44-6.fc42.so", O_RDONLY|O_CLOEXEC) = 3
3342831 openat(AT_FDCWD, "/lib64/libz.so.1", O_RDONLY|O_CLOEXEC) = 3
3342831 openat(AT_FDCWD, "/lib64/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3342831 openat(AT_FDCWD, "/lib64/libsframe.so.1", O_RDONLY|O_CLOEXEC) = 3
3342831 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3342831 openat(AT_FDCWD, "/tmp/ccLuHthu.o", O_RDWR|O_CREAT|O_TRUNC, 0666) = 3
3342831 openat(AT_FDCWD, "/tmp/ccVYkTL0.s", O_RDONLY) = 4
3342831 openat(AT_FDCWD, "/usr/share/locale/locale.alias", O_RDONLY|O_CLOEXEC) = 4
3342831 openat(AT_FDCWD, "/usr/share/locale/en_US.UTF-8/LC_MESSAGES/gas.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342831 openat(AT_FDCWD, "/usr/share/locale/en_US.utf8/LC_MESSAGES/gas.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342831 openat(AT_FDCWD, "/usr/share/locale/en_US/LC_MESSAGES/gas.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342831 openat(AT_FDCWD, "/usr/share/locale/en.UTF-8/LC_MESSAGES/gas.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342831 openat(AT_FDCWD, "/usr/share/locale/en.utf8/LC_MESSAGES/gas.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342831 openat(AT_FDCWD, "/usr/share/locale/en/LC_MESSAGES/gas.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342829 openat(AT_FDCWD, "/tmp/ccuBJW03.res", O_RDWR|O_CREAT|O_EXCL, 0600) = 3
3342832 execve("/usr/libexec/gcc/x86_64-redhat-linux/15/collect2", ["/usr/libexec/gcc/x86_64-redhat-l"..., "-plugin", "/usr/libexec/gcc/x86_64-redhat-l"..., "-plugin-opt=/usr/libexec/gcc/x86"..., "-plugin-opt=-fresolution=/tmp/cc"..., "-plugin-opt=-pass-through=-lgcc", "-plugin-opt=-pass-through=-lgcc_"..., "-plugin-opt=-pass-through=-lc", "-plugin-opt=-pass-through=-lgcc", "-plugin-opt=-pass-through=-lgcc_"..., "--build-id", "--no-add-needed", "--eh-frame-hdr", "--hash-style=gnu", "-m", "elf_x86_64", "-dynamic-linker", "/lib64/ld-linux-x86-64.so.2", "/usr/lib/gcc/x86_64-redhat-linux"..., "/usr/lib/gcc/x86_64-redhat-linux"..., "/usr/lib/gcc/x86_64-redhat-linux"..., "-L/usr/lib/gcc/x86_64-redhat-lin"..., "-L/usr/lib/gcc/x86_64-redhat-lin"..., "-L/lib/../lib64", "-L/usr/lib/../lib64", "-L/usr/lib/gcc/x86_64-redhat-lin"..., "-L/lib", "-L/usr/lib", "/tmp/ccLuHthu.o", "-lgcc", "--push-state", "--as-needed", ...], 0x24b35c90 /* 63 vars */ <unfinished ...>
3342832 <... execve resumed>)           = 0
3342832 openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
3342832 openat(AT_FDCWD, "/lib64/libm.so.6", O_RDONLY|O_CLOEXEC) = 3
3342832 openat(AT_FDCWD, "/lib64/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3342832 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3342832 openat(AT_FDCWD, "/usr/share/locale/locale.alias", O_RDONLY|O_CLOEXEC) = 3
3342832 openat(AT_FDCWD, "/usr/share/locale/en_US.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342832 openat(AT_FDCWD, "/usr/share/locale/en_US.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342832 openat(AT_FDCWD, "/usr/share/locale/en_US/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342832 openat(AT_FDCWD, "/usr/share/locale/en.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342832 openat(AT_FDCWD, "/usr/share/locale/en.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342832 openat(AT_FDCWD, "/usr/share/locale/en/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342832 openat(AT_FDCWD, "/tmp/ccdYX5ay.cdtor.c", O_RDWR|O_CREAT|O_EXCL, 0600) = 3
3342832 openat(AT_FDCWD, "/tmp/cc3B0WN1.cdtor.o", O_RDWR|O_CREAT|O_EXCL, 0600) = 3
3342833 execve("/usr/bin/ld", ["/usr/bin/ld", "-plugin", "/usr/libexec/gcc/x86_64-redhat-l"..., "-plugin-opt=/usr/libexec/gcc/x86"..., "-plugin-opt=-fresolution=/tmp/cc"..., "-plugin-opt=-pass-through=-lgcc", "-plugin-opt=-pass-through=-lgcc_"..., "-plugin-opt=-pass-through=-lc", "-plugin-opt=-pass-through=-lgcc", "-plugin-opt=-pass-through=-lgcc_"..., "--build-id", "--no-add-needed", "--eh-frame-hdr", "--hash-style=gnu", "-m", "elf_x86_64", "-dynamic-linker", "/lib64/ld-linux-x86-64.so.2", "/usr/lib/gcc/x86_64-redhat-linux"..., "/usr/lib/gcc/x86_64-redhat-linux"..., "/usr/lib/gcc/x86_64-redhat-linux"..., "-L/usr/lib/gcc/x86_64-redhat-lin"..., "-L/usr/lib/gcc/x86_64-redhat-lin"..., "-L/lib/../lib64", "-L/usr/lib/../lib64", "-L/usr/lib/gcc/x86_64-redhat-lin"..., "-L/lib", "-L/usr/lib", "/tmp/ccLuHthu.o", "-lgcc", "--push-state", "--as-needed", ...], 0x7ffc91e83760 /* 63 vars */ <unfinished ...>
3342833 <... execve resumed>)           = 0
3342833 openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
3342833 openat(AT_FDCWD, "/lib64/libbfd-2.44-6.fc42.so", O_RDONLY|O_CLOEXEC) = 3
3342833 openat(AT_FDCWD, "/lib64/libctf.so.0", O_RDONLY|O_CLOEXEC) = 3
3342833 openat(AT_FDCWD, "/lib64/libjansson.so.4", O_RDONLY|O_CLOEXEC) = 3
3342833 openat(AT_FDCWD, "/lib64/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3342833 openat(AT_FDCWD, "/lib64/libz.so.1", O_RDONLY|O_CLOEXEC) = 3
3342833 openat(AT_FDCWD, "/lib64/libsframe.so.1", O_RDONLY|O_CLOEXEC) = 3
3342833 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3342833 openat(AT_FDCWD, "/usr/lib64/gconv/gconv-modules.cache", O_RDONLY|O_CLOEXEC) = 3
3342833 openat(AT_FDCWD, "/usr/libexec/gcc/x86_64-redhat-linux/15/liblto_plugin.so", O_RDONLY|O_CLOEXEC) = 3
3342833 openat(AT_FDCWD, "/usr/share/locale/locale.alias", O_RDONLY|O_CLOEXEC) = 3
3342833 openat(AT_FDCWD, "/usr/share/locale/en_US.UTF-8/LC_MESSAGES/ld.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/share/locale/en_US.utf8/LC_MESSAGES/ld.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/share/locale/en_US/LC_MESSAGES/ld.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/share/locale/en.UTF-8/LC_MESSAGES/ld.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/share/locale/en.utf8/LC_MESSAGES/ld.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/share/locale/en/LC_MESSAGES/ld.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "a.out", O_RDWR|O_CREAT|O_TRUNC, 0666) = 3
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/crt1.o", O_RDONLY) = 4
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/crt1.o", O_RDONLY) = 5
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/crti.o", O_RDONLY) = 5
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/crti.o", O_RDONLY) = 6
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/crtbegin.o", O_RDONLY) = 6
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/crtbegin.o", O_RDONLY) = 7
3342833 openat(AT_FDCWD, "/tmp/ccLuHthu.o", O_RDONLY) = 7
3342833 openat(AT_FDCWD, "/tmp/ccLuHthu.o", O_RDONLY) = 8
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc.a", O_RDONLY) = 8
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc_s.so", O_RDONLY) = 9
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc_s.so", O_RDONLY) = 10
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc_s.so", O_RDONLY) = 10
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc_s.so", O_RDONLY) = 9
3342833 openat(AT_FDCWD, "/lib64/libgcc_s.so.1", O_RDONLY) = 9
3342833 openat(AT_FDCWD, "/lib64/libgcc_s.so.1", O_RDONLY) = 10
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc.a", O_RDONLY) = 10
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libc.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libc.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/libc.so", O_RDONLY) = 11
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/libc.so", O_RDONLY) = 12
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/libc.so", O_RDONLY) = 12
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/libc.so", O_RDONLY) = 11
3342833 openat(AT_FDCWD, "/lib64/libc.so.6", O_RDONLY) = 11
3342833 openat(AT_FDCWD, "/lib64/libc.so.6", O_RDONLY) = 12
3342833 openat(AT_FDCWD, "/usr/lib64/libc_nonshared.a", O_RDONLY) = 12
3342833 openat(AT_FDCWD, "/lib64/ld-linux-x86-64.so.2", O_RDONLY) = 13
3342833 openat(AT_FDCWD, "/lib64/ld-linux-x86-64.so.2", O_RDONLY) = 14
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc.a", O_RDONLY) = 14
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc_s.so", O_RDONLY) = 15
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc_s.so", O_RDONLY) = 16
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc_s.so", O_RDONLY) = 16
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc_s.so", O_RDONLY) = 15
3342833 openat(AT_FDCWD, "/lib64/libgcc_s.so.1", O_RDONLY) = 15
3342833 openat(AT_FDCWD, "/lib64/libgcc_s.so.1", O_RDONLY) = 16
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/libgcc.a", O_RDONLY) = 16
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/crtend.o", O_RDONLY) = 17
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/crtend.o", O_RDONLY) = 18
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/crtn.o", O_RDONLY) = 18
3342833 openat(AT_FDCWD, "/usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/crtn.o", O_RDONLY) = 19
3342833 openat(AT_FDCWD, "/usr/share/locale/en_US.UTF-8/LC_MESSAGES/bfd.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/share/locale/en_US.utf8/LC_MESSAGES/bfd.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/share/locale/en_US/LC_MESSAGES/bfd.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/share/locale/en.UTF-8/LC_MESSAGES/bfd.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/share/locale/en.utf8/LC_MESSAGES/bfd.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/usr/share/locale/en/LC_MESSAGES/bfd.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3342833 openat(AT_FDCWD, "/lib64/ld-linux-x86-64.so.2", O_RDONLY) = 19
```

Unpack this to see:

* five processes are invoked using `execve`. No `cpp` is invoked, as the preprocessor
  stage is apparently performed internal to the C compiler.
    * `/usr/bin/gcc` as the primary process
    * `/usr/libexec/gcc/x86_64-redhat-linux/15/cc1` as the compiler workhorse
    * `/usr/bin/as` as the assembler
    * `/usr/libexec/gcc/x86_64-redhat-linux/15/collect2` to collect objects
    * `/usr/bin/ld` to link and prepare an executable
* The search path for `<stdio.h>` is:
    * `/usr/lib/gcc/x86_64-redhat-linux/15/include/stdio.h` - not found
    * `/usr/local/include/stdio.h` - not found
    * `/usr/include/stdio.h` - found and processed
* Additional header files opened are:
	* /usr/include/stdc-predef.h
	* /usr/include/stdio.h
	* /usr/include/bits/libc-header-start.h
	* /usr/include/features.h
	* /usr/include/features-time64.h
	* /usr/include/bits/wordsize.h
	* /usr/include/bits/timesize.h
	* /usr/include/sys/cdefs.h
	* /usr/include/bits/wordsize.h
	* /usr/include/bits/long-double.h
	* /usr/include/gnu/stubs.h
	* /usr/include/gnu/stubs-64.h
	* /usr/lib/gcc/x86_64-redhat-linux/15/include/stddef.h
	* /usr/lib/gcc/x86_64-redhat-linux/15/include/stdarg.h
	* /usr/include/bits/types.h
	* /usr/include/bits/typesizes.h
	* /usr/include/bits/time64.h
	* /usr/include/bits/types/__fpos_t.h
	* /usr/include/bits/types/__mbstate_t.h
	* /usr/include/bits/types/__fpos64_t.h
	* /usr/include/bits/types/__FILE.h
	* /usr/include/bits/types/FILE.h
	* /usr/include/bits/types/struct_FILE.h
	* /usr/include/bits/types/cookie_io_functions_t.h
	* /usr/include/bits/stdio_lim.h
	* /usr/include/bits/floatn.h
	* /usr/include/bits/floatn-common.h
	* /usr/include/bits/long-double.h
* No include files are taken from `/include` - this may be a deprecated location.
* The `liblto_plugin.so` is located even thogh no Link Time Optimization is requested
* The linker `ld` uses multiple object files, including:
    * /usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/crt1.o
    * /usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/crti.o
    * /usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/crtn.o
    * /usr/lib/gcc/x86_64-redhat-linux/15/crtbegin.o
    * /usr/lib/gcc/x86_64-redhat-linux/15/crtend.o
    * /usr/lib/gcc/x86_64-redhat-linux/15/libgcc.so
    * /usr/lib/gcc/x86_64-redhat-linux/15/libgcc.a
    * /usr/lib/gcc/x86_64-redhat-linux/15/libgcc_s.so
    * /lib64/libgcc_s.so.1
    * /usr/lib/gcc/x86_64-redhat-linux/15/../../../../lib64/libc.so
    * /lib64/libc.so.6
    * /usr/lib64/libc_nonshared.a
    * /lib64/ld-linux-x86-64.so.2

Repeat this with the C++ example `helloworld.cc`, noting that there are many more files examined

## Compare paths when using the Bazel toolchain

>Note: The build target was changed arbitrarily from `x86_64-redhat-linux` to `x86_64-pc-linux-gnu` during construction of the Bazel
>      toolchain.


The Bazel build process separates the compilation and the linking phases.  We need to extract the commands for both steps, then
rerun them under `strace` control.  We will run the build twice, once with the 'native' gcc and once with our imported toolchain.

The native build includes no reference to a specific platform

```console
$ bazel build -s --sandbox_debug helloworld
...
SUBCOMMAND: # //:helloworld [action 'Compiling helloworld.c', configuration: e8494724f8baac23aca058d3505bda14b53b5306128c401b729b89c7aeb7b13c, execution platform: @@platforms//host:host, mnemonic: CppCompile]
(cd /run/user/1000/bazel/execroot/_main && \
  exec env - \
    PATH=/home/thixotropist/.local/bin:/home/thixotropist/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/var/lib/snapd/snap/bin:/opt/ghidra_12.0_DEV/:/opt/jdk-22.0.1/bin:/opt/gradle-8.8/bin \
    PWD=/proc/self/cwd \
  /usr/bin/gcc -U_FORTIFY_SOURCE -fstack-protector -Wall -Wunused-but-set-parameter -Wno-free-nonheap-object -fno-omit-frame-pointer -MD -MF bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.d '-frandom-seed=bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.o' -fPIC -iquote . -iquote bazel-out/k8-fastbuild/bin -iquote external/bazel_tools -iquote bazel-out/k8-fastbuild/bin/external/bazel_tools -c helloworld.c -o bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.o -fno-canonical-system-headers -Wno-builtin-macro-redefined '-D__DATE__="redacted"' '-D__TIMESTAMP__="redacted"' '-D__TIME__="redacted"')
...
SUBCOMMAND: # //:helloworld [action 'Linking helloworld', configuration: e8494724f8baac23aca058d3505bda14b53b5306128c401b729b89c7aeb7b13c, execution platform: @@platforms//host:host, mnemonic: CppLink]
(cd /run/user/1000/bazel/execroot/_main && \
  exec env - \
    PATH=/home/thixotropist/.local/bin:/home/thixotropist/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/var/lib/snapd/snap/bin:/opt/ghidra_12.0_DEV/:/opt/jdk-22.0.1/bin:/opt/gradle-8.8/bin \
    PWD=/proc/self/cwd \
    ZERO_AR_DATE=1 \
  /usr/bin/gcc @bazel-out/k8-fastbuild/bin/helloworld-0.params)
```

Repeat with an explicit platform reference:

```console
$ bazel build -s --sandbox_debug --platforms=//platforms:x86_64 helloworld
WARNING: Build option --platforms has changed, discarding analysis cache (this can be expensive, see https://bazel.build/advanced/performance/iteration-speed).
INFO: Analyzed target //:helloworld (3 packages loaded, 5803 targets configured).
SUBCOMMAND: # //:helloworld [action 'Compiling helloworld.c', configuration: 18005088ebc3c2bce561736e29f2eb165b16ec1f9b674d24ecb15def1fcfd2bc, execution platform: @@platforms//host:host, mnemonic: CppCompile]
(cd /run/user/1000/bazel/execroot/_main && \
  exec env - \
    PATH=/home/thixotropist/.local/bin:/home/thixotropist/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/var/lib/snapd/snap/bin:/opt/ghidra_12.0_DEV/:/opt/jdk-22.0.1/bin:/opt/gradle-8.8/bin \
    PWD=/proc/self/cwd \
  toolchains/x86/gcc/wrappers/gcc -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15 -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include '-march=native' -no-canonical-prefixes -fno-canonical-system-headers -Wno-builtin-macro-redefined '-D__DATE__="redacted"' '-D__TIMESTAMP__="redacted"' '-D__TIME__="redacted"' -fstack-protector -Wall -Wunused-but-set-parameter -Wno-free-nonheap-object -fno-omit-frame-pointer -MD -MF bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.d '-frandom-seed=bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.o' -fPIC -iquote . -iquote bazel-out/k8-fastbuild/bin -iquote external/bazel_tools -iquote bazel-out/k8-fastbuild/bin/external/bazel_tools -c helloworld.c -o bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.o)
...
1757601466.220838299: src/main/tools/linux-sandbox-pid1.cc:308: working dir: /run/user/1000/bazel/sandbox/linux-sandbox/11/execroot/_main
...
SUBCOMMAND: # //:helloworld [action 'Linking helloworld', configuration: 18005088ebc3c2bce561736e29f2eb165b16ec1f9b674d24ecb15def1fcfd2bc, execution platform: @@platforms//host:host, mnemonic: CppLink]
(cd /run/user/1000/bazel/execroot/_main && \
  exec env - \
    PATH=/home/thixotropist/.local/bin:/home/thixotropist/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/var/lib/snapd/snap/bin:/opt/ghidra_12.0_DEV/:/opt/jdk-22.0.1/bin:/opt/gradle-8.8/bin \
    PWD=/proc/self/cwd \
  toolchains/x86/gcc/wrappers/gcc -o bazel-out/k8-fastbuild/bin/helloworld bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.o -Wl,-S -Wl,-Ttoolchains/x86/gcc/elf_x86_64.xce -Wl,-lstdc++ -Wl,-lm -Wl,-z,relro,-z,now -no-canonical-prefixes -pass-exit-codes)
...
1757601466.317686282: src/main/tools/linux-sandbox-pid1.cc:308: working dir: /run/user/1000/bazel/sandbox/linux-sandbox/12/execroot/_main
```

The bazel command options preserve the sandboxes used for both subcommands.  We need to cd into each sandbox, then extract and run the gcc invocations for each

The compilation subcommand executes in the sandbox /run/user/1000/bazel/sandbox/linux-sandbox/11/execroot/_main:

```console
$ cd /run/user/1000/bazel/sandbox/linux-sandbox/11/execroot/_main
$ strace -f -o /tmp/bazel_c.log toolchains/x86/gcc/wrappers/gcc -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15 -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include '-march=native' -no-canonical-prefixes -fno-canonical-system-headers -Wno-builtin-macro-redefined '-D__DATE__="redacted"' '-D__TIMESTAMP__="redacted"' '-D__TIME__="redacted"' -fstack-protector -Wall -Wunused-but-set-parameter -Wno-free-nonheap-object -fno-omit-frame-pointer -MD -MF bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.d '-frandom-seed=bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.o' -fPIC -iquote . -iquote bazel-out/k8-fastbuild/bin -iquote external/bazel_tools -iquote bazel-out/k8-fastbuild/bin/external/bazel_tools -c helloworld.c -o bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.o
$ grep -P 'openat|execve'  /tmp/bazel_c.log
3500510 execve("toolchains/x86/gcc/wrappers/gcc", ["toolchains/x86/gcc/wrappers/gcc", "-isystem/run/user/1000/bazel/ext"..., "-isystem/run/user/1000/bazel/ext"..., "-isystem/run/user/1000/bazel/ext"..., "-isystem/run/user/1000/bazel/ext"..., "-isystem/run/user/1000/bazel/ext"..., "-march=native", "-no-canonical-prefixes", "-fno-canonical-system-headers", "-Wno-builtin-macro-redefined", "-D__DATE__=\"redacted\"", "-D__TIMESTAMP__=\"redacted\"", "-D__TIME__=\"redacted\"", "-fstack-protector", "-Wall", "-Wunused-but-set-parameter", "-Wno-free-nonheap-object", "-fno-omit-frame-pointer", "-MD", "-MF", "bazel-out/k8-fastbuild/bin/_objs"..., "-frandom-seed=bazel-out/k8-fastb"..., "-fPIC", "-iquote", ".", "-iquote", "bazel-out/k8-fastbuild/bin", "-iquote", "external/bazel_tools", "-iquote", "bazel-out/k8-fastbuild/bin/exter"..., "-c", ...], 0x7ffd278dcef8 /* 56 vars */) = 0
3500510 openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
3500510 openat(AT_FDCWD, "/lib64/libtinfo.so.6", O_RDONLY|O_CLOEXEC) = 3
3500510 openat(AT_FDCWD, "/lib64/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3500510 openat(AT_FDCWD, "/dev/tty", O_RDWR|O_NONBLOCK) = 3
3500510 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3500510 openat(AT_FDCWD, "/usr/lib64/gconv/gconv-modules.cache", O_RDONLY|O_CLOEXEC) = 3
3500510 openat(AT_FDCWD, "toolchains/x86/gcc/wrappers/gcc", O_RDONLY) = 3
3500511 execve("external/gcc_x86_64_suite+/bin/gcc", ["external/gcc_x86_64_suite+/bin/g"..., "-isystem/run/user/1000/bazel/ext"..., "-isystem/run/user/1000/bazel/ext"..., "-isystem/run/user/1000/bazel/ext"..., "-isystem/run/user/1000/bazel/ext"..., "-isystem/run/user/1000/bazel/ext"..., "-march=native", "-no-canonical-prefixes", "-fno-canonical-system-headers", "-Wno-builtin-macro-redefined", "-D__DATE__=\"redacted\"", "-D__TIMESTAMP__=\"redacted\"", "-D__TIME__=\"redacted\"", "-fstack-protector", "-Wall", "-Wunused-but-set-parameter", "-Wno-free-nonheap-object", "-fno-omit-frame-pointer", "-MD", "-MF", "bazel-out/k8-fastbuild/bin/_objs"..., "-frandom-seed=bazel-out/k8-fastb"..., "-fPIC", "-iquote", ".", "-iquote", "bazel-out/k8-fastbuild/bin", "-iquote", "external/bazel_tools", "-iquote", "bazel-out/k8-fastbuild/bin/exter"..., "-c", ...], 0x55cd1b3eb140 /* 57 vars */) = 0
3500511 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libm.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500511 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libm.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500511 openat(AT_FDCWD, "external/fedora_syslibs+/libm.so.6", O_RDONLY|O_CLOEXEC) = 3
3500511 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libc.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500511 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libc.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500511 openat(AT_FDCWD, "external/fedora_syslibs+/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3500511 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3500511 openat(AT_FDCWD, "/usr/share/locale/locale.alias", O_RDONLY|O_CLOEXEC) = 3
3500511 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500511 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500511 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500511 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500511 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500511 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500511 openat(AT_FDCWD, "/tmp/cc6kPoST.s", O_RDWR|O_CREAT|O_EXCL, 0600) = 3
3500512 execve("external/gcc_x86_64_suite+/bin/../libexec/gcc/x86_64-pc-linux-gnu/15.2.0/cc1", ["external/gcc_x86_64_suite+/bin/."..., "-quiet", "-iprefix", "external/gcc_x86_64_suite+/bin/."..., "-MD", "bazel-out/k8-fastbuild/bin/_objs"..., "-MF", "bazel-out/k8-fastbuild/bin/_objs"..., "-MQ", "bazel-out/k8-fastbuild/bin/_objs"..., "-D", "__DATE__=\"redacted\"", "-D", "__TIMESTAMP__=\"redacted\"", "-D", "__TIME__=\"redacted\"", "-isystem", "/run/user/1000/bazel/external/gc"..., "-isystem", "/run/user/1000/bazel/external/gc"..., "-isystem", "/run/user/1000/bazel/external/gc"..., "-isystem", "/run/user/1000/bazel/external/gc"..., "-isystem", "/run/user/1000/bazel/external/gc"..., "-iquote", ".", "-iquote", "bazel-out/k8-fastbuild/bin", "-iquote", "external/bazel_tools", ...], 0x3bb41cf0 /* 60 vars */ <unfinished ...>
3500512 <... execve resumed>)           = 0
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libisl.so.15", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libisl.so.15", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/libisl.so.15", O_RDONLY|O_CLOEXEC) = 3
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libmpc.so.3", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libmpc.so.3", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/libmpc.so.3", O_RDONLY|O_CLOEXEC) = 3
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libmpfr.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libmpfr.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/libmpfr.so.6", O_RDONLY|O_CLOEXEC) = 3
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libgmp.so.10", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libgmp.so.10", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/libgmp.so.10", O_RDONLY|O_CLOEXEC) = 3
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libm.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libm.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/libm.so.6", O_RDONLY|O_CLOEXEC) = 3
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libc.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libc.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "external/fedora_syslibs+/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3500512 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3500512 openat(AT_FDCWD, "/usr/share/locale/locale.alias", O_RDONLY|O_CLOEXEC) = 3
3500512 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "helloworld.c", O_RDONLY|O_NOCTTY) = 3
3500512 openat(AT_FDCWD, "/tmp/cc6kPoST.s", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 3
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/stdc-predef.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/stdc-predef.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/stdc-predef.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/stdc-predef.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/stdc-predef.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/stdio.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/stdio.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/stdio.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/stdio.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/stdio.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/libc-header-start.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/libc-header-start.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/libc-header-start.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/libc-header-start.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/libc-header-start.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/features.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/features.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/features.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/features.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/features.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/features-time64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/features-time64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/features-time64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/features-time64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/features-time64.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/wordsize.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/wordsize.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/wordsize.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/timesize.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/timesize.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/timesize.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/timesize.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/timesize.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/sys/cdefs.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/sys/cdefs.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/sys/cdefs.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/sys/cdefs.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/sys/cdefs.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/long-double.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/long-double.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/long-double.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/long-double.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/long-double.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/gnu/stubs.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/gnu/stubs.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/gnu/stubs.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/gnu/stubs.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/gnu/stubs.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/gnu/stubs-64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/gnu/stubs-64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/gnu/stubs-64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/gnu/stubs-64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/gnu/stubs-64.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/stddef.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/stddef.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/stdarg.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/stdarg.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/types.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/types.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/types.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/types.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/types.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/timesize.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/wordsize.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/typesizes.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/typesizes.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/typesizes.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/typesizes.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/typesizes.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/time64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/time64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/time64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/time64.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/time64.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/types/__fpos_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/types/__fpos_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/types/__fpos_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/types/__fpos_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/types/__fpos_t.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/types/__mbstate_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/types/__mbstate_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/types/__mbstate_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/types/__mbstate_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/types/__mbstate_t.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/types/__fpos64_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/types/__fpos64_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/types/__fpos64_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/types/__fpos64_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/types/__fpos64_t.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/types/__FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/types/__FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/types/__FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/types/__FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/types/__FILE.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/types/FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/types/FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/types/FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/types/FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/types/FILE.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/types/struct_FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/types/struct_FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/types/struct_FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/types/struct_FILE.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/types/struct_FILE.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/types/cookie_io_functions_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/types/cookie_io_functions_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/types/cookie_io_functions_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/types/cookie_io_functions_t.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/types/cookie_io_functions_t.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/stdio_lim.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/stdio_lim.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/stdio_lim.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/stdio_lim.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/stdio_lim.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/floatn.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/floatn.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/floatn.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/floatn.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/floatn.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed/bits/floatn-common.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include/bits/floatn-common.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu/bits/floatn-common.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/bits/floatn-common.h", O_RDONLY|O_NOCTTY) = -1 ENOENT (No such file or directory)
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/floatn-common.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/bits/long-double.h", O_RDONLY|O_NOCTTY) = 4
3500512 openat(AT_FDCWD, "bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.d", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 3
3500513 execve("external/gcc_x86_64_suite+/bin/as", ["as", "--64", "-o", "bazel-out/k8-fastbuild/bin/_objs"..., "/tmp/cc6kPoST.s"], 0x3bb41cf0 /* 60 vars */ <unfinished ...>
3500513 <... execve resumed>)           = 0
3500513 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libzstd.so.1", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500513 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libzstd.so.1", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500513 openat(AT_FDCWD, "external/fedora_syslibs+/libzstd.so.1", O_RDONLY|O_CLOEXEC) = 3
3500513 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libc.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500513 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libc.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3500513 openat(AT_FDCWD, "external/fedora_syslibs+/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3500513 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3500513 openat(AT_FDCWD, "bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.o", O_RDWR|O_CREAT|O_TRUNC, 0666) = 3
3500513 openat(AT_FDCWD, "/tmp/cc6kPoST.s", O_RDONLY) = 4
3500513 openat(AT_FDCWD, "/usr/share/locale/locale.alias", O_RDONLY|O_CLOEXEC) = 4
3500513 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US.UTF-8/LC_MESSAGES/gas.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500513 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US.utf8/LC_MESSAGES/gas.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500513 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US/LC_MESSAGES/gas.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500513 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en.UTF-8/LC_MESSAGES/gas.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500513 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en.utf8/LC_MESSAGES/gas.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3500513 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en/LC_MESSAGES/gas.mo", O_RDONLY) = -1 ENOENT (No such file or directory) 
```
That looks fairly reasonable, with the possible exception of the `locale` message subsystem resources.

What about the linker subcommand?

```console
$ cd /run/user/1000/bazel/sandbox/linux-sandbox/12/execroot/_main
$ strace -f -o /tmp/bazel_c_link.log toolchains/x86/gcc/wrappers/gcc -o bazel-out/k8-fastbuild/bin/helloworld bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.o -Wl,-S -Wl,-Ttoolchains/x86/gcc/elf_x86_64.xce -Wl,-lstdc++ -Wl,-lm -Wl,-z,relro,-z,now -no-canonical-prefixes -pass-exit-codes
$  grep -P 'openat|execve'  /tmp/bazel_c_link.log
3502384 execve("toolchains/x86/gcc/wrappers/gcc", ["toolchains/x86/gcc/wrappers/gcc", "-o", "bazel-out/k8-fastbuild/bin/hello"..., "bazel-out/k8-fastbuild/bin/_objs"..., "-Wl,-S", "-Wl,-Ttoolchains/x86/gcc/elf_x86"..., "-Wl,-lstdc++", "-Wl,-lm", "-Wl,-z,relro,-z,now", "-no-canonical-prefixes", "-pass-exit-codes"], 0x7ffd274517c8 /* 56 vars */) = 0
3502384 openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
3502384 openat(AT_FDCWD, "/lib64/libtinfo.so.6", O_RDONLY|O_CLOEXEC) = 3
3502384 openat(AT_FDCWD, "/lib64/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3502384 openat(AT_FDCWD, "/dev/tty", O_RDWR|O_NONBLOCK) = 3
3502384 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3502384 openat(AT_FDCWD, "/usr/lib64/gconv/gconv-modules.cache", O_RDONLY|O_CLOEXEC) = 3
3502384 openat(AT_FDCWD, "toolchains/x86/gcc/wrappers/gcc", O_RDONLY) = 3
3502385 execve("external/gcc_x86_64_suite+/bin/gcc", ["external/gcc_x86_64_suite+/bin/g"..., "-o", "bazel-out/k8-fastbuild/bin/hello"..., "bazel-out/k8-fastbuild/bin/_objs"..., "-Wl,-S", "-Wl,-Ttoolchains/x86/gcc/elf_x86"..., "-Wl,-lstdc++", "-Wl,-lm", "-Wl,-z,relro,-z,now", "-no-canonical-prefixes", "-pass-exit-codes"], 0x560b0fc8e170 /* 57 vars */) = 0
3502385 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libm.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3502385 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libm.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3502385 openat(AT_FDCWD, "external/fedora_syslibs+/libm.so.6", O_RDONLY|O_CLOEXEC) = 3
3502385 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libc.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3502385 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libc.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3502385 openat(AT_FDCWD, "external/fedora_syslibs+/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3502385 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3502385 openat(AT_FDCWD, "/usr/share/locale/locale.alias", O_RDONLY|O_CLOEXEC) = 3
3502385 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502385 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502385 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502385 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502385 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502385 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502385 openat(AT_FDCWD, "/tmp/ccfIgQiH.res", O_RDWR|O_CREAT|O_EXCL, 0600) = 3
3502386 execve("external/gcc_x86_64_suite+/bin/../libexec/gcc/x86_64-pc-linux-gnu/15.2.0/collect2", ["external/gcc_x86_64_suite+/bin/."..., "-plugin", "external/gcc_x86_64_suite+/bin/."..., "-plugin-opt=", "-plugin-opt=-fresolution=/tmp/cc"..., "-plugin-opt=-pass-through=-lgcc", "-plugin-opt=-pass-through=-lgcc_"..., "-plugin-opt=-pass-through=-lc", "-plugin-opt=-pass-through=-lgcc", "-plugin-opt=-pass-through=-lgcc_"..., "--sysroot=/opt/x86_64/sysroot", "--eh-frame-hdr", "-m", "elf_x86_64", "-dynamic-linker", "/lib64/ld-linux-x86-64.so.2", "-o", "bazel-out/k8-fastbuild/bin/hello"..., "/opt/x86_64/sysroot/usr/lib/../l"..., "/opt/x86_64/sysroot/usr/lib/../l"..., "external/gcc_x86_64_suite+/bin/."..., "-Lexternal/gcc_x86_64_suite+/bin"..., "-Lexternal/gcc_x86_64_suite+/bin"..., "-Lexternal/gcc_x86_64_suite+/bin"..., "-L/opt/x86_64/sysroot/lib/../lib"..., "-L/opt/x86_64/sysroot/usr/lib/.."..., "-Lexternal/gcc_x86_64_suite+/bin"..., "-L/opt/x86_64/sysroot/lib", "-L/opt/x86_64/sysroot/usr/lib", "bazel-out/k8-fastbuild/bin/_objs"..., "-S", "-Ttoolchains/x86/gcc/elf_x86_64."..., ...], 0x38fce5d0 /* 62 vars */ <unfinished ...>
3502386 <... execve resumed>)           = 0
3502386 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libm.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3502386 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libm.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3502386 openat(AT_FDCWD, "external/fedora_syslibs+/libm.so.6", O_RDONLY|O_CLOEXEC) = 3
3502386 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libc.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3502386 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libc.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3502386 openat(AT_FDCWD, "external/fedora_syslibs+/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3502386 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3502386 openat(AT_FDCWD, "/usr/share/locale/locale.alias", O_RDONLY|O_CLOEXEC) = 3
3502386 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502386 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502386 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en_US/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502386 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en.UTF-8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502386 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en.utf8/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502386 openat(AT_FDCWD, "/opt/x86_64/sysroot/share/locale/en/LC_MESSAGES/gcc.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502386 openat(AT_FDCWD, "/tmp/cc8fuUsd.cdtor.c", O_RDWR|O_CREAT|O_EXCL, 0600) = 3
3502386 openat(AT_FDCWD, "/tmp/ccFpMcRy.cdtor.o", O_RDWR|O_CREAT|O_EXCL, 0600) = 3
3502387 execve("external/gcc_x86_64_suite+/bin/ld", ["external/gcc_x86_64_suite+/bin/l"..., "-plugin", "external/gcc_x86_64_suite+/bin/."..., "-plugin-opt=", "-plugin-opt=-fresolution=/tmp/cc"..., "-plugin-opt=-pass-through=-lgcc", "-plugin-opt=-pass-through=-lgcc_"..., "-plugin-opt=-pass-through=-lc", "-plugin-opt=-pass-through=-lgcc", "-plugin-opt=-pass-through=-lgcc_"..., "--sysroot=/opt/x86_64/sysroot", "--eh-frame-hdr", "-m", "elf_x86_64", "-dynamic-linker", "/lib64/ld-linux-x86-64.so.2", "-o", "bazel-out/k8-fastbuild/bin/hello"..., "/opt/x86_64/sysroot/usr/lib/../l"..., "/opt/x86_64/sysroot/usr/lib/../l"..., "external/gcc_x86_64_suite+/bin/."..., "-Lexternal/gcc_x86_64_suite+/bin"..., "-Lexternal/gcc_x86_64_suite+/bin"..., "-Lexternal/gcc_x86_64_suite+/bin"..., "-L/opt/x86_64/sysroot/lib/../lib"..., "-L/opt/x86_64/sysroot/usr/lib/.."..., "-Lexternal/gcc_x86_64_suite+/bin"..., "-L/opt/x86_64/sysroot/lib", "-L/opt/x86_64/sysroot/usr/lib", "bazel-out/k8-fastbuild/bin/_objs"..., "-S", "-Ttoolchains/x86/gcc/elf_x86_64."..., ...], 0x7ffcf0ac21d8 /* 62 vars */ <unfinished ...>
3502387 <... execve resumed>)           = 0
3502387 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libzstd.so.1", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libzstd.so.1", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/fedora_syslibs+/libzstd.so.1", O_RDONLY|O_CLOEXEC) = 3
3502387 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v3/libc.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/fedora_syslibs+/glibc-hwcaps/x86-64-v2/libc.so.6", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/fedora_syslibs+/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
3502387 openat(AT_FDCWD, "/usr/lib/locale/locale-archive", O_RDONLY|O_CLOEXEC) = 3
3502387 openat(AT_FDCWD, "/usr/lib64/gconv/gconv-modules.cache", O_RDONLY|O_CLOEXEC) = 3
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../libexec/gcc/x86_64-pc-linux-gnu/15.2.0/liblto_plugin.so", O_RDONLY|O_CLOEXEC) = 3
3502387 openat(AT_FDCWD, "toolchains/x86/gcc/elf_x86_64.xce", O_RDONLY) = 3
3502387 openat(AT_FDCWD, "bazel-out/k8-fastbuild/bin/helloworld", O_RDWR|O_CREAT|O_TRUNC, 0666) = 4
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/crt1.o", O_RDONLY) = 5
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/crt1.o", O_RDONLY) = 6
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/crti.o", O_RDONLY) = 6
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/crti.o", O_RDONLY) = 7
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/crtbegin.o", O_RDONLY) = 7
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/crtbegin.o", O_RDONLY) = 8
3502387 openat(AT_FDCWD, "bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.o", O_RDONLY) = 8
3502387 openat(AT_FDCWD, "bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.pic.o", O_RDONLY) = 9
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libstdc++.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libstdc++.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/libstdc++.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/libstdc++.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libstdc++.so", O_RDONLY) = 9
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libstdc++.so", O_RDONLY) = 10
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libm.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libm.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/libm.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/libm.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libm.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libm.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/lib/../lib64/libm.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/lib/../lib64/libm.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/libm.so", O_RDONLY) = 10
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/libm.so", O_RDONLY) = 11
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/libm.so", O_RDONLY) = 11
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/libm.so", O_RDONLY) = 10
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/./libm.so.6", O_RDONLY) = 10
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/./libm.so.6", O_RDONLY) = 11
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/./libmvec.so.1", O_RDONLY) = 11
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/./libmvec.so.1", O_RDONLY) = 12
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libgcc.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libgcc.a", O_RDONLY) = 12
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libgcc_s.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libgcc_s.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/libgcc_s.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/libgcc_s.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so", O_RDONLY) = 13
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so", O_RDONLY) = 14
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so", O_RDONLY) = 14
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so", O_RDONLY) = 13
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so.1", O_RDONLY) = 13
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so.1", O_RDONLY) = 14
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libgcc.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libgcc.a", O_RDONLY) = 14
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libc.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libc.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/libc.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/libc.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libc.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libc.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/lib/../lib64/libc.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/lib/../lib64/libc.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/libc.so", O_RDONLY) = 15
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/libc.so", O_RDONLY) = 16
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/libc.so", O_RDONLY) = 16
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/libc.so", O_RDONLY) = 15
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/./libc.so.6", O_RDONLY) = 15
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/./libc.so.6", O_RDONLY) = 16
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/./libc_nonshared.a", O_RDONLY) = 16
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/./ld-linux-x86-64.so.2", O_RDONLY) = 17
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/./ld-linux-x86-64.so.2", O_RDONLY) = 18
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libgcc.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libgcc.a", O_RDONLY) = 18
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libgcc_s.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libgcc_s.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/libgcc_s.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/libgcc_s.a", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so", O_RDONLY) = 19
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so", O_RDONLY) = 20
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so", O_RDONLY) = 20
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so", O_RDONLY) = 19
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so.1", O_RDONLY) = 19
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so.1", O_RDONLY) = 20
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libgcc.so", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/libgcc.a", O_RDONLY) = 20
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/crtend.o", O_RDONLY) = 21
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/crtend.o", O_RDONLY) = 22
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/crtn.o", O_RDONLY) = 22
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/crtn.o", O_RDONLY) = 23
3502387 openat(AT_FDCWD, "/usr/share/locale/locale.alias", O_RDONLY|O_CLOEXEC) = 23
3502387 openat(AT_FDCWD, "/usr/share/locale/en_US.UTF-8/LC_MESSAGES/bfd.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "/usr/share/locale/en_US.utf8/LC_MESSAGES/bfd.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "/usr/share/locale/en_US/LC_MESSAGES/bfd.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "/usr/share/locale/en.UTF-8/LC_MESSAGES/bfd.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "/usr/share/locale/en.utf8/LC_MESSAGES/bfd.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "/usr/share/locale/en/LC_MESSAGES/bfd.mo", O_RDONLY) = -1 ENOENT (No such file or directory)
3502387 openat(AT_FDCWD, "/opt/x86_64/sysroot/usr/lib/../lib64/./ld-linux-x86-64.so.2", O_RDONLY) = 23
3502387 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so.1", O_RDONLY) = 24
```

The linker subcommand shows the same dependence on the host's `locale` subsystem.  There's a likely issue with references to files like `ctrn.o`, `libc.so`, `libc_nonshared.a`,
and `crt1.o`.  These are read from the `/opt/x86_64/sysroot` location *if it exists* in the current root.  Bazel normally runs in a 'sandbox', using Linux container mechanisms
to block access to files not named as dependencies.  We reran the Bazel build and link commands outside of that sandboxing mechanisms, so `/opt/x86_64/sysroot` was accessible.
If we `mv /opt/x86_64 /opt/x86_64_save` and rerun the builds, strace shows that these problem files are correctly found within the toolchain sandbox.  The link subcommand
trace in that case shows:

```command
3503568 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../.././ld-linux-x86-64.so.2", O_RDONLY) = 23
3503568 openat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.2.0/../../../../lib64/libgcc_s.so.1", O_RDONLY) = 24
```

>Note: The file `ld-linux-x86-64.so.2` can be quite specific to a single kernel.  If the developer's workstation was materially different from the hypothetical
>      internal integration test server, the binary produced for the integration test server may not actually run on the developer's workstation.

Next try the C++ build with an explicit platform.

```console
$ bazel build -s --sandbox_debug --platforms=//platforms:x86_64 helloworld++
Starting local Bazel server (8.4.0) and connecting to it...
INFO: Analyzed target //:helloworld++ (72 packages loaded, 5823 targets configured).
SUBCOMMAND: # //:helloworld++ [action 'Compiling helloworld.cc', configuration: 18005088ebc3c2bce561736e29f2eb165b16ec1f9b674d24ecb15def1fcfd2bc, execution platform: @@platforms//host:host, mnemonic: CppCompile]
(cd /run/user/1000/bazel/execroot/_main && \
  exec env - \
    PATH=/home/thixotropist/.local/bin:/home/thixotropist/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/var/lib/snapd/snap/bin:/opt/ghidra_12.0_DEV/:/opt/jdk-22.0.1/bin:/opt/gradle-8.8/bin \
    PWD=/proc/self/cwd \
  toolchains/x86/gcc/wrappers/gcc -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15 -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include '-march=native' -no-canonical-prefixes -fno-canonical-system-headers -Wno-builtin-macro-redefined '-D__DATE__="redacted"' '-D__TIMESTAMP__="redacted"' '-D__TIME__="redacted"' -fstack-protector -Wall -Wunused-but-set-parameter -Wno-free-nonheap-object -fno-omit-frame-pointer '-std=c++20' -MD -MF bazel-out/k8-fastbuild/bin/_objs/helloworld++/helloworld.pic.d '-frandom-seed=bazel-out/k8-fastbuild/bin/_objs/helloworld++/helloworld.pic.o' -fPIC -iquote . -iquote bazel-out/k8-fastbuild/bin -iquote external/bazel_tools -iquote bazel-out/k8-fastbuild/bin/external/bazel_tools -c helloworld.cc -o bazel-out/k8-fastbuild/bin/_objs/helloworld++/helloworld.pic.o)
  ...
  1757776615.723480238: src/main/tools/linux-sandbox-pid1.cc:291: writable: /run/user/1000/bazel/sandbox/linux-sandbox/1/execroot/_main
  ...
SUBCOMMAND: # //:helloworld++ [action 'Linking helloworld++', configuration: 18005088ebc3c2bce561736e29f2eb165b16ec1f9b674d24ecb15def1fcfd2bc, execution platform: @@platforms//host:host, mnemonic: CppLink]
(cd /run/user/1000/bazel/execroot/_main && \
  exec env - \
    PATH=/home/thixotropist/.local/bin:/home/thixotropist/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/var/lib/snapd/snap/bin:/opt/ghidra_12.0_DEV/:/opt/jdk-22.0.1/bin:/opt/gradle-8.8/bin \
    PWD=/proc/self/cwd \
  toolchains/x86/gcc/wrappers/gcc -o bazel-out/k8-fastbuild/bin/helloworld++ bazel-out/k8-fastbuild/bin/_objs/helloworld++/helloworld.pic.o -Wl,-S -Wl,-Ttoolchains/x86/gcc/elf_x86_64.xce -Wl,-lstdc++ -Wl,-lm -Wl,-z,relro,-z,now -no-canonical-prefixes -pass-exit-codes)
...
1757776616.090555590: src/main/tools/linux-sandbox-pid1.cc:291: writable: /run/user/1000/bazel/sandbox/linux-sandbox/2/execroot/_main
```

For this run we will `mv /opt/x86_64 /opt/x86_64_save` first, and exclude from the output any file references into our toolchains.

The strace output from the compile phase is:

```console
strace -f -o /tmp/trace_c++.log toolchains/x86/gcc/wrappers/gcc -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include-fixed -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.2.0/include -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15/x86_64-pc-linux-gnu -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include/c++/15 -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include '-march=native' -no-canonical-prefixes -fno-canonical-system-headers -Wno-builtin-macro-redefined '-D__DATE__="redacted"' '-D__TIMESTAMP__="redacted"' '-D__TIME__="redacted"' -fstack-protector -Wall -Wunused-but-set-parameter -Wno-free-nonheap-object -fno-omit-frame-pointer '-std=c++20' -MD -MF bazel-out/k8-fastbuild/bin/_objs/helloworld++/helloworld.pic.d '-frandom-seed=bazel-out/k8-fastbuild/bin/_objs/helloworld++/helloworld.pic.o' -fPIC -iquote . -iquote bazel-out/k8-fastbuild/bin -iquote external/bazel_tools -iquote bazel-out/k8-fastbuild/bin/external/bazel_tools -c helloworld.cc -o bazel-out/k8-fastbuild/bin/_objs/helloworld++/helloworld.pic.o

$ grep -P 'openat|execve'  /tmp/trace_c++.log|grep -v /run/user/1000/bazel/external/gcc_x86_64_suite+
...
```

The output looks clean, showing lots of valid references into `external/fedora_syslibs+` and the usual links into the host system's locale libraries.  Near the start is a single reference to the host
system's `libc.so.6` which is *probably* loaded by `strace` rather than our toolchain itself.

Repeat for the linker phase, getting about the same results.

The linker phase shows a concern, where the linker acquires the loader script `elf_x86_64.xce` from `toolchains/x86/gcc`. We would normally want it loaded from `gcc_x86_64_suite/x86_64-pc-linux-gnu/lib/ldscripts/elf_x86_64.xce`,
since that file is versioned with the compiler toolchain suite.  However, the toolchain suite's version contains explicit references to the wrong search path:

```text
SEARCH_DIR("=/opt/x86_64/sysroot/x86_64-pc-linux-gnu/lib64");
``````

Our override version search paths look like this instead:

```text
SEARCH_DIR("external/gcc_x86_64_suite+/lib64")
```

>WARNING: There are about 125 different loader scripts in our toolchain suite - these should probably *all* be edited to avoid the absolute paths.  We'll punt on that until we actually have a dedicated internal integration test server.

## RISC-V toolchain path analysis

Now we want to repeat the path analysis for the risc-v 64 bit toolchain.  The planned steps are:

1. Run `integration_test.sh` to establish a baseline
2. Edit the risc-v compiler suite and toolchain files so that improvements we have made to the x86_64 toolchain are replicated in the risc-v toolchain.  We want any remaining differences to be essential differences,
   so that it is easy to keep the two closely aligned.
3. Run `integration_test.sh` to verify no regressions
4. Build and trace the C and C++ helloworld examples to verify paths.
