# chimera

[![Black](https://github.com/asakatida/chimera/actions/workflows/black.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/black.yml) [![ClangFormat](https://github.com/asakatida/chimera/actions/workflows/clang-format.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/clang-format.yml) [![ClangTidy](https://github.com/asakatida/chimera/actions/workflows/clang-tidy.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/clang-tidy.yml) [![CMake](https://github.com/asakatida/chimera/actions/workflows/cmake.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/cmake.yml) [![Isort](https://github.com/asakatida/chimera/actions/workflows/isort.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/isort.yml) [![MyPy](https://github.com/asakatida/chimera/actions/workflows/mypy.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/mypy.yml) [![Pylama](https://github.com/asakatida/chimera/actions/workflows/pylama.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/pylama.yml) [![Shellcheck](https://github.com/asakatida/chimera/actions/workflows/shellcheck.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/shellcheck.yml)

A forkable alternative Python3 interpreter.

## documentation

### compatibility

This fork tracks the latest cpython alpha spec for language features.  The stdlib can be cpython or pypy.

The threading model is different.  Garbage collection is a separate set of threads.  Also the method lookup model follows simpler rules.

### building/installing

The supported build process is cmake, ninja, and clang with support for c++20.  Default settings and target names are used.

### working on core

- [1 TOC](process/1_TOC.md) list of process documents

## forks

This is a list of forks that target compatibility with particular release versions of cpython.
