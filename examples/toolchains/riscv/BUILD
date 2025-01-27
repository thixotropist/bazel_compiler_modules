load(":cc_toolchain_config.bzl", "cc_toolchain_config")
load("//:variables.bzl", "OUTPUT_BASE")
package(default_visibility = ["//visibility:public"])

# These should match a dependency named in MODULE.bazel
SUITE_MODULE = "gcc_riscv_suite"

# This is the gcc version, not the bazel gcc_riscv_suite module version
SUITE_VERSION = "15.0.1"

# the binutils, gcc, and glibc configuration target
SUITE_TARGET = "riscv64-unknown-linux-gnu"

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

# a generic RISCV 64 hart supporting the rva23 ISA profile
constraint_value(
    name = "riscv64",
    constraint_setting = "@@platforms//cpu",
)

filegroup(
    name = "empty",
    srcs = [],
)

# Most compiler and linker actions depend on an imported gcc and local wrappers
filegroup(
    name = "gcc_riscv64_compiler_files",
    srcs =
        glob(["gcc-riscv/imported/*"]) + [
            "@gcc_riscv_suite//:compiler_files",
        ],
)

filegroup(
    name = "gcc_riscv_objdump",
    srcs =
        [
            "gcc-riscv/imported/objdump",
        ],
)

filegroup(
    name = 'gcc_riscv_as',
    srcs = 
        [
            'gcc-riscv/imported/as',
        ]
)

# currently selected with the riscv64 platform
toolchain(
    name = "riscv64-rva23",
    target_compatible_with = [
        ":riscv64",
    ],
    toolchain = ":riscv64-rva23-gcc",
    toolchain_type = "@bazel_tools//tools/cpp:toolchain_type",
)
cc_toolchain(
    name = "riscv64-rva23-gcc",
    all_files = ":gcc_riscv64_compiler_files",
    ar_files = ":gcc_riscv64_compiler_files",
    as_files = ":empty",
    compiler_files = ":gcc_riscv64_compiler_files",
    dwp_files = ":empty",
    linker_files = ":gcc_riscv64_compiler_files",
    objcopy_files = ":empty",
    strip_files = ":gcc_riscv64_compiler_files",
    supports_param_files = 0,
    toolchain_config = ":riscv64-rva23-gcc-config",
    toolchain_identifier = "riscv64-rva23-gcc",
)

# This configuration enables the RVA23 profile's mandatory and optional instructions
cc_toolchain_config(
    name = "riscv64-rva23-gcc-config",
    abi_libc_version = ":empty",
    abi_version = ":empty",
    compile_flags = [
        "--sysroot=" + SYSROOT,
        "-Wall",
        "-march=rv64gcv_zfhmin_zvfhmin_zvbb_zicond_zimop_zcmop_zcb_zfa_zawrs_zvkng_zvksg"
    ],
    compiler = "gcc",
    coverage_compile_flags = ["--coverage"],
    coverage_link_flags = ["--coverage"],
    cpu = "riscv64",
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
        "{}/{}/lib/libstdc++.so.6".format(PATH_TO_MODULE, SUITE_TARGET),
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
        "ar": "gcc-riscv/imported/ar",
        "ld": ":empty",
        "cpp": "gcc-riscv/imported/cpp",
        "gcc": "gcc-riscv/imported/gcc",
        "dwp": ":empty",
        "gcov": ":empty",
        "nm": "gcc-riscv/imported/nm",
        "objcopy": "gcc-riscv/imported/objcopy",
        "objdump": "gcc-riscv/imported/objdump",
        "strip": "gcc-riscv/imported/strip",
    },
    toolchain_identifier = "riscv64-rva23-gcc",
    unfiltered_compile_flags = [
        "-fno-canonical-system-headers",
        "-Wno-builtin-macro-redefined",
        "-D__DATE__=\"redacted\"",
        "-D__TIMESTAMP__=\"redacted\"",
        "-D__TIME__=\"redacted\"",
    ],
)
