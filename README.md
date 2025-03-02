# chimera

[![Ansible Lint](https://github.com/asakatida/chimera/actions/workflows/ansible-lint.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/ansible-lint.yml)
[![CMake](https://github.com/asakatida/chimera/actions/workflows/cmake.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/cmake.yml)
[![Cmake Lint](https://github.com/asakatida/chimera/actions/workflows/cmakelint.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/cmakelint.yml)
[![CodeCov](https://github.com/asakatida/chimera/actions/workflows/codecov.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/codecov.yml)
[![CodeQL](https://github.com/asakatida/chimera/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/github-code-scanning/codeql)
[![Python](https://github.com/asakatida/chimera/actions/workflows/python.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/python.yml)
[![Requirements.txt](https://github.com/asakatida/chimera/actions/workflows/requirements-txt.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/requirements-txt.yml)
[![TruffleHog](https://github.com/asakatida/chimera/actions/workflows/trufflehog.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/trufflehog.yml)
[![Utf8 Generate](https://github.com/asakatida/chimera/actions/workflows/utf8-generate.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/utf8-generate.yml)
[![YamlLint](https://github.com/asakatida/chimera/actions/workflows/yamllint.yml/badge.svg)](https://github.com/asakatida/chimera/actions/workflows/yamllint.yml)

A forkable alternative Python3 interpreter.

## documentation

### compatibility

This fork tracks the latest cpython alpha spec for language features.  The stdlib can be cpython or pypy.

The threading model is different.  Garbage collection is a separate set of threads.  Also the method lookup model follows simpler rules.

### building/installing

The supported build process is cmake, ninja, and clang with support for c++23.  Default settings and target names are used.

### working on core

- [1 TOC](process/1_TOC.md) list of process documents

## forks

This is a list of forks that target compatibility with particular release versions of cpython.
