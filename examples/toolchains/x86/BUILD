load(":cc_toolchain_config.bzl", "cc_toolchain_config")
load("//:variables.bzl", "OUTPUT_BASE")
package(default_visibility = ["//visibility:public"])

# These should match a dependency named in MODULE.bazel
SUITE_MODULE = "gcc_x86_64_suite"

# This is the gcc version, not the bazel gcc_x86_64_suite module version
SUITE_VERSION = "15.0.1"

# the binutils, gcc, and glibc configuration target
SUITE_TARGET = "x86_64-pc-linux-gnu"

# Bazel currently makes the imported module available at this file system location
PATH_TO_MODULE = OUTPUT_BASE + "/external/" + SUITE_MODULE + "+"


# compiler and linker need to know the imported location of sysroot
SYSROOT = "external/" + SUITE_MODULE + "+/"

# Generate the set of sandbox filesystem directories containing system include files
BUILTIN_INCLUDE_DIRS = [
    PATH_TO_MODULE + "/include",
    PATH_TO_MODULE + "/usr/include",
    PATH_TO_MODULE + "/" + SUITE_TARGET + "/include/c++/" + SUITE_VERSION,
    PATH_TO_MODULE + "/lib/gcc/" + SUITE_TARGET + "/" + SUITE_VERSION + "/include",
    PATH_TO_MODULE + "/lib/gcc/" + SUITE_TARGET + "/" + SUITE_VERSION + "/include-fixed",
]

# a generic x86_64 CPU 
constraint_value(
    name = "x86_64",
    constraint_setting = "@@platforms//cpu",
)

filegroup(
    name = "empty",
    srcs = [],
)

# Most compiler and linker actions depend on an imported gcc and local wrappers
filegroup(
    name = "gcc_x86_64_compiler_files",
    srcs =
        glob(["gcc-x86_64/imported/*"]) + [
            "@gcc_x86_64_suite//:compiler_files",
        ],
)

filegroup(
    name = "gcc_x86_64_objdump",
    srcs =
        [
            "gcc-x86_64/imported/objdump",
        ],
)

filegroup(
    name = 'gcc_x86_64_as',
    srcs = 
        [
            'gcc-x86_64/imported/as',
        ]
)

# currently selected with the x86_64 platform
toolchain(
    name = "x86_64-native",
    target_compatible_with = [
        ":x86_64",
    ],
    toolchain = ":x86_64-native-gcc",
    toolchain_type = "@bazel_tools//tools/cpp:toolchain_type",
)
cc_toolchain(
    name = "x86_64-native-gcc",
    all_files = ":gcc_x86_64_compiler_files",
    ar_files = ":gcc_x86_64_compiler_files",
    as_files = ":empty",
    compiler_files = ":gcc_x86_64_compiler_files",
    dwp_files = ":empty",
    linker_files = ":gcc_x86_64_compiler_files",
    objcopy_files = ":empty",
    strip_files = ":gcc_x86_64_compiler_files",
    supports_param_files = 0,
    toolchain_config = ":x86_64-native-gcc-config",
    toolchain_identifier = "x86_64-native-gcc",
)

cc_toolchain_config(
    name = "x86_64-native-gcc-config",
    abi_libc_version = ":empty",
    abi_version = ":empty",
    compile_flags = [
        "--sysroot=" + SYSROOT,
        "-Wall",
        "-march=native"
    ],
    compiler = "gcc",
    coverage_compile_flags = ["--coverage"],
    coverage_link_flags = ["--coverage"],
    cpu = "x86_64",
    # we really want the following to be constructed from $(output_base) or $(location ...)
    cxx_builtin_include_directories = BUILTIN_INCLUDE_DIRS,
    cxx_flags = [
        "-std=c++20",
        "-fno-rtti",
        ],
    dbg_compile_flags = ["-g"],
    host_system_name = ":empty",
    link_flags = [
    ],
    link_libs = [
        "{}/lib/libc.so.6".format(PATH_TO_MODULE),
        "{}/lib/libm.so.6".format(PATH_TO_MODULE),
        "{}/lib64/libstdc++.so.6".format(PATH_TO_MODULE),
    ],
    opt_compile_flags = [
        "-O3",
        "-DNDEBUG",
        "-ffunction-sections",
        "-fdata-sections",
    ],
    opt_link_flags = ["-Wl,--gc-sections"],
    supports_start_end_lib = False,
    target_libc = ":empty",
    target_system_name = ":empty",
    tool_paths = {
        "ar": "gcc-x86_64/imported/ar",
        "ld": ":empty",
        "cpp": "gcc-x86_64/imported/cpp",
        "gcc": "gcc-x86_64/imported/gcc",
        "dwp": ":empty",
        "gcov": ":empty",
        "nm": "gcc-x86_64/imported/nm",
        "objcopy": "gcc-x86_64/imported/objcopy",
        "objdump": "gcc-x86_64/imported/objdump",
        "strip": "gcc-x86_64/imported/strip",
    },
    toolchain_identifier = "x86_64-native-gcc",
    unfiltered_compile_flags = [
        "-fno-canonical-system-headers",
        "-Wno-builtin-macro-redefined",
        "-D__DATE__=\"redacted\"",
        "-D__TIMESTAMP__=\"redacted\"",
        "-D__TIME__=\"redacted\"",
    ],
)
