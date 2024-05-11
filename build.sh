#!/usr/bin/env sh

set -ex

git clean -dfx
rm -rf "${HOME}/.cargo"

git submodule update --init

curl -o rustup.sh https://sh.rustup.rs -sSf
chmod +x rustup.sh
./rustup.sh -y --no-modify-path
rm rustup.sh
set +ex
. "${HOME}/.cargo/env"
set -ex
rustup default stable

python3 tools/venv.py venv
set +ex
. venv/bin/activate
set -ex

for patch in "$(pwd)/patches"/*; do
    external="external/$(basename "${patch}")"
    git -C "${external}" clean -dfx
    git -C "${external}" restore .
    git -C "${external}" apply "${patch}"
done

cmake -DCMAKE_BUILD_TYPE=Release -B . -S .
make "-j$(nproc --all)"
