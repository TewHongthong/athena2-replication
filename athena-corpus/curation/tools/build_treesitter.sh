#!/usr/bin/env bash
# Build the shared library that tsbind.py loads (tree-sitter runtime + Java/C#/TypeScript/TSX/JavaScript/C++ grammars).
# Needs: git, gcc, network access to github.com.  Linux / WSL / macOS(untested).  Output: <curation dir>/libtsall.so
# Exact commits used for the published benchmark (pinned below):
#   tree-sitter            dcdc8cc55e5dfedfc858080835f153999a29ec40 (2026-09-24)
#   tree-sitter-java       e10607b45ff745f5f876bfa3e94fbcc6b44bdc11 (2025-09-14)
#   tree-sitter-c-sharp    9150f7d56bb47f1a809fa23623f1ba1413e93fa9 (2026-07-15)
#   tree-sitter-typescript 75b3874edb2dc714fb1fd77a32013d0f8699989f (2025-01-30)
#   tree-sitter-javascript 58404d8cf191d69f2674a8fd507bd5776f46cb11 (2025-09-14)
# Athena Vol. 2 addition (pinned 2026-10-14; the five lines above are unchanged from Vol. 1):
#   tree-sitter-cpp        c009222808634c1014f82438d4883753516a2c24 (2026-09-17; untagged, newer than release v0.23.4 of 2024-11-11; parser ABI 15)
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
W="${1:-$(mktemp -d)}"; mkdir -p "$W"; cd "$W"
fetch() { # repo sha
  mkdir -p "$1" && cd "$1" && git init -q && git remote add origin "https://github.com/tree-sitter/$1" \
    && git fetch -q --depth 1 origin "$2" && git checkout -q FETCH_HEAD && cd ..
}
fetch tree-sitter            dcdc8cc55e5dfedfc858080835f153999a29ec40
fetch tree-sitter-java       e10607b45ff745f5f876bfa3e94fbcc6b44bdc11
fetch tree-sitter-c-sharp    9150f7d56bb47f1a809fa23623f1ba1413e93fa9
fetch tree-sitter-typescript 75b3874edb2dc714fb1fd77a32013d0f8699989f
fetch tree-sitter-javascript 58404d8cf191d69f2674a8fd507bd5776f46cb11
fetch tree-sitter-cpp        c009222808634c1014f82438d4883753516a2c24
mkdir -p build && cd build
CF="-O2 -fPIC -std=c11"
gcc -O2 -fPIC -std=gnu11 -D_DEFAULT_SOURCE -c ../tree-sitter/lib/src/lib.c -I../tree-sitter/lib/include -I../tree-sitter/lib/src -o runtime.o
gcc $CF -c ../tree-sitter-java/src/parser.c -I../tree-sitter-java/src -o java_parser.o
gcc $CF -c ../tree-sitter-c-sharp/src/parser.c -I../tree-sitter-c-sharp/src -o cs_parser.o
gcc $CF -c ../tree-sitter-c-sharp/src/scanner.c -I../tree-sitter-c-sharp/src -o cs_scanner.o
T=../tree-sitter-typescript
gcc $CF -c $T/typescript/src/parser.c -I$T/typescript/src -o ts_parser.o
gcc $CF -c $T/typescript/src/scanner.c -I$T/typescript/src -I$T/common -o ts_scanner.o
gcc $CF -c $T/tsx/src/parser.c -I$T/tsx/src -o tsx_parser.o
gcc $CF -c $T/tsx/src/scanner.c -I$T/tsx/src -I$T/common -o tsx_scanner.o
gcc $CF -c ../tree-sitter-javascript/src/parser.c -I../tree-sitter-javascript/src -o js_parser.o
gcc $CF -c ../tree-sitter-javascript/src/scanner.c -I../tree-sitter-javascript/src -o js_scanner.o
gcc $CF -c ../tree-sitter-cpp/src/parser.c -I../tree-sitter-cpp/src -o cpp_parser.o
gcc $CF -c ../tree-sitter-cpp/src/scanner.c -I../tree-sitter-cpp/src -o cpp_scanner.o
gcc -shared -o "$HERE/libtsall.so" *.o
echo "built $HERE/libtsall.so"
