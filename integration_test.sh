#!/usr/bin/bash
# Generate helloworld executables for C and C++ with multiple platforms
set -euo pipefail
# rebuild the riscv compiler suite
#scripts/gcc_riscv.py
#scripts/gcc_x86_64.py
pushd examples
echo "Shutdown Bazel server to force reloading external modules"
bazel shutdown
bazel clean
bazel build --platforms=//platforms:riscv64 helloworld
file bazel-bin/helloworld
bazel build --platforms=//platforms:riscv64 helloworld++
file bazel-bin/helloworld++
bazel run --platforms=//platforms:x86_64 helloworld
file bazel-bin/helloworld
bazel run --platforms=//platforms:x86_64 helloworld++
file bazel-bin/helloworld++
popd
