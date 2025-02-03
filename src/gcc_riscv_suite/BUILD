package(default_visibility = ["//visibility:public"])

GCC_VERSION = "15.0.1"

SUITE_TARGET = "riscv64-unknown-linux-gnu"

TARGET_INC_DIR = SUITE_TARGET + "/include/"

TARGET_LIB_DIR = SUITE_TARGET + "/lib/"

TARGET_BIN_DIR = SUITE_TARGET + "/bin/"

BIN_TARGET_PREFIX = "bin/" + SUITE_TARGET + "-"

# Assign names to different crosscompiler components

filegroup(
    name = "std_includes",
    srcs = glob([
        "usr/include/**",
        "include/**",
    ]),
)

filegroup(
    name = "libexec",
    srcs = glob(["libexec/gcc/{}/{}/**".format(SUITE_TARGET, GCC_VERSION)]),
)

filegroup(
    name = "lib",
    srcs = glob(["lib/gcc/{}/{}/**".format(SUITE_TARGET, GCC_VERSION)]) + [
        "lib/gcc/crt1.o",
        "lib/crti.o",
        "lib/crtn.o",
        "lib/libc.so",
        "lib/libc.so.6",
        "lib/libm.so",
        "lib/libm.so.6",
        "lib/libc_nonshared.a",
        "lib/ld-linux-riscv64-lp64d.so.1",
        TARGET_LIB_DIR + "libgcc_s.so",
        TARGET_LIB_DIR + "libgcc_s.so.1",
        TARGET_LIB_DIR + "libstdc++.so",
        TARGET_LIB_DIR + "libstdc++.so.6",
        TARGET_LIB_DIR + "libstdc++.so.6.0.34",
    ],
)

filegroup(
    name = "c++_std_includes",
    srcs = glob([TARGET_INC_DIR + "c++/{}/**".format(GCC_VERSION)]),
)

# Note that binutils executables have a different naming convention and location than GCC executables
filegroup(
    name = "compiler_files",
    srcs = [
        # binutils files
        TARGET_BIN_DIR + "ar",
        TARGET_BIN_DIR + "as",
        TARGET_BIN_DIR + "ld",
        TARGET_BIN_DIR + "ld.bfd",
        TARGET_BIN_DIR + "objdump",
        TARGET_BIN_DIR + "ranlib",
        TARGET_BIN_DIR + "readelf",
        TARGET_BIN_DIR + "strip",
        # compiler files
        BIN_TARGET_PREFIX + "cpp",
        BIN_TARGET_PREFIX + "gcc",
        ":c++_std_includes",
        ":lib",
        ":libexec",
        ":std_includes",
        # system sharable libraries used by compiler
        "@fedora_syslibs//:common_compiler_ldd_dependencies",
    ],
)
