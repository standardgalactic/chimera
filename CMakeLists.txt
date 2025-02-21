cmake_minimum_required(VERSION 3.19 FATAL_ERROR)
project(
  chimera
  VERSION 1.0.0
  LANGUAGES CXX)

set(
  CMAKE_CXX_FLAGS_COVERAGE
  -O0 -DNDEBUG
  -fcoverage-mapping
  -fprofile-instr-generate
  -mllvm
  -runtime-counter-relocation
  CACHE STRING
  "Flags used by the C++ compiler during coverage builds.")

set(CMAKE_CXX_STANDARD 23)

if(MSVC)
  add_compile_options(/W4 /WX)
else()
  if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    add_compile_options(
      -Wno-c++11-extensions
      -Wno-c++17-extensions
      -Wno-c++98-compat-pedantic)
  endif()
  add_compile_options(
    -Wno-date-time
    -Wno-padded)
endif()

enable_testing()

include(CTest)

add_library(
  chimera-grammar
  OBJECT
  library/asdl/parse_expression_istream.cpp
  library/asdl/parse_interactive_istream.cpp
  library/asdl/parse_module_istream.cpp
  library/grammar/input.cpp)

target_include_directories(chimera-grammar PUBLIC library stdlib)

target_include_directories(
  chimera-grammar
  SYSTEM PUBLIC
  external/GSL/include
  external/metal/include
  external/operators/include
  external/PEGTL/include
  oxidation)

file(GLOB_RECURSE NUMBER_SOURCES "*.rs")
add_custom_command(
  OUTPUT
  ${CMAKE_SOURCE_DIR}/oxidation/number-rust.hpp
  ${CMAKE_SOURCE_DIR}/oxidation/number/target/release/libnumber.a
  COMMAND
  cargo build --release
  WORKING_DIRECTORY
  ${CMAKE_SOURCE_DIR}/oxidation/number
  DEPENDS
  ${NUMBER_SOURCES})
add_custom_target(
  chimera-number-header
  DEPENDS
  ${CMAKE_SOURCE_DIR}/oxidation/number-rust.hpp)
add_library(number STATIC IMPORTED GLOBAL)
set_target_properties(
  number
  PROPERTIES
  IMPORTED_LOCATION
  ${CMAKE_SOURCE_DIR}/oxidation/number/target/release/libnumber.a)

add_library(
  chimera-core
  OBJECT
  library/object/number/number.cpp
  library/object/object.cpp
  library/virtual_machine/bin_evaluator.cpp
  library/virtual_machine/bool_evaluator.cpp
  library/virtual_machine/call_evaluator.cpp
  library/virtual_machine/del_evaluator.cpp
  library/virtual_machine/evaluator.cpp
  library/virtual_machine/garbage.cpp
  library/virtual_machine/get_evaluator.cpp
  library/virtual_machine/global_context.cpp
  library/virtual_machine/process_context.cpp
  library/virtual_machine/push_stack.cpp
  library/virtual_machine/set_evaluator.cpp
  library/virtual_machine/slice_evaluator.cpp
  library/virtual_machine/thread_context.cpp
  library/virtual_machine/to_bool_evaluator.cpp
  library/virtual_machine/tuple_evaluator.cpp
  library/virtual_machine/unary_evaluator.cpp
  stdlib/builtins/builtins.cpp
  stdlib/importlib/importlib.cpp
  stdlib/marshal/marshal.cpp
  stdlib/sys/sys.cpp)

target_include_directories(chimera-core PUBLIC library stdlib)

target_include_directories(
  chimera-core
  SYSTEM PUBLIC
  external/GSL/include
  external/metal/include
  external/operators/include
  oxidation)

add_dependencies(chimera-core chimera-number-header)

add_library(
  libchimera
  include/chimera.h
  library/c-api/chimera.cpp)

target_include_directories(
  libchimera
  SYSTEM PUBLIC
  include
  external/GSL/include)

set_target_properties(libchimera PROPERTIES OUTPUT_NAME "chimera")

add_executable(chimera source/main.cpp)

target_link_libraries(
  chimera
  chimera-core
  chimera-grammar
  number)

add_subdirectory(external/Catch EXCLUDE_FROM_ALL)
include(CatchShardTests)

foreach(FUZZ_TESTS_IDX RANGE 1020)
  list(
    APPEND
    FUZZ_TESTS
    ${CMAKE_BINARY_DIR}/generated/fuzz-${FUZZ_TESTS_IDX}.cpp)
endforeach()

add_custom_command(
  OUTPUT
  ${FUZZ_TESTS}
  COMMAND
  python tools/generate_fuzz.py ${FUZZ_TESTS}
  WORKING_DIRECTORY
  ${CMAKE_SOURCE_DIR}
  DEPENDS
  tools/generate_fuzz.py
  external/big-list-of-naughty-strings/blns.base64.json
  unit_tests/fuzz/cases.json)

add_executable(
  unit-test
  unit_tests/fuzz/cases.cpp
  unit_tests/grammar/expression.cpp
  unit_tests/grammar/grammar.cpp
  unit_tests/grammar/identifier.cpp
  unit_tests/grammar/number_parse.cpp
  unit_tests/grammar/number.cpp
  unit_tests/grammar/statement.cpp
  unit_tests/number/number.cpp
  unit_tests/virtual_machine/fuzz.cpp
  unit_tests/virtual_machine/parse.cpp
  unit_tests/virtual_machine/trace.cpp
  unit_tests/virtual_machine/virtual_machine.cpp
  ${FUZZ_TESTS})

target_include_directories(
  unit-test
  PUBLIC
  library
  stdlib
  unit_tests)

target_include_directories(
  unit-test
  SYSTEM PUBLIC
  external/Catch/src
  external/json/include
  external/PEGTL/include
  oxidation)

target_link_libraries(
  unit-test
  Catch2WithMain
  chimera-core
  chimera-grammar
  number
  pthread)

catch_add_sharded_tests(unit-test SHARD_COUNT 1021)

add_custom_target(
  check-stat
  perf stat ./unit-test
  DEPENDS unit-test
  VERBATIM)

add_custom_target(corpus)
add_custom_target(fuzzers)
add_custom_target(regression)

if(
  CMAKE_CXX_COMPILER_ID MATCHES "Clang" AND
  NOT CMAKE_CXX_COMPILER_ID MATCHES "AppleClang")
  set(
    FUZZ_CXXFLAGS
    -fsanitize-coverage=no-prune
    -fsanitize-coverage=trace-cmp
    -fsanitize-coverage=trace-div
    -fsanitize-coverage=trace-gep
    -fsanitize-coverage=trace-loads
    -fsanitize-coverage=trace-stores
    -fsanitize=fuzzer)
  add_library(chimera-fuzz OBJECT unit_tests/fuzz/cases.cpp)
  target_compile_options(
    chimera-fuzz
    PUBLIC
    ${FUZZ_CXXFLAGS})
  target_include_directories(
    chimera-fuzz
    PUBLIC
    library
    stdlib
    unit_tests)
  target_include_directories(
    chimera-fuzz
    SYSTEM PUBLIC
    external/GSL/include
    external/metal/include
    external/operators/include
    external/PEGTL/include
    oxidation)
  set(
    FUZZERS
    ellipsis
    expression
    false
    interactive
    keywords
    module
    name
    none
    number
    statement
    string
    true
    vm
    vm-expression
    vm-interact)
  foreach(fuzzer IN LISTS FUZZERS)
    add_executable(fuzz-${fuzzer} unit_tests/fuzz/target-${fuzzer}.cpp)
    target_compile_options(
      fuzz-${fuzzer}
      PUBLIC
      ${FUZZ_CXXFLAGS})
    target_include_directories(fuzz-${fuzzer} PUBLIC unit_tests)
    target_include_directories(
      fuzz-${fuzzer}
      SYSTEM PUBLIC
      external/PEGTL/include)
    target_link_libraries(
      fuzz-${fuzzer}
      chimera-core
      chimera-fuzz
      chimera-grammar
      number
      pthread
      ${FUZZ_CXXFLAGS}
      -rtlib=compiler-rt)
    add_custom_target(
      corpus-${fuzzer}
      python ${CMAKE_SOURCE_DIR}/tools/fuzz.py ${fuzzer}
      ${CMAKE_SOURCE_DIR}/unit_tests/fuzz/dictionaries/${fuzzer}.dict
      ${CMAKE_SOURCE_DIR}/unit_tests/fuzz/corpus
      DEPENDS fuzz-${fuzzer}
      VERBATIM)
    add_custom_target(
      regression-${fuzzer}
      python ${CMAKE_SOURCE_DIR}/tools/regression.py
      ${CMAKE_BINARY_DIR}
      ${fuzzer}
      DEPENDS fuzz-${fuzzer}
      VERBATIM)
    add_dependencies(corpus corpus-${fuzzer})
    add_dependencies(fuzzers fuzz-${fuzzer})
    add_dependencies(regression regression-${fuzzer})
  endforeach()
endif()

add_executable(bnf2abnf tools/bnf2abnf.cpp)

target_include_directories(bnf2abnf PUBLIC library)

target_include_directories(
  bnf2abnf
  SYSTEM PUBLIC
  external/GSL/include
  external/metal/include
  external/PEGTL/include)

add_library(modules-tools OBJECT tools/modules/modules.cpp)

target_include_directories(modules-tools PUBLIC library tools)

target_include_directories(
  modules-tools
  SYSTEM PUBLIC
  external/GSL/include
  external/metal/include
  external/operators/include)

add_custom_target(modules)

set(
  REGEN_MODULES
  builtins
  importlib)
foreach(regen_module IN LISTS REGEN_MODULES)
  add_executable(${regen_module} tools/modules/${regen_module}.cpp)
  target_link_libraries(
    ${regen_module}
    modules-tools
    chimera-core
    chimera-grammar
    number
    pthread)
  add_dependencies(modules ${regen_module})
endforeach()

add_custom_target(
  spec
  chimera -m test --multiprocess 3
  DEPENDS chimera
  VERBATIM)

add_custom_target(
  spec-stat
  perf stat ./chimera -m test --multiprocess 3
  DEPENDS chimera
  VERBATIM)

install(
  TARGETS chimera libchimera
  ARCHIVE DESTINATION lib
  FRAMEWORK DESTINATION lib
  LIBRARY DESTINATION lib
  PUBLIC_HEADER DESTINATION include
  RUNTIME DESTINATION bin)
install(SCRIPT cmake/bootstrap_pip.cmake)
