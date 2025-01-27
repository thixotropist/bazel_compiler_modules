package(default_visibility = ["//visibility:public"])

GCC_VERSION = "15.0.1"

# Assign names to different crosscompiler components

filegroup(
    name = "std_includes",
    srcs = glob(["usr/include/**"]),
)

filegroup(
    name = "x86_64_libexec",
    srcs = glob(["libexec/gcc/x86_64-pc-linux-gnu/{}/**".format(GCC_VERSION)]),
)

filegroup(
    name = "x86_64_lib",
    srcs = ["lib/libc.so.6",
            "lib/libm.so.6",
            "lib64/libstdc++.so.6",
            "lib64/libstdc++.so.6.0.34",
    ] +
    glob(["lib/gcc/x86_64-pc-linux-gnu/{}/**".format(GCC_VERSION)])
)

filegroup(
    name = "c++_std_includes",
    srcs = glob(["include/c++/{}/*".format(GCC_VERSION)])
)

filegroup(
    name = "compiler_files",
    srcs =  [
        "bin/as",
        "bin/ar",
        "bin/cpp",
        "bin/gcc",
        "bin/ld",
        "bin/ld.bfd",
		"bin/objdump",
        "bin/ranlib",
		"bin/strip",
        "bin/readelf",
        ":c++_std_includes",
        ":x86_64_lib",
        ":x86_64_libexec",
        ":std_includes",
        "@fedora_syslibs//:common_compiler_ldd_dependencies",
    ]
)
