# Debugging path and hermeticity problems

Untangling search path problems is often a challenge with hermetic toolchains.  Absolute paths are compiled into programs and scripts,
breaking the build when we try an execute on a machine other than the one in which the compiler suite was actually installed.

This file collects debugging case studies using the riscv toolchain as an example.

## Finding crt1.o

Every user-space executable using `libc.so` needs to include `crt1.o` in its link inputs.  Let's debug a case in which our toolchain
can't find `crt1.o`.

```console
$ bazel build --sandbox_debug --subcommands --platforms=//platforms:riscv64 helloworld
INFO: Analyzed target //:helloworld (0 packages loaded, 0 targets configured).
SUBCOMMAND: # //:helloworld [action 'Linking helloworld', configuration: 23cc6e53e11cc61cfec907df36e56120f7fbed3ddc8305590321f94d67847b14, execution platform: @@platforms//host:host, mnemonic: CppLink]
(cd /run/user/1000/bazel/execroot/_main && \
...
  toolchains/riscv/gcc-riscv/imported/gcc -o bazel-out/k8-fastbuild/bin/helloworld bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o -Wl,-S -Wl,-T/tmp/ldscript -lstdc++)
# Configuration: 23cc6e53e11cc61cfec907df36e56120f7fbed3ddc8305590321f94d67847b14
# Execution platform: @@platforms//host:host
DEBUG: Sandbox debug output for CppLink //:helloworld:
...
Run this command to start an interactive shell in an identical sandboxed environment:
(exec env - \
    ...
  /home/thixotropist/.cache/bazel/_bazel_thixotropist/install/3744b016d0eb18910a3977c3596f2493/linux-sandbox -t 15 -w /dev/shm -w /run/user/1000/bazel/sandbox/linux-sandbox/10/execroot/_main -w /tmp -S /run/user/1000/bazel/sandbox/linux-sandbox/10/stats.out -D /run/user/1000/bazel/sandbox/linux-sandbox/10/debug.out -- /bin/sh -i)
ERROR: /home/thixotropist/projects/github/bazel_compiler_modules/examples/BUILD:3:10: Linking helloworld failed: (Exit 1): linux-sandbox failed: error executing CppLink command 
  (cd /run/user/1000/bazel/sandbox/linux-sandbox/10/execroot/_main && \
  exec env - \
    ...
  /home/thixotropist/.cache/bazel/_bazel_thixotropist/install/3744b016d0eb18910a3977c3596f2493/linux-sandbox -t 15 -w /dev/shm -w /run/user/1000/bazel/sandbox/linux-sandbox/10/execroot/_main -w /tmp -S /run/user/1000/bazel/sandbox/linux-sandbox/10/stats.out -D /run/user/1000/bazel/sandbox/linux-sandbox/10/debug.out -- toolchains/riscv/gcc-riscv/imported/gcc -o bazel-out/k8-fastbuild/bin/helloworld bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o -Wl,-S -Wl,-T/tmp/ldscript -lstdc++)
/run/user/1000/bazel/external/gcc_riscv_suite+/bin/../lib/gcc/riscv64-unknown-linux-gnu/15.0.1/../../../../riscv64-unknown-linux-gnu/bin/ld: cannot find crt1.o: No such file or directory
collect2: error: ld returned 1 exit status
Target //:helloworld failed to build
Use --verbose_failures to see the command lines of failed build steps.
INFO: Elapsed time: 0.102s, Critical Path: 0.04s
INFO: 2 processes: 2 internal.
ERROR: Build did NOT complete successfully
```

This failure notification shows:

* The build command includes `--sandbox_debug` and `--subcommands` to expose the linux commands invoked by bazel
* The failure occured in the `CppLink` phase, after compilation had completed
* The sandbox directory was `/run/user/1000/bazel/sandbox/linux-sandbox/10/execroot/_main` - and it was preserved from deletion after the build
* The failing command was `toolchains/riscv/gcc-riscv/imported/gcc -o bazel-out/k8-fastbuild/bin/helloworld bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o -Wl,-S -Wl,-T/tmp/ldscript -lstdc++`
* We attempted a custom ldscript from `/tmp/ldscript`.  The SEARCH_DIR there includes
    * "/run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/lib"
    * "/run/user/1000/bazel/external/gcc_riscv_suite+/lib"
* The error returned from `ld` was `cannot find crt1.o: No such file or directory`

Since the sandbox was preserved, we can retry the failing command in the same environment but without strict hermeticity.

```console
$ pushd /run/user/1000/bazel/sandbox/linux-sandbox/10/execroot/_main
$/run/user/1000/bazel/sandbox/linux-sandbox/10/execroot/_main ~/projects/github/bazel_compiler_modules/examples
/run/user/1000/bazel/external/gcc_riscv_suite+/bin/../lib/gcc/riscv64-unknown-linux-gnu/15.0.1/../../../../riscv64-unknown-linux-gnu/bin/ld: cannot find crt1.o
```

Is `crt1.o` present in the sandbox?

```console
$ find /run/user/1000/bazel/external/gcc_riscv_suite+ -name crt1.o -ls
/run/user/1000/bazel/external/gcc_riscv_suite+/lib/crt1.o
... -rw-r--r-- ... 13864 Jan 23 09:47 /run/user/1000/bazel/external/gcc_riscv_suite+/lib/crt1.o
```

So why can't the linker find it?  More specifically, where is the loader searching for this file?  The `strace` utility helps us with the answer.

```console
$ strace -f toolchains/riscv/gcc-riscv/imported/gcc -o bazel-out/k8-fastbuild/bin/helloworld bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o -Wl,-S -Wl,-T/tmp/ldscript -lstdc++ 2>&1 | less
[pid 273206] access("/run/user/1000/bazel/external/gcc_riscv_suite+/bin/../lib/gcc/riscv64-unknown-linux-gnu/15.0.1/crt1.o", R_OK) = -1 ENOENT (No such file or directory)
[pid 273206] access("/run/user/1000/bazel/external/gcc_riscv_suite+/bin/../lib/gcc/crt1.o", R_OK) = -1 ENOENT (No such file or directory)
[pid 273206] access("/run/user/1000/bazel/external/gcc_riscv_suite+/bin/../lib/gcc/riscv64-unknown-linux-gnu/15.0.1/../../../../riscv64-unknown-linux-gnu/lib/riscv64-unknown-linux-gnu/15.0.1/crt1.o", R_OK) = -1 ENOENT (No such file or directory)
[pid 273206] access("/run/user/1000/bazel/external/gcc_riscv_suite+/bin/../lib/gcc/riscv64-unknown-linux-gnu/15.0.1/../../../../riscv64-unknown-linux-gnu/lib/crt1.o", R_OK) = -1 ENOENT (No such file or directory)
[pid 273206] access("/opt/riscv/sysroot/lib64/lp64d/riscv64-unknown-linux-gnu/15.0.1/crt1.o", R_OK) = -1 ENOENT (No such file or directory)
[pid 273206] access("/opt/riscv/sysroot/lib64/lp64d/crt1.o", R_OK) = -1 ENOENT (No such file or directory)
[pid 273206] access("/opt/riscv/sysroot/usr/lib64/lp64d/riscv64-unknown-linux-gnu/15.0.1/crt1.o", R_OK) = -1 ENOENT (No such file or directory)
[pid 273206] access("/opt/riscv/sysroot/usr/lib64/lp64d/crt1.o", R_OK) = -1 ENOENT (No such file or directory)
[pid 273206] access("/opt/riscv/sysroot/lib/riscv64-unknown-linux-gnu/15.0.1/crt1.o", R_OK) = -1 ENOENT (No such file or directory)
[pid 273206] access("/opt/riscv/sysroot/lib/crt1.o", R_OK) = -1 ENOENT (No such file or directory)
[pid 273206] access("/opt/riscv/sysroot/usr/lib/riscv64-unknown-linux-gnu/15.0.1/crt1.o", R_OK) = -1 ENOENT (No such file or directory)
[pid 273206] access("/opt/riscv/sysroot/usr/lib/crt1.o", R_OK) = -1 ENOENT (No such file or directory)
[pid 273206] access("/run/user/1000/bazel/external/gcc_riscv_suite+/bin/../lib/gcc/riscv64-unknown-linux-gnu/15.0.1/crti.o", R_OK) = 0
[pid 273206] access("/run/user/1000/bazel/external/gcc_riscv_suite+/bin/../lib/gcc/riscv64-unknown-linux-gnu/15.0.1/crtbegin.o", R_OK) = 0
```

It looks like the linker is searching through a dozen directories for `crt1.o` and failing each time.  The file was copied into the sysroot directory
as part of the bootstrap, and is in the wrong place.  Try a local patch:

```console
$ mv /run/user/1000/bazel/external/gcc_riscv_suite+/lib/crt1.o /run/user/1000/bazel/external/gcc_riscv_suite+/lib/gcc/crt1.o
$ toolchains/riscv/gcc-riscv/imported/gcc -o bazel-out/k8-fastbuild/bin/helloworld bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o -Wl,-S -Wl,-T/tmp/ldscript -lstdc++ 2>&1
$ ls -l bazel-out/k8-fastbuild/bin/helloworld
-rwxr-xr-x. 1 ... 8712 Jan 28 16:21 bazel-out/k8-fastbuild/bin/helloworld
$ file bazel-out/k8-fastbuild/bin/helloworld
bazel-out/k8-fastbuild/bin/helloworld: ELF 64-bit LSB executable, UCB RISC-V, RVC, double-float ABI, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-riscv64-lp64d.so.1, for GNU/Linux 4.15.0, not stripped
```

That looks good, so make the change permanent.

```console
$ pushd /opt/riscv_save
$ find . -name crt1.o
./sysroot/lib/crt1.o
/opt/riscv_save$ mv sysroot/lib/crt1.o sysroot/lib/gcc/crt1.o
$ sudo mv /opt/riscv_save /opt/riscv
$ cd .../bazel_compiler_modules
# edit src/gcc_riscv_suite/BUILD to change "lib/crt1.o" to "lib/gcc/crt1.o"
$ scripts/gcc_riscv.py
$ sudo mv /opt/riscv /opt/riscv_save
$ cd examples
# restart the Bazel server so that it will reload the compiler suite
$ bazel shutdown
$ bazel build --sandbox_debug --subcommands --platforms=//platforms:riscv64 helloworld
...
$ file bazel-bin/helloworld
bazel-bin/helloworld: ELF 64-bit LSB executable, UCB RISC-V, RVC,
```

And we're done.

## include paths and include_next

C++ compilations can be very fussy about include path search orders.  Try building the C++ version of helloworld:

```console
$ bazel build --platforms=//platforms:riscv64 helloworld++
INFO: Analyzed target //:helloworld++ (0 packages loaded, 0 targets configured).
ERROR: /home/thixotropist/projects/github/bazel_compiler_modules/examples/BUILD:9:10: Compiling helloworld.cc failed: (Exit 1): gcc failed: error executing CppCompile command (from target //:helloworld++) toolchains/riscv/gcc-riscv/imported/gcc -MD -MF bazel-out/k8-fastbuild/bin/_objs/helloworld++/helloworld.d '-frandom-seed=bazel-out/k8-fastbuild/bin/_objs/helloworld++/helloworld.o' -iquote . -iquote ... (remaining 16 arguments skipped)

Use --sandbox_debug to see verbose messages from the sandbox and retain the sandbox build root for debugging
In file included from /run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/include/c++/15.0.1/ext/string_conversions.h:45,
                 from /run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/include/c++/15.0.1/bits/basic_string.h:4230,
                 from /run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/include/c++/15.0.1/string:56,
                 from /run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/include/c++/15.0.1/bits/locale_classes.h:42,
                 from /run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/include/c++/15.0.1/bits/ios_base.h:43,
                 from /run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/include/c++/15.0.1/ios:46,
                 from /run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/include/c++/15.0.1/bits/ostream.h:43,
                 from /run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/include/c++/15.0.1/ostream:42,
                 from /run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/include/c++/15.0.1/iostream:43,
                 from helloworld.cc:1:
/run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/include/c++/15.0.1/cstdlib:83:15: fatal error: stdlib.h: No such file or directory
   83 | #include_next <stdlib.h>
      |               ^~~~~~~~~~
compilation terminated.
```

What was the include path? we can get it from the build log if we enable sandbox_debug

* /run/user/1000/bazel/external/gcc_riscv_suite+/lib/gcc/riscv64-unknown-linux-gnu/15.0.1/include-fixed
* /run/user/1000/bazel/external/gcc_riscv_suite+/lib/gcc/riscv64-unknown-linux-gnu/15.0.1/include
* //run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/include/c++/15.0.1
    * the "//" instead of "/" is a red herring - fix it, but it makes no difference
* /run/user/1000/bazel/external/gcc_riscv_suite+/lib/gcc/riscv64-unknown-linux-gnu/include
    * this directory doesn't exist - but it is also a red herring, and makes no difference.
* /run/user/1000/bazel/external/gcc_riscv_suite+/usr/include
* /run/user/1000/bazel/external/gcc_riscv_suite+/include

Running strace in the sandbox shows the problem.  stdlib.h is not being searched in the directories marked with `-I`.
I used the wrong gcc flags like `-I.../lib/gcc/riscv64-unknown-linux-gnu/15.0.1/include` instead of 
`-isystem.../lib/gcc/riscv64-unknown-linux-gnu/15.0.1/include`.  Fix this and repeat:

```console
$ bazel build --platforms=//platforms:riscv64 helloworld++
WARNING: Couldn't auto load rules or symbols, because no dependency on module/repository 'rules_android' found. This will result in a failure if there's a reference to those rules or symbols.
INFO: Analyzed target //:helloworld++ (71 packages loaded, 3747 targets configured).
INFO: Found 1 target...
Target //:helloworld++ up-to-date:
  bazel-bin/helloworld++
INFO: Elapsed time: 1.031s, Critical Path: 0.46s
INFO: 6 processes: 4 internal, 2 linux-sandbox.
INFO: Build completed successfully, 6 total actions
```

## Updating regressions

The Bazel approach to crosscompiler configuration evolves as new compiler features arrive.  They do a good job of
maintaining backwards compatibility, so rebasing to the current configuration methodology is usually optional.
This example shows how to debug broken linkages during one such update.

### Current configuration model

Bazel uses a `cc_toolchain_config` object to hold C and C++ compiler configuration.  Among other things,
this object holds the file system paths needed to invoke `gcc` and other crosscompiler components.

For example, the following lines in `cc_toolchain_config.bzl` tell Bazel what to execute when compiling C or C++:

```py
...
    tool_paths = [
        tool_path(
            name = "gcc",
            path = "gcc/wrappers/gcc",
        ),
...
        tool_path(
            name = "as",
            path = "gcc/wrappers/as",
        ),
    ]
...
```

Most of the time the assembler `as` is called by `gcc` directly, not using this wrapper.

Bazel factors configuration into actions, features, and flags.

* actions can include
    * ACTION_NAMES.c_compile
    * ACTION_NAMES.cpp_compile,
    * ACTION_NAMES.assemble,
    * ACTION_NAMES.preprocess_assemble,
    * ACTION_NAMES.cpp_header_parsing,
    * ACTION_NAMES.cpp_link_executable,
    * ACTION_NAMES.cpp_link_dynamic_library,
* features collect the flags needed to implement an action.  You might see features named:
    * default_compile_flags
    * default_default_link_flags
* flags are standard GCC command line flags like `-O3`.  Each feature has flag sets and flag groups
  to show which flags are needed to implement a specific feature.

### The bug to fix

After refactoring of `cc_toolchain_config` the riscv64 build of helloworld fails with the message

```text
Assembler messages:
Fatal error: invalid -march= option: `rv64gcv_zfhmin_zvfhmin_zvbb_zicond_zimop_zcmop_zcb_zfa_zawrs_zvkng_zvksg'
```

The most likely problem is gcc invoking the wrong assembler, say the native x86_64 assembler instead of the
toolchain suite's riscv64 assembler.  Run the build with sandbox and subcommand
debugging to look at the command line.  Some line breaks and annotation are added for clarity.

```console
$ bazel build --sandbox_debug --subcommands --platforms=//platforms:riscv64 helloworld
...
(cd /run/user/1000/bazel/sandbox/linux-sandbox/25/execroot/_main && \
  exec env - \
    ...
    PWD=/proc/self/cwd \
    TMPDIR=/tmp \
  ... toolchains/riscv/gcc/wrappers/gcc
        -isystem/run/user/1000/bazel/external/gcc_riscv_suite+/lib/gcc/riscv64-unknown-linux-gnu/15.0.1/include-fixed -isystem/run/user/1000/bazel/external/gcc_riscv_suite+/lib/gcc/riscv64-unknown-linux-gnu/15.0.1/include -isystem/run/user/1000/bazel/external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/include/c++/15.0.1
        -isystem/run/user/1000/bazel/external/gcc_riscv_suite+/usr/include
        -isystem/run/user/1000/bazel/external/gcc_riscv_suite+/include '-march=rv64gcv_zfhmin_zvfhmin_zvbb_zicond_zimop_zcmop_zcb_zfa_zawrs_zvkng_zvksg'
        -no-canonical-prefixes
        -fno-canonical-system-headers
        -Wno-builtin-macro-redefined
        '-D__DATE__="redacted"'
        '-D__TIMESTAMP__="redacted"'
        '-D__TIME__="redacted"'
        -fstack-protector
        -Wall
        -Wunused-but-set-parameter
        -Wno-free-nonheap-object
        -fno-omit-frame-pointer
        -MD -MF bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.d
        '-frandom-seed=bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o'
        -iquote .
        -iquote bazel-out/k8-fastbuild/bin
        -iquote external/bazel_tools
        -iquote bazel-out/k8-fastbuild/bin/external/bazel_tools
        -c helloworld.c
        -o bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o
)
```

Push into the sandbox and run this command using `strace -f`.  We want to know the search path for the assembler.

```text
[pid 368477] newfstatat(AT_FDCWD, "external/gcc_riscv_suite+/bin/../libexec/gcc/riscv64-unknown-linux-gnu/15.0.1/as", 0x7ffcc9249bc0, 0) = -1 ENOENT (No such file or directory)
[pid 368477] newfstatat(AT_FDCWD, "external/gcc_riscv_suite+/bin/../libexec/gcc/as", 0x7ffcc9249bc0, 0) = -1 ENOENT (No such file or directory)
[pid 368477] newfstatat(AT_FDCWD, "external/gcc_riscv_suite+/bin/../lib/gcc/riscv64-unknown-linux-gnu/15.0.1/../../../../riscv64-unknown-linux-gnu/bin/riscv64-unknown-linux-gnu/15.0.1/as", 0x7ffcc9249bc0, 0) = -1 ENOENT (No such file or directory)
[pid 368477] newfstatat(AT_FDCWD, "external/gcc_riscv_suite+/bin/../lib/gcc/riscv64-unknown-linux-gnu/15.0.1/../../../../riscv64-unknown-linux-gnu/bin/as", 0x7ffcc9249bc0, 0) = -1 ENOENT (No such file or directory)
[pid 368477] mmap(NULL, 36864, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_STACK, -1, 0) = 0x7fb040983000
[pid 368477] rt_sigprocmask(SIG_BLOCK, ~[], [], 8) = 0
[pid 368477] clone3({flags=CLONE_VM|CLONE_VFORK|CLONE_CLEAR_SIGHAND, exit_signal=SIGCHLD, stack=0x7fb040983000, stack_size=0x9000}, 88strace: Process 368480 attached
 <unfinished ...>
[pid 368480] rt_sigprocmask(SIG_BLOCK, NULL, ~[KILL STOP], 8) = 0
[pid 368480] rt_sigprocmask(SIG_SETMASK, [], NULL, 8) = 0
[pid 368480] execve("/home/gary/.local/bin/as", ["as", "--traditional-format", "-march=rv64gcv_zfhmin_zvfhmin_zv"..., "-march=rv64imafdcv_zicond_zicsr_"..., "-mabi=lp64d", "-misa-spec=20191213", "-o", "bazel-out/k8-fastbuild/bin/_objs"..., "/tmp/cc8eYW3a.s"], 0xe0f6990 /* 61 vars */) = -1 ENOENT (No such file or directo
ry)
[pid 368480] execve("/usr/local/bin/as", ["as", "--traditional-format", "-march=rv64gcv_zfhmin_zvfhmin_zv"..., "-march=rv64imafdcv_zicond_zicsr_"..., "-mabi=lp64d", "-misa-spec=20191213", "-o", "bazel-out/k8-fastbuild/bin/_objs"..., "/tmp/cc8eYW3a.s"], 0xe0f6990 /* 61 vars */) = -1 ENOENT (No such file or directory)
[pid 368480] execve("/usr/local/sbin/as", ["as", "--traditional-format", "-march=rv64gcv_zfhmin_zvfhmin_zv"..., "-march=rv64imafdcv_zicond_zicsr_"..., "-mabi=lp64d", "-misa-spec=20191213", "-o", "bazel-out/k8-fastbuild/bin/_objs"..., "/tmp/cc8eYW3a.s"], 0xe0f6990 /* 61 vars */) = -1 ENOENT (No such file or directory)
[pid 368480] execve("/usr/bin/as", ["as", "--traditional-format", "-march=rv64gcv_zfhmin_zvfhmin_zv"..., "-march=rv64imafdcv_zicond_zicsr_"..., "-mabi=lp64d", "-misa-spec=20191213", "-o", "bazel-out/k8-fastbuild/bin/_objs"..., "/tmp/cc8eYW
```

So we wanted a riscv64 assembler under `external/gcc_riscv_suite+` but the system could only find `/usr/bin/as`.  It searched in three configured places then in several
locations in the user's PATH.

The configured search order was:

* external/gcc_riscv_suite+/libexec/gcc/riscv64-unknown-linux-gnu/15.0.1/as
* external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/bin/riscv64-unknown-linux-gnu/15.0.1/as
* external/gcc_riscv_suite+/riscv64-unknown-linux-gnu/bin/as

None of those exist in our compiler suite module.  What we have instead is:
* external/gcc_riscv_suite+/bin/riscv64-unknown-linux-gnu-as

The assembler exists in our `/opt` install directory, as a single file with two directory links

* sysroot/bin/riscv64-unknown-linux-gnu-as
* sysroot/riscv64-unknown-linux-gnu/bin/as

So we have lost the assembler at one of two steps:

* `sysroot/riscv64-unknown-linux-gnu/bin/as` may not have been copied into the module tarball
    * it appears to exist there
* `sysroot/riscv64-unknown-linux-gnu/bin/as` may not have been added to the compiler_files filegroup
    * it appears to be missing here

Fix this by editing `src/gcc_riscv_suite/BUILD` in the top level modules directory to read:

```py
# Note that binutils executables have a different naming convention and location than GCC executables
filegroup(
    name = "compiler_files",
    srcs = [
        "riscv64-unknown-linux-gnu/bin/ar",
        "riscv64-unknown-linux-gnu/bin/as",
        "riscv64-unknown-linux-gnu/bin/ld",
        "riscv64-unknown-linux-gnu/bin/ld.bfd",
        "riscv64-unknown-linux-gnu/bin/objdump",
        "riscv64-unknown-linux-gnu/bin/ranlib",
        "riscv64-unknown-linux-gnu/bin/readelf",
        "riscv64-unknown-linux-gnu/bin/strip",
        "bin/riscv64-unknown-linux-gnu-cpp",
        "bin/riscv64-unknown-linux-gnu-gcc",
        ":c++_std_includes",
        ":lib",
        ":libexec",
        ":std_includes",
        "@fedora_syslibs//:common_compiler_ldd_dependencies",
    ],
)
```

## No support of optimization

The toolchain configuration doesn't recognize `-c opt` command line options.  We get the same results with or without `-c opt`, and none of the
intended optimization flags are present.

The configuration is controlled by a dynamically loaded file `external/rules_cc+/cc/private/toolchain/cc_toolchain_config.bzl`.  Documentation
is found at https://bazel.build/docs/cc-toolchain-config-reference.

Comparing our configuration with the reference configuration shows the problem - we need to add the definition `opt_feature = feature(name = "opt")` and
then add this feature to the set of features available to the configuration.  This feature is only triggered if the command line includes
switches like `-c opt` or `--features opt`.

Let's add support for `-c dbg` too.

## The ldscript location makes it non-hermetic

The toolchain configuration adds `-T/tmp/ldscript` to every link action.  That makes it non-portable and non-hermetic.
There are about 370 discrete linker scripts provided in our compiler suite, under `riscv64-unknown-linux-gnu/lib/ldscripts` - and all of them include
non-hermetic search paths like

```text
SEARCH_DIR("=/opt/riscv/sysroot/riscv64-unknown-linux-gnu/lib64/lp64f");
SEARCH_DIR("=/opt/riscv/sysroot/riscv64-unknown-linux-gnu/lib64")
```

The file `/tmp/ldscript` is good for `-z combreloc` and essentially the same as `elf64lriscv_lp64f.xc`.
If we wanted `pie` code for a kernel module or sharable object library we would want to use something based on `elf64lriscv_lp64f.xdc` instead.

Let's change the configuration to support a pair of loader scripts bundled within the toolchain, and with SEARCH_DIR values adjusted

>Summary: At this point the riscv toolchain appears to be working without a resident `/opt/riscv` installation tree.  It's
>         not truly hermetic, as localized messages may still be taken from /usr.

## Debugging x86_64 toolchains

Apply lessons learned from the riscv debugging to x86_.  The context is different:

* The x86_64 compiler suite is not configured as a cross-compiler, but as an alternate suite on the same base architecture.
  That means default installation and search paths will be different.
* We can hide the installation directory `/opt/x86_64` after the module is built, but we can't hide similar files under `/usr`.

Try a simple helloworld build:

```console
$ bazel clean
$ bazel build --verbose_failures --sandbox_debug --subcommands --platforms=//platforms:x86_64 helloworld
...
SUBCOMMAND: # //:helloworld [action 'Compiling helloworld.c
...
toolchains/x86/gcc/wrappers/gcc -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.0.1/include-fixed -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/lib/gcc/x86_64-pc-linux-gnu/15.0.1/include -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/x86_64-pc-linux-gnu/include/c++/15.0.1 -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/usr/include -isystem/run/user/1000/bazel/external/gcc_x86_64_suite+/include -no-canonical-prefixes -fno-canonical-system-headers -Wno-builtin-macro-redefined '-D__DATE__="redacted"' '-D__TIMESTAMP__="redacted"' '-D__TIME__="redacted"' -fstack-protector -Wall -Wunused-but-set-parameter -Wno-free-nonheap-object -fno-omit-frame-pointer -MD -MF bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.d '-frandom-seed=bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o' -iquote . -iquote bazel-out/k8-fastbuild/bin -iquote external/bazel_tools -iquote bazel-out/k8-fastbuild/bin/external/bazel_tools -c helloworld.c -o bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o
...
SUBCOMMAND: # //:helloworld [action 'Linking helloworld'
...
toolchains/x86/gcc/wrappers/gcc -o bazel-out/k8-fastbuild/bin/helloworld bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o -Wl,-S -Wl,-Ttoolchains/x86/gcc/elf_x86_64.xce -Wl,-lstdc++ -Wl,-z,relro,-z,now -no-canonical-prefixes -pass-exit-codes
...
ERROR: /home/gary/projects/github/bazel_compiler_modules/examples/BUILD:3:10: Linking helloworld failed: (Exit 1): linux-sandbox failed: error executing CppLink command 
/usr/bin/ld: bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o: undefined reference to symbol 'puts@@GLIBC_2.2.5'
/usr/bin/ld: external/fedora_syslibs+/libc.so.6: error adding symbols: DSO missing from command line
collect2: error: ld returned 1 exit status
```

The compilation appears to have succeeded while the linking failed with a missing symbol.  Let's review the evidence:

* Compilation
    * The list of dependencies `bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.d` looks good - there are no references to `/opt/x86_64` or `/usr`.
    * The compiled object file `bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o` shows one undefined symbol - `puts` - to be resolved via a library like libc.
* Linking
    * The linker script `examples/toolchains/x86/gcc/elf_x86_64.xce` adds `SEARCH_DIR("external/gcc_x86_64_suite+/lib64")` and
      `SEARCH_DIR("external/gcc_x86_64_suite+/lib")`.
    * The link failures are `undefined reference to symbol 'puts@@GLIBC_2.2.5'` and `external/fedora_syslibs+/libc.so.6: error adding symbols`
    * The error is generated by the host's `/usr/bin/ld` rather than the toolchain's `ld`.

The translation from `puts` to `puts@@GLIBC_2.2.5` is confusing.  It suggests libc is involved, and possibly the `libresolv` component of the `glibc` package.

Run the link command through `strace` to see at least part of the problem.

`gcc` is failing to find `ld` in many places in our toolchain suite, including `external/gcc_x86_64_suite+/bin/libexec/gcc/ld`.
It ends up using `/usr/bin/ld` instead.

We'll revisit the correct solution to how our compiler suite chooses `ld` later.  For now, we will adjust the PATH for this command and rerun under strace
with special attention to system calls opening files.

```console
PATH=external/gcc_x86_64_suite+/bin:$PATH strace -f toolchains/x86/gcc/wrappers/gcc -o bazel-out/k8-fastbuild/bin/helloworld bazel-out/k8-fastbuild/bin/_objs/helloworld/helloworld.o -Wl,-Map=/tmp/bazel.map -Wl,-S -Wl,-Ttoolchains/x86/gcc/elf_x86_64.xce -Wl,-lstdc++ -Wl,-z,relro,-z,now -no-canonical-prefixes -pass-exit-codes 2>&1 |grep -E 'execve|openat|newfstat|readlink' > /tmp/bazel.log

cat /tmp/bazel.log
...
pid 237061] newfstatat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../libexec/gcc/x86_64-pc-linux-gnu/15.0.1/real-ld", 0x7ffd29fc3510, 0) = -1 ENOENT (No such file or directory)
[pid 237061] newfstatat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../libexec/gcc/real-ld", 0x7ffd29fc3510, 0) = -1 ENOENT (No such file or directory)
[pid 237061] newfstatat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../libexec/gcc/x86_64-pc-linux-gnu/15.0.1/collect-ld", 0x7ffd29fc3510, 0) = -1 ENOENT (No such file or directory)
[pid 237061] newfstatat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../libexec/gcc/collect-ld", 0x7ffd29fc3510, 0) = -1 ENOENT (No such file or directory)
[pid 237061] newfstatat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../libexec/gcc/x86_64-pc-linux-gnu/15.0.1/ld", 0x7ffd29fc3510, 0) = -1 ENOENT (No such file or directory)
[pid 237061] newfstatat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/../libexec/gcc/ld", 0x7ffd29fc3510, 0) = -1 ENOENT (No such file or directory)
[pid 237061] newfstatat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/ld", {st_mode=S_IFREG|0755, st_size=2671016, ...}, 0) = 0
[pid 237061] newfstatat(AT_FDCWD, "external/gcc_x86_64_suite+/bin/ld", {st_mode=S_IFREG|0755, st_size=2671016, ...}, 0) = 0
...
```

This shows some suspiciously late references to `external/fedora_syslibs+/libc.so.6` after references to
`external/gcc_x86_64_suite+/bin/../lib/gcc/x86_64-pc-linux-gnu/15.0.1/libgcc.a`.  The library in `fedora_syslibs` is needed
to run tools like `gcc`, `ld`, and `collect2` on the host computer, while the library in `gcc_x86_64_suite+` is the one we should link
target executables against.  Are they getting mixed up?  Are their significant version changes?

Browsing through files like `libc.so` and `libc.so.6` shows us some clues

```console
$ readelf -as  /run/user/1000/bazel/execroot/_main/external/gcc_x86_64_suite+/lib/libc.so.6|grep puts@@GLIBC
   237: 00000000000574e0   514 FUNC    WEAK   DEFAULT    5 puts@@GLIBC_2.2.5
  2589: 00000000000574e0   514 FUNC    GLOBAL DEFAULT    5 _IO_puts@@GLIBC_2.2.5
  2648: 0000000000055bd0   418 FUNC    WEAK   DEFAULT    5 fputs@@GLIBC_2.2.5
$ readelf -as  /run/user/1000/bazel/execroot/_main/external/fedora_syslibs+/libc.so.6|grep puts@@GLIBC
   237: 000000000005daa0   518 FUNC    WEAK   DEFAULT    3 puts@@GLIBC_2.2.5
  2584: 000000000005daa0   518 FUNC    GLOBAL DEFAULT    3 _IO_puts@@GLIBC_2.2.5
  2643: 000000000005c100   422 FUNC    WEAK   DEFAULT    3 fputs@@GLIBC_2.2.5
$ readelf -as  /usr/lib64/libc.so.6|grep puts@@GLIBC
   237: 000000000005daa0   518 FUNC    WEAK   DEFAULT    6 puts@@GLIBC_2.2.5
  2584: 000000000005daa0   518 FUNC    GLOBAL DEFAULT    6 _IO_puts@@GLIBC_2.2.5
  2643: 000000000005c100   422 FUNC    WEAK   DEFAULT    6 fputs@@GLIBC_2.2.5
```

So all three libraries define the missing symbol - none is being found, there is no mixup.

The linker finds `libc.so.6` by examining `libc.so`.  This can be a symbolic link or a linker script including
`GROUP` directives.  What we have is neither.

```console
$ cat /run/user/1000/bazel/execroot/_main/external/gcc_x86_64_suite+/lib/libc.so
/* GNU ld script
   Use the shared library, but some functions are only in
   the static library, so try that secondarily.  */
OUTPUT_FORMAT(elf64-x86-64)
```

It looks like I dropped a critical line when removing absolute links.  This file should
instead be

```text
/* GNU ld script
   Use the shared library, but some functions are only in
   the static library, so try that secondarily.  */
OUTPUT_FORMAT(elf64-x86-64)
GROUP ( ./libc.so.6 ./libc_nonshared.a  AS_NEEDED ( ./ld-linux-x86-64.so.2 ) )
```

Make that change in `/opt/x86_64` , rerun `scripts/gcc_x86_64.py`, then `bazel shutdown` and `bazel clean` to force reloading the toolchain suite,
and the build works.  But it's not hermetic, since gcc is still silently using the system's `ld` to do the linking.

We can fix that by changing the `examples/toolchains/x86/wrappers/gcc` to use an explicit path leading to the correct - toolchain - `ld` and not
the host system `ld`.

There is likely a better way to handle this, perhaps by configuing `binutils` and `gcc` with `sysroot`.  Maybe we'll try that later.
