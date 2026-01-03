# generating a new compiler suite Bazel module

This file shows how to generate a new Bazel module encapsulating a GCC compiler suite.
For this example, we want to build from the stable releases of
`binutils`, `gcc`, and `glibc` for x86_64 and riscv architectures.

We'll use the x86_64 and riscv-64 compiler suite development tips as examples.  These will become the `gcc_x86_64_suite` and the `gcc_riscv_suite` Bazel Modules.
These modules will use Bazel module versioning, with a patch number following the GCC version number.  For the example below, we will be creating
`gcc_x86_64_suite` and `gcc_riscv_suite` version 15.2.0.0 using a snapshot of GCC 15.2.0 as the baseline source.  The Bazel version is 8.4.

The example use case for these crosscompiler tools is support of a RISC-V 64 bit network appliance, built with some AI or inference engine capabilities.  That means
the RISC-V toolchain is the dominant toolchain, with a closely-aligned x86_64 toolchain useful for unit tests and internal integration tests.

Toolchains run over kernels, importing quite a lot of include files and linker/loader data from the kernel build process.  We won't build a kernel from scratch to
get those `sysroot` files. Instead we will import them from Ubuntu 25 system images.

It takes several steps to generate each Bazel crosscompiler toolchain:

1. Git pull or clone sources for `binutils`, `gcc`, and `glibc`.  Detach the Git head to select `binutils-2_45`, `releases/gcc-15.2.0`, and `glibc-2.42` respectively.
   For this example, these are found under `/home2/vendor`.
2. Import sysroot files for a minimal server.  This takes several steps.  For the RISC-V case these are:
   1. Download installation media for [Ubuntu for RISC-V](https://cdimage.ubuntu.com/releases/25.04/release/ubuntu-25.04-live-server-riscv64.iso).
   2. Move it to `/opt/riscv_vm/ubuntu-25.04-live-server-riscv64.iso`.
   3. Start a new VM with this ISO, using a recent `u-boot.bin` to get it launched:
      ```console
      DIR=/opt/riscv_vm
      qemu-system-riscv64 \
         -machine virt -nographic -m 8192 -smp 4 \
         -kernel $DIR/u-boot.bin \
         -device virtio-net-device,netdev=eth0 -netdev user,id=eth0 \
         -device virtio-rng-pci \
         -drive file=$DIR/ubuntu-25.04-live-server-riscv64.iso,format=raw,if=virtio \
         -drive file=$DIR/disk,format=raw,if=virtio
      ```
   4. Complete the VM installation steps and reboot without the ISO image
      ```console
      DIR=/opt/riscv_vm
      QEMU_CPU=rv64,v=true,zba=true,zbb=true,zbc=true,zbkb=true,zbkc=true,zbkx=true,zvbb=true,zvbc=true,vlen=256,vext_spec=v1.0 \
      qemu-system-riscv64 -L $DIR/lib \
      -machine virt -cpu max,zfbfmin=false,zvfbfmin=false,zvfbfwma=false -nographic -m 8192 -smp 4 \
      -kernel $DIR/u-boot.bin \
      -device virtio-net-device,netdev=eth0 \
      -netdev user,id=eth0,hostfwd=tcp::5555-:22 \
      -device virtio-rng-pci \
      -drive file=$DIR/disk,format=raw,if=virtio
      ```
   5. Survey for key files connecting the kernel to `gcc` and `glibc`:
      ```console
      riscvm:/usr$ find . -name libc.so.6 -ls
         1545   1536 -rwxr-xr-x   1 root     root      1571096 Jul  9 16:42 ./lib/riscv64-linux-gnu/libc.so.6
      riscvm:/usr$ find . -name crt1.o -ls
         23101      4 -rw-r--r--   1 root     root         3592 Jul  9 16:42 ./lib/riscv64-linux-gnu/crt1.o
      riscvm:/usr$ find . -name stdio.h
      ./include/stdio.h
      ./include/riscv64-linux-gnu/bits/stdio.h
      ```
   6. Update and upgrade any installed Ubuntu packages
   7. Generate a tarball from the existing sysroot:
      ```console
      riscvm:/$ tar cJf ~/riscv_sysroot.tar.xz usr
      ```
   8. `scp` this to our host Linux system, and install it as `/opt/riscv`.
      Find and patch any full path name references buried within so files:
      ```console
      $ find . -name \*.so -size -10b -ls | grep -v '\->'
      21970344 4 -rw-r--r--  295 Jul  9 12:42 ./usr/lib/riscv64-linux-gnu/libc.so
      ```
3. Configure and compile those sources into `/home2/build_riscv`.
   The configuration step specifies intermediate install directory `/opt/riscv/sysroot`.
   1.  Clean the `binutils` build directory and configure with:
      ```console
      /home2/vendor/binutils-gdb/configure --prefix=/opt/riscv/sysroot \
        --with-sysroot=/opt/riscv/sysroot --target=riscv64-linux-gnu
      make -j4
      make install
      ```
   2. Some files are not exactly where the gcc build environment expects them, so add some links:
      ```console
      mkdir /opt/riscv/sysroot/lib/riscv64-linux-gnu
      ln /opt/riscv/sysroot/lib/libc.so.6 /opt/riscv/sysroot/lib/riscv64-linux-gnu/libc.so.6
      /opt/riscv/sysroot/usr/include$ ln -s riscv64-linux-gnu/asm asm
      ```
   3. Clean the gcc build directory and configure with:
      ```console
      /home2/vendor/gcc/configure --prefix=/opt/riscv/sysroot \
        --with-sysroot=/opt/riscv/sysroot --enable-languages=c,c++ --disable-multilib \
        --target=riscv64-linux-gnu
      make -j4
      make install
      ```
   4. Clean the glibc build directory and configure with:
      ```console
      /home2/vendor/glibc/configure --host=riscv64-linux-gnu --prefix=/opt/riscv/sysroot \
        CC=/opt/riscv/sysroot/bin/riscv64-linux-gnu-gcc LD=/opt/riscv/sysroot/bin/riscv64-linux-gnu-ld \
        AR=/opt/riscv/sysroot/bin/riscv64-linux-gnu-ar \
        --with-headers=/opt/riscv/sysroot/usr/include \
        --disable-multilib --enable-languages=c,c++
      make -j4
      make install
      ```
   5. Search for and replace any full paths with relative paths.  This mostly applies to sharable
      object files and some loader metadata files.  'libc.so` and `libm.so` are common files needing edits.
      ```console
      $ find . -name \*.so -size -10b -ls | grep -v '\->'
      21970344 4 -rw-r--r--  295 Jul  9 12:42 ./usr/lib/riscv64-linux-gnu/libc.so
      ```
      The file `libc.so` is a text file.  Edit the `GROUP` line to look like:
      ```text
      GROUP ( ./libc.so.6 ./libc_nonshared.a  AS_NEEDED ( ./ld-linux-riscv64-lp64d.so.1 ) )
      ```
   6. Test the linkages with commands like:
      ```console
      $ /opt/riscv/sysroot/bin/riscv64-linux-gnu-gcc examples/helloworld.c
      $ file a.out
      a.out: ELF 64-bit LSB executable, UCB RISC-V, RVC, double-float ABI, version 1 (SYSV), \
      dynamically linked, interpreter /lib/ld-linux-riscv64-lp64d.so.1, for GNU/Linux 4.15.0,
      with debug_info, not stripped
       /opt/riscv/sysroot/bin/riscv64-linux-gnu-gcc -lstdc++ examples/helloworld.cc
      $ file a.out
      a.out: ELF 64-bit LSB executable, UCB RISC-V, RVC, double-float ABI, version 1 (SYSV), \
      dynamically linked, interpreter /lib/ld-linux-riscv64-lp64d.so.1, for GNU/Linux 4.15.0,\
      with debug_info, not stripped
      ```
      The linkages most likely to fail involve `gcc` finding `as`, `ld`, and `collect2`, or the linker
      finding kernel-generated include files or dynamic loader files.

We now have a RISC-V crosscompiler installed on our local workstation.  The next steps collect
a subset of those crosscompiler files into portable Bazel modules.  Scripts like `scripts/gcc_riscv.py`
do most of that work.

1. Identify the subset of files in the intermediate install directories intended for the Bazel tarballs.
   These files are specified in python scripts like `script/gcc_riscv.py`.  The files and their locations depend
   on specific suite releases, so these scripts likely need to be updated.
2. Run the desired script to collect needed files, strip unnecessary debugging information, replace duplicates with hard links, and
   generate the compressed Bazel module tarballs.  The scripts will install the new Bazel modules (tarball plus metadata) under
   `/opt/bazel/bzlmod/`.Test the new modules to verify all desired files are present and nothing references host directories like `/usr/` or `/opt/riscv64`.
   This is usually an iterative process, especially making sure that all of the obscure files needed by the linker/loader are present
   and on a relative file path.39. Move the installation directory `/opt/riscv/` to `/opt/riscv_save`before exercising the new
   modules within Bazel.  This helps test hermeticity, so that `bazel build` can not easily find the local compiler suite components.

## Generate an x86_64 toolchain to match

A development shop might need three or more coordinated toolchains.  We have the first one, a crosscompiler toolchain ready to build
binaries for deployment.  The shop would also need at least one more toolchain, one to run on an integration server or developer's workstation
to test compilations, run unit tests, and fully mocked local integration tests.  Those toolchains likely run on an x86_64 hardware platform instead
of the riscv-64 hardware platform, and with a different sysroot configuration.  The compiler version and system library versions should be the
same.

For our example, we want an x86_64 toolchain with gcc 15.2, regardless of the native gcc version available on the integration server or the developer's
workstations.  Our sysroot can be copied - with pruning - from an existing server's `/usr` directory, where we clone a selection of `/usr/include` and
`/usr/lib64` into the new sysroot `/opt/x86_64`.

Building the x86_64 toolchain is similar to building the riscv64 toolchain, except there is no `target` option in the configuration.
File location within `/opt/x86_64/sysroot` is likely to differ, since this is not a crosscompiler build so much as a direct upgrade
to a single-platform sysroot.

## System Library Dependencies

Crosscompiler components expect to find a number of shared libraries at runtime.  If we want a portable
toolchain, we need to either provide these libraries separately or rebuild the crosscompiler for diverse host development
platforms.

We can survey these dependencies with commands like:

```console
$ for i in bin/riscv64-linux-gnu-ar bin/riscv64-linux-gnu-as bin/riscv64-linux-gnu-gcc bin/riscv64-linux-gnu-g++ \
           bin/riscv64-linux-gnu-cpp bin/riscv64-linux-gnu-ld bin/riscv64-linux-gnu-nm bin/riscv64-linux-gnu-objcopy \
           bin/riscv64-linux-gnu-objdump bin/riscv64-linux-gnu-strip \
           libexec/gcc/riscv64-linux-gnu/15.2.0/collect2 libexec/gcc/riscv64-linux-gnu/15.2.0/cc1plus;
  do ldd $i >> /tmp/ldd.log;
  done
```

After some cleanup we get the aggregate dependencies:

```text
/lib64/ld-linux-x86-64.so.2
linux-vdso.so.1
libc.so.6 => /lib64/libc.so.6
libgcc_s.so.1 => /lib64/libgcc_s.so.1
libm.so.6 => /lib64/libm.so.6
libstdc++.so.6 => /lib64/libstdc++.so.6
libgmp.so.10 => /lib64/libgmp.so.10
libisl.so.15 => /lib64/libisl.so.15
libmpc.so.3 => /lib64/libmpc.so.3
libmpfr.so.6 => /lib64/libmpfr.so.6
libzstd.so.1 => /lib64/libzstd.so.1
```

If we wanted to run this on an Ubuntu 24 development host we would likely run into a problem with `libisl`.
Fedora builds with SONAME (Sharable Object Name) 15, while Ubuntu names it 23.  This will be a problem if we
expect to crosscompile C++ RISC-V code on both Fedora and Ubuntu development hosts as well as a continuous integration
server.  The full solution is out of scope for this project.

A quick and dirty patch simply copies /lib64/libisl.so.15 and libisl.so.15.1.1 from the fedora system to /usr/lib/x86_64-linux-gnu/ on the Ubuntu system.  This allows compilation to complete, but generates a more local error:

`external/gcc_riscv_suite+/bin/../libexec/gcc/riscv64-linux-gnu/15.2.0/ld: cannot find crt1.o: No such file or directory`

## TODO

* [] Test with more complex compilations
* [] Understand and remove multiple versions of the same file, especially between `/usr/include` and `/include`
* [] Verify that the loader scripts are current and hermetic
* [] Document the search paths for complicated process invocations and include path searches, such as gcc -> ld -> loader scripts.