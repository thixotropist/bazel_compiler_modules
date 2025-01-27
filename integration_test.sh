#!/usr/bin/bash

set -euo pipefail
pushd examples
bazel clean
bazel build --platforms=//platforms:riscv64 helloworld helloworld++
file bazel-bin/helloworld
file bazel-bin/helloworld++
bazel run --platforms=//platforms:x86_64 helloworld
bazel run --platforms=//platforms:x86_64 helloworld++
popd
