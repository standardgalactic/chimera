FROM alpine:3.20 AS builder

ENV TZ Etc/UTC

RUN <<SHELL sh
    set -ex
    apk update
    apk add --no-cache \
        ca-certificates=20240226-r0 \
        git=2.45.2-r0
    apk add --no-cache \
        python3-dev=3.12.3-r1
    apk add --no-cache \
        build-base=0.5-r3 \
        gdb=14.2-r1 \
        gdbm-dev=1.23-r1 \
        libbz2=1.0.8-r6 \
        libffi-dev=3.4.6-r0 \
        libncursesw=6.4_p20240420-r0 \
        openssl-dev=3.3.1-r0 \
        readline-dev=8.2.10-r0 \
        sqlite-dev=3.45.3-r1 \
        xz-dev=5.6.1-r3 \
        zlib-dev=1.3.1-r1
    apk cache clean
    rm -rf /var/cache/apk/*
SHELL

RUN git clone --depth 1 https://github.com/python/cpython.git /tmp/cpython
WORKDIR /tmp/cpython
RUN <<SHELL sh
    set -ex
    ./configure
    make -j3
    ./python -c 'import sys; assert "3.14" < sys.version < "3.15", sys.version'
    make install
SHELL

FROM alpine:3.20

COPY --from=builder /usr/local/bin/python3.14 /usr/local/bin/python3.14
COPY --from=builder /usr/local/lib/python3.14 /usr/local/lib/python3.14

ENV TZ Etc/UTC

COPY . /tmp

RUN <<SHELL sh
    set -ex
    apk update
    apk add --no-cache \
        gcc=13.2.1_git20240309-r0 \
        musl-dev=1.2.5-r0 \
        python3-dev=3.12.3-r1
    python3 -m venv /tmp/env
    /tmp/env/bin/pip install -r /tmp/tools/requirements.txt
    /tmp/env/bin/pip install -r /tmp/requirements.txt
    /tmp/env/bin/ansible-playbook /tmp/tools/boot.yml
    rm -rf /root/.ansible /root/.cache /tmp/* /var/tmp/*
    apk cache clean
    rm -rf /var/cache/apk/*
SHELL

USER github:github

ENV CC=clang \
    CMAKE_BUILD_TYPE=Debug \
    CMAKE_EXPORT_COMPILE_COMMANDS=YES \
    CTEST_PARALLEL_LEVEL=3 \
    CXX=clang++ \
    LDFLAGS="-lgcc_s"
