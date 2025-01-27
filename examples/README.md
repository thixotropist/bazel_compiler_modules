This directory provides an example showing the use of several Bazel compiler modules.

Three modules are imported to provide a build and test environment for a RISCV 64 bit product based on
the [RISCV RCA 23](https://github.com/riscv/riscv-profiles/blob/main/src/rva23-profile.adoc) profile.

The primary components are:

* GCC compiler suites for riscv64 and x86_64, currently built from prereleased snapshots of GCC 15, binutils, and glibc.
  These are imported from a bzlmod repo (local file system, web server, NFS or CIFS server, ...) via the `MODULE.bazel` file.
* Crosscompiler toolchains that should be hermetic - use a minimum of host computer files so that binaries built are
  identical regardless of the host computer.  This greatly improves testing performance.
    * a riscv64 C and C++ toolchain with a default machine architecture supporting rva23 including a generic sysroot and standard libraries.
      This toolchain is named `//toolchains/riscv:riscv64-rva23` and registered in `MODULE.bazel`.  Default libraries and compiler/linker options
      are provided in the file `toolchains/riscv/BUILD`
    * an x86_64 C and C++ toolchain suitable for unit and local integration tests.
      This toolchain is named `//toolchains/x86:x86_64-native` and also registered
      in `MODULE.bazel`.  Default libraries and compiler/linker options
      are provided in the file `toolchains/x86/BUILD`
* System platforms describing the environment for which the toolchains can build appropriate binaries.  These are named on `bazel build` command lines
  and provide constraint tests that toolchains must meet.
    * `//platforms:riscv64` - A RISCV 64 bit CPU with a linux kernel and hardware support for the RVA23 instruction set extensions.  The platform must also
       provide libc, libm, and libstdc++.
    * `//platforms:x86_64` - An x86_64 CPU  with a linux kernel and similar versions of libc, libm, and libstdc++

## Usage

Programs are built and run for local unit testing with commands like:

```console
$ bazel build --platforms=//platforms:x86_64 helloworld helloworld++
INFO: Analyzed 2 targets (0 packages loaded, 0 targets configured).
INFO: Found 2 targets...
INFO: Elapsed time: 0.065s, Critical Path: 0.00s
INFO: 1 process: 1 internal.
INFO: Build completed successfully, 1 total action

$ bazel run --platforms=//platforms:x86_64 helloworld
INFO: Analyzed target //:helloworld (0 packages loaded, 0 targets configured).
INFO: Found 1 target...
Target //:helloworld up-to-date:
  bazel-bin/helloworld
INFO: Elapsed time: 0.056s, Critical Path: 0.00s
INFO: 1 process: 1 internal.
INFO: Build completed successfully, 1 total action
INFO: Running command line: bazel-bin/helloworld
Hello World!

$ bazel run --platforms=//platforms:x86_64 helloworld++
INFO: Analyzed target //:helloworld++ (0 packages loaded, 0 targets configured).
INFO: Found 1 target...
Target //:helloworld++ up-to-date:
  bazel-bin/helloworld++
INFO: Elapsed time: 0.057s, Critical Path: 0.00s
INFO: 1 process: 1 internal.
INFO: Build completed successfully, 1 total action
INFO: Running command line: bazel-bin/helloworld++
Hello World!
```

We want a portable x86_64 toolchain so that local developers and shared test servers all
use the same libraries and compiler options.

The same programs can be built for the target riscv64 system with:

```console
$ bazel build --platforms=//platforms:riscv64 helloworld helloworld++
WARNING: Build option --platforms has changed, discarding analysis cache (this can be expensive, see https://bazel.build/advanced/performance/iteration-speed).
INFO: Analyzed 2 targets (0 packages loaded, 3250 targets configured).
INFO: Found 2 targets...
INFO: Elapsed time: 0.686s, Critical Path: 0.54s
INFO: 7 processes: 4 action cache hit, 3 internal, 4 linux-sandbox.
INFO: Build completed successfully, 7 total actions

$ file bazel-bin/helloworld
bazel-bin/helloworld: ELF 64-bit LSB executable, UCB RISC-V, RVC, double-float ABI, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-riscv64-lp64d.so.1, for GNU/Linux 4.15.0, not stripped

$ readelf -A bazel-bin/helloworld
Attribute Section: riscv
File Attributes
  Tag_RISCV_stack_align: 16-bytes
  Tag_RISCV_arch: "rv64i2p1_m2p0_a2p1_f2p2_d2p2_c2p0_v1p0_zicond1p0_zicsr2p0_zifencei2p0_zimop1p0_zmmul1p0_zaamo1p0_zalrsc1p0_zawrs1p0_zfa1p0_zfhmin1p0_zca1p0_zcb1p0_zcd1p0_zcmop1p0_zvbb1p0_zve32f1p0_zve32x1p0_zve64d1p0_zve64f1p0_zve64x1p0_zvfhmin1p0_zvkb1p0_zvkg1p0_zvkn1p0_zvkned1p0_zvkng1p0_zvknhb1p0_zvks1p0_zvksed1p0_zvksg1p0_zvksh1p0_zvkt1p0_zvl128b1p0_zvl32b1p0_zvl64b1p0"

$ file bazel-bin/helloworld++
bazel-bin/helloworld++: ELF 64-bit LSB executable, UCB RISC-V, RVC, double-float ABI, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-riscv64-lp64d.so.1, for GNU/Linux 4.15.0, not stripped

$ readelf -A bazel-bin/helloworld++
Attribute Section: riscv
File Attributes
  Tag_RISCV_stack_align: 16-bytes
  Tag_RISCV_arch: "rv64i2p1_m2p0_a2p1_f2p2_d2p2_c2p0_v1p0_zicond1p0_zicsr2p0_zifencei2p0_zimop1p0_zmmul1p0_zaamo1p0_zalrsc1p0_zawrs1p0_zfa1p0_zfhmin1p0_zca1p0_zcb1p0_zcd1p0_zcmop1p0_zvbb1p0_zve32f1p0_zve32x1p0_zve64d1p0_zve64f1p0_zve64x1p0_zvfhmin1p0_zvkb1p0_zvkg1p0_zvkn1p0_zvkned1p0_zvkng1p0_zvknhb1p0_zvks1p0_zvksed1p0_zvksg1p0_zvksh1p0_zvkt1p0_zvl128b1p0_zvl32b1p0_zvl64b1p0"
```

Note the `Tag_RISCV_arch` metadata - these executables are built assuming a specific set of instruction set extensions is present, including vector instructions version 1.0.
