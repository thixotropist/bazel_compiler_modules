package(default_visibility = ["//visibility:public"])

# Assign names to different crosscompiler components

filegroup(
    name = "std_includes",
    srcs = glob(["usr/include/**"]),
)

filegroup(
    name = "x86_64_libexec",
    srcs = glob(["libexec/gcc/x86_64-pc-linux-gnu/14.1.0/**"]),
)

filegroup(
    name = "x86_64_lib",
    srcs = glob(["lib/gcc/x86_64-pc-linux-gnu/14.1.0/**"])
)

filegroup(
    name = "c++_std_includes",
    srcs = glob(["x86_64-pc-linux-gnu/include/c++/14.1.0/*"])
)

filegroup(
    name = "compiler_files",
    srcs =  [
                ":std_includes",
                ":c++_std_includes",
                ":x86_64_libexec",
                ":x86_64_lib",
                "bin/cpp",
                "bin/gcc",
                "bin/as",
                "bin/ar",
                "bin/ld",
                "bin/ld.bfd",
                "bin/ranlib",
		"bin/objdump",
		"bin/strip",
                "@fedora_syslibs//:common_compiler_ldd_dependencies",
                ]
)
