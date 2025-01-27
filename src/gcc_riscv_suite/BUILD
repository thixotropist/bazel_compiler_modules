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

filegroup(
    name = "lib",
    srcs = glob(["lib/gcc/riscv64-unknown-linux-gnu/{}/**".format(GCC_VERSION)]),
)

filegroup(
    name = "c++_std_includes",
    srcs = glob(["riscv64-unknown-linux-gnu/include/c++/{}/**".format(GCC_VERSION)]),
)

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
        "bin/riscv64-unknown-linux-gnu-readelf",
        "bin/riscv64-unknown-linux-gnu-strip",
        ":c++_std_includes",
        ":lib",
        ":libexec",
        ":std_includes",
        "@fedora_syslibs//:common_compiler_ldd_dependencies",
    ],
)
