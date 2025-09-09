load(":gcc/cc_toolchain_config.bzl", "cc_toolchain_config")
load("//:variables.bzl", "OUTPUT_BASE")

package(default_visibility = ["//visibility:public"])

# These should match a dependency named in MODULE.bazel
SUITE_MODULE = "gcc_x86_64_suite"

# This is the gcc version, not the bazel gcc_x86_64_suite module version
SUITE_VERSION = "15.2.0"

# the binutils, gcc, and glibc configuration target
SUITE_TARGET = "x86_64-pc-linux-gnu"

# Bazel currently makes the imported module available at this file system location
PATH_TO_MODULE = OUTPUT_BASE + "/external/" + SUITE_MODULE + "+"

# compiler and linker need to know the imported location of sysroot
SYSROOT = "external/" + SUITE_MODULE + "+/"

# a generic x86_64 CPU
constraint_value(
    name = "x86_64",
    constraint_setting = "@@platforms//cpu",
)

filegroup(
    name = "empty",
    srcs = [],
)

filegroup(
    name = "objdump",
    srcs =
        [
            "gcc/wrappers/objdump",
        ],
)

filegroup(
    name = "as",
    srcs =
        [
            "gcc/wrappers/as",
        ],
)

# Most compiler and linker actions depend on an imported gcc, local wrappers, and loader scripts
filegroup(
    name = "compiler_files",
    srcs =
        glob(["gcc/wrappers/*"]) + [
            "gcc/elf_x86_64.xce",
            "gcc/elf_x86_64.xdce",
            "@gcc_x86_64_suite//:compiler_files",
        ],
)

cc_toolchain_config(name = "x86_64-gcc-config")

cc_toolchain(
    name = "x86_64-native-gcc",
    all_files = ":compiler_files",
    compiler_files = ":compiler_files",
    dwp_files = ":empty",
    linker_files = ":compiler_files",
    objcopy_files = ":empty",
    strip_files = ":compiler_files",
    supports_param_files = 0,
    toolchain_config = ":x86_64-gcc-config",
    toolchain_identifier = "x86_64-gcc",
)

# currently selected with the x86_64 platform
toolchain(
    name = "x86_64-native",
    exec_compatible_with = [
        "@@platforms//cpu:x86_64",
        "@@platforms//os:linux",
    ],
    target_compatible_with = [
        ":x86_64",
    ],
    toolchain = ":x86_64-native-gcc",
    toolchain_type = "@@bazel_tools//tools/cpp:toolchain_type",
)
