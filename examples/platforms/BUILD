package(default_visibility = ["//visibility:public"])

# a riscv userspace platform with a CPU supporting rva23 with vector instructions.
# In gcc machine architecture terms, march=rv64gcv
platform(
    name = "riscv64",
    constraint_values = [
        "//toolchains/riscv:riscv64",
    ],
)

# x86_64 platform for unit testing
platform(
    name = "x86_64",
    constraint_values = [
        "//toolchains/x86:x86_64",
    ],
)
