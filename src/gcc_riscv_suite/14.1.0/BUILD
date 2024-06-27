package(default_visibility = ["//visibility:public"])

# Assign names to different crosscompiler components

filegroup(
    name = "std_includes",
    srcs = glob(["usr/include/**"]),
)

filegroup(
    name = "riscv64_libexec",
    srcs = glob(["libexec/gcc/riscv64-unknown-linux-gnu/14.1.0/**"]),
)

filegroup(
    name = "riscv64_lib",
    srcs = glob(["lib/riscv64-unknown-linux-gnu/*"]) +
        glob(["lib/gcc/riscv64-unknown-linux-gnu/14/*"])
)

filegroup(
    name = "c++_std_includes",
    srcs = glob(["riscv64-unknown-linux-gnu/include/c++/14.1.0/*"])
)

filegroup(
    name = "compiler_files",
    srcs =  [
                ":std_includes",
                ":c++_std_includes",
                ":riscv64_libexec",
                ":riscv64_lib",
                "bin/riscv64-unknown-linux-gnu-cpp",
                "bin/riscv64-unknown-linux-gnu-gcc",
                "bin/riscv64-unknown-linux-gnu-as",
                "bin/riscv64-unknown-linux-gnu-ar",
                "bin/riscv64-unknown-linux-gnu-ld",
                "bin/riscv64-unknown-linux-gnu-ld.bfd",
                "bin/riscv64-unknown-linux-gnu-ranlib",
                "bin/riscv64-unknown-linux-gnu-objdump",
                "bin/riscv64-unknown-linux-gnu-strip",
                "@fedora_syslibs//:common_compiler_ldd_dependencies",
                ]
)
