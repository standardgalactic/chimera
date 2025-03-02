#!/usr/bin/env sh

set -ex

cd "$(git rev-parse --show-toplevel || true)"

tools/cmake.sh "$1"

python tools/ninja.py "$1"
python tools/ninja.py "$1" test
python tools/ninja.py "$1" check-stat
python tools/ninja.py "$1" corpus
python tools/ninja.py "$1" spec
