# Building a gcc16 toolchain

For this we want:

* gcc 16.1
* libc 2.43
* binutils 2.46.1

## Copy a Linux Ubuntu system root to the crosscompiler directory

We need a system root with bootstrap libraries and header files appropriate for
a kernel.  We'll use an Ubuntu 25.04 RISC-V vm and `apr update` to early August, 2026.

>Note: the directories usr/lib/{firmware,modules,snapd,llvm-18} can probably be excluded from
>      this tarfile, saving about 1.05GB of uncompressed files

```console
$ root@riscvm:/usr# tar cjf /tmp/usr.tz bin include lib libexec local sbin share src
$ scp /tmp/usr.tz thixotropist@10.0.2.2:/tmp
```

Clean out the /opt/riscv root and load it with the /usr files from the VM:

```console
$ sudo mkdir -p /opt/riscv
$ sudo rm -rf /opt/riscv/*
$ sudo chown thixotropist /opt/riscv
$ cd /opt/riscv
$ git init
$ cd usr
$ tar xf /tmp/usr.tz
$ cd ..
$ git add usr
$ git commit -m"load /usr from ubuntu 25.04"
$ git gc --aggressive
```

## Build and install binutils, gcc, and libc

```console
cd binutils-gdb
TARGET=riscv64-linux-gnu
PREFIX=/opt/riscv
/home2/vendor/binutils-gdb/configure --target=$TARGET --prefix=$PREFIX --with-sysroot --disable-nls --disable-werror
make -j4
make install
# commit this in /opt/riscv git repo

# edit /opt/riscv/usr/lib/riscv64-linux-gnu/libc.so to use relative paths, e.g.:
# GROUP ( ./libc.so.6 ./riscv64-linux-gnu/libc_nonshared.a  AS_NEEDED ( ./ld-linux-riscv64-lp64d.so.1 ) )
# and git commit
cd ../gcc
../../vendor/gcc/configure --target=$TARGET --prefix=$PREFIX --disable-nls --enable-languages=c,c++ --with-sysroot=$PREFIX --disable-multilib
make -j4
make install
/opt/riscv/bin/riscv64-linux-gnu-gcc --version
/opt/riscv/bin/riscv64-linux-gnu-g++ --version
# commit this in /opt/riscv git repo
cd ../glibc
/home2/vendor/glibc/configure --host=riscv64-linux-gnu --prefix=/opt/riscv CC=/opt/riscv/bin/riscv64-linux-gnu-gcc LD=/opt/riscv/bin/riscv64-linux-gnu-ld AR=/opt/riscv/bin/riscv64-linux-gnu-ar --with-sysroot=/opt/riscv --disable-multilib --enable-languages=c,c++ --disable-werror
make -j4
make install
# commit this in /opt/riscv git repo
# search for sharable object files with absolute paths, and make those relative paths
cd $PREFIX
find . -name \*.so -size -2b -ls
# correct /opt/riscv/lib/libc.so as we corrected /opt/riscv/usr/lib/riscv64-linux-gnu/libc.so
# and commit
```

## Test the local toolchain

```console
$ cd examples
$ /opt/riscv/bin/riscv64-linux-gnu-gcc helloworld.c
$ file a.out
a.out: ELF 64-bit LSB executable, UCB RISC-V, RVC, double-float ABI, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-riscv64-lp64d.so.1, for GNU/Linux 4.15.0, with debug_info, not stripped
$ readelf -A a.out
Attribute Section: riscv
File Attributes
  Tag_RISCV_stack_align: 16-bytes
  Tag_RISCV_arch: "rv64i2p1_m2p0_a2p1_f2p2_d2p2_c2p0_zicsr2p0_zifencei2p0_zmmul1p0_zaamo1p0_zalrsc1p0_zca1p0_zcd1p0"
# repeat with a c++ test case
$ /opt/riscv/bin/riscv64-linux-gnu-g++ helloworld.cc
$ file a.out
a.out: ELF 64-bit LSB executable, UCB RISC-V, RVC, double-float ABI, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux-riscv64-lp64d.so.1, for GNU/Linux 4.15.0, with debug_info, not stripped
$ readelf -A a.out
Attribute Section: riscv
File Attributes
  Tag_RISCV_stack_align: 16-bytes
  Tag_RISCV_arch: "rv64i2p1_m2p0_a2p1_f2p2_d2p2_c2p0_zicsr2p0_zifencei2p0_zmmul1p0_zaamo1p0_zalrsc1p0_zca1p0_zcd1p0"
```
