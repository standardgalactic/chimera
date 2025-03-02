#include "object/number/number.hpp"

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include <limits>
#include <sstream>

using chimera::library::object::number::Number;
using NumericLimits = std::numeric_limits<std::uint64_t>;

TEST_CASE("number Number") {
  Number number(0);
  {
    std::stringstream stream;
    stream << number;
    REQUIRE(stream.str() == "0");
  }
  const Number other(2);
  REQUIRE(number < other);
  number = other + other;
  REQUIRE(std::uint64_t(number) == 4);
  number = number * other + other;
  REQUIRE(std::uint64_t(number) == 10);
  REQUIRE(number == Number(10));
  number = other * number + number;
  REQUIRE(std::uint64_t(number) == 30);
  REQUIRE(number == Number(30));
  number = number - other;
  REQUIRE(std::uint64_t(number) == 28);
  REQUIRE(number == Number(28));
  {
    std::stringstream stream;
    stream << number;
    REQUIRE(stream.str() == "28");
  }
  number = number % Number(3);
  REQUIRE(std::uint64_t(number) == 1);
  number = number - Number(1);
  REQUIRE(std::uint64_t(number) == 0);
}

TEST_CASE("number Number division") {
  const Number other(2);
  const Number huge(8);
  auto number = huge * huge;
  REQUIRE(number > huge);
  auto massive = number * other;
  REQUIRE(massive > number);
  REQUIRE(massive.is_int());
  massive = massive / huge;
  REQUIRE(massive > huge);
  REQUIRE(massive.is_int());
  auto test = huge * other;
  REQUIRE(massive == test);
  REQUIRE(massive.is_int());
  massive = massive / other;
  REQUIRE(massive == huge);
}

TEST_CASE("number Number addition huge a") {
  const Number two(2);
  const Number eight(8);
  const Number huge(NumericLimits::max());
  auto number = huge + eight;
  auto massive = huge + two;
  massive += two;
  massive += two;
  massive += two;
  REQUIRE(massive.is_int());
  REQUIRE(massive == number);
}

TEST_CASE("number Number addition huge b") {
  const Number two(2);
  const Number eight(8);
  const Number huge(NumericLimits::max());
  auto number = eight + huge;
  auto massive = two + two;
  massive += two;
  massive += two;
  massive += huge;
  REQUIRE(massive.is_int());
  REQUIRE(massive == number);
}

TEST_CASE("number Number addition huge c") {
  const Number two(2);
  const Number eight(8);
  const Number huge(NumericLimits::max());
  const auto number = huge + eight;
  auto massive = two + two;
  massive += two;
  massive += two;
  massive += huge;
  REQUIRE(massive.is_int());
  REQUIRE(massive == number);
}

TEST_CASE("number Number division huge") {
  const Number other(2);
  const Number huge(NumericLimits::max());
  auto number = huge * huge;
  REQUIRE(number > huge);
  auto massive = number * other;
  REQUIRE(massive.is_int());
  REQUIRE(massive > number);
  massive = massive / huge;
  REQUIRE(massive.is_int());
  REQUIRE(massive > huge);
  auto test = huge * other;
  REQUIRE(massive == test);
  massive = massive / other;
  REQUIRE(massive.is_int());
  REQUIRE(huge.is_int());
  REQUIRE(massive == huge);
}

TEST_CASE("number Number modulus huge") {
  const Number huge(NumericLimits::max());
  const auto number = huge * Number(3);
  REQUIRE((number % Number(2)) == Number(1));
}

TEST_CASE("number Number multiplication huge a") {
  const Number two(2);
  const Number eight(8);
  const Number huge(NumericLimits::max());
  const auto number = huge * eight;
  auto massive = huge * two;
  massive *= two;
  massive *= two;
  REQUIRE(massive.is_int());
  REQUIRE(massive == number);
}

TEST_CASE("number Number multiplication huge b") {
  const Number two(2);
  const Number eight(8);
  const Number huge(NumericLimits::max());
  const auto number = eight * huge;
  auto massive = two * two;
  massive *= two;
  massive *= huge;
  REQUIRE(massive.is_int());
  REQUIRE(massive == number);
}

TEST_CASE("number Number multiplication huge c") {
  const Number two(2);
  const Number eight(8);
  const Number huge(NumericLimits::max());
  const auto number = huge * eight;
  auto massive = two * two;
  massive *= two;
  massive *= huge;
  REQUIRE(massive.is_int());
  REQUIRE(massive == number);
}

TEST_CASE("number Number naturals") {
  const Number one(1);
  const Number huge(NumericLimits::max());
  const auto number = huge * huge;
  const auto massive = number * number;
  REQUIRE(massive.is_int());
  REQUIRE(massive > number);
  REQUIRE((massive + huge) > massive);
  REQUIRE((massive + number) == (number * (number + one)));
  REQUIRE((massive - number) == (number * (number - one)));
  REQUIRE((massive * number) > massive);
  REQUIRE((massive / huge) == (number * huge));
  REQUIRE(std::uint64_t(massive & huge) == 1);
  REQUIRE((massive & number) > one);
}

TEST_CASE("number Number naturals costly") {
  const Number huge(NumericLimits::max());
  const auto number = huge * huge;
  const auto massive = number * number;
  REQUIRE((massive / number) == number);
  const auto extra = massive * massive;
  REQUIRE((extra / number) == (massive * number));
}

TEST_CASE("number Number subtraction huge") {
  const Number two(2);
  const Number eight(8);
  const Number huge(NumericLimits::max());
  auto number = huge + eight;
  auto massive = number;
  massive -= two;
  massive -= two;
  massive -= two;
  massive -= two;
  number -= eight;
  REQUIRE(massive.is_int());
  REQUIRE(massive == number);
  REQUIRE(std::uint64_t(massive) == NumericLimits::max());
  REQUIRE(std::uint64_t(number) == NumericLimits::max());
}

TEST_CASE("number Number rational costly") {
  const Number huge(NumericLimits::max());
  const Number one(1);
  const Number three(3);
  const auto third = one / three;
  const auto number = huge * three;
  REQUIRE(third == (huge / number));
  const auto massive = number * three;
  REQUIRE(third == (number / massive));
  const auto extra = massive * three;
  REQUIRE(third == (massive / extra));
  REQUIRE_THAT(double(third), Catch::Matchers::WithinRel(1.0 / 3.0));
}
