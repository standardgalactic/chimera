// Copyright (c) 2017 Asa Katida <github@holomaplefeline.net>
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

#include "object/number/mult.hpp"

#include <gsl/gsl>

#include "object/number/left_shift.hpp"
#include "object/number/negative.hpp"
#include "object/number/overflow.hpp"

namespace chimera {
  namespace library {
    namespace object {
      namespace number {
        Positive operator*(std::uint64_t left, Base right) {
          return right * left;
        }

        Natural operator*(std::uint64_t left, const Natural &right) {
          return right * left;
        }

        Positive operator*(std::uint64_t /*left*/, const Positive & /*right*/) {
          Expects(false);
        }

        Negative operator*(std::uint64_t left, const Negative &right) {
          return right * left;
        }

        Integer operator*(std::uint64_t /*left*/, const Integer & /*right*/) {
          Expects(false);
        }

        Rational operator*(std::uint64_t left, const Rational &right) {
          return right * left;
        }

        Positive operator*(Base left, std::uint64_t right) {
          auto value = mult(left.value, right);
          if (value.overflow == 0u) {
            return Base{value.result};
          }
          return Natural{{value.result, value.overflow}};
        }

        Positive operator*(Base left, Base right) { return left * right.value; }

        Natural operator*(Base left, const Natural &right) {
          return right * left;
        }

        Positive operator*(Base /*left*/, const Positive & /*right*/) {
          Expects(false);
        }

        Negative operator*(Base left, const Negative &right) {
          return right * left;
        }

        Integer operator*(Base /*left*/, const Integer & /*right*/) {
          Expects(false);
        }

        Rational operator*(Base left, const Rational &right) {
          return right * left;
        }

        Natural operator*(const Natural &left, std::uint64_t right) {
          if (right == 0) {
            return {};
          }
          if (right == 1) {
            return left;
          }
          Natural value{};
          value.value.reserve(left.value.size() + 1);
          Carryover carryover{};
          for (std::uint64_t i : left.value) {
            auto m = mult(i, right);
            carryover = sum(m.result, carryover.result);
            value.value.push_back(carryover.result);
            carryover = sum(m.overflow, carryover.overflow);
            Ensures(carryover.overflow == 0);
          }
          if (carryover.result != 0) {
            value.value.push_back(carryover.result);
          }
          return value;
        }

        Natural operator*(const Natural &left, Base right) {
          return left * right.value;
        }

        Natural operator*(const Natural &left, const Natural &right) {
          std::vector<Natural> integers;
          integers.reserve(right.value.size());
          for (std::uint64_t i : right.value) {
            integers.push_back((left * i) << (64 * integers.size()));
          }
          // TODO(asakatida)
          // return std::accumulate(integers.begin(), integers.end(),
          // Natural{});
          return {};
        }

        Natural operator*(const Natural & /*left*/,
                          const Positive & /*right*/) {
          Expects(false);
        }

        Negative operator*(const Natural &left, const Negative &right) {
          return right * left;
        }

        Integer operator*(const Natural & /*left*/, const Integer & /*right*/) {
          Expects(false);
        }

        Rational operator*(const Natural &left, const Rational &right) {
          return right * left;
        }

        Positive operator*(const Positive & /*left*/, std::uint64_t /*right*/) {
          Expects(false);
        }

        Positive operator*(const Positive & /*left*/, Base /*right*/) {
          Expects(false);
        }

        Positive operator*(const Positive & /*left*/,
                           const Natural & /*right*/) {
          Expects(false);
        }

        Positive operator*(const Positive & /*left*/,
                           const Positive & /*right*/) {
          Expects(false);
        }

        Negative operator*(const Positive & /*left*/,
                           const Negative & /*right*/) {
          Expects(false);
        }

        Integer operator*(const Positive & /*left*/,
                          const Integer & /*right*/) {
          Expects(false);
        }

        Rational operator*(const Positive & /*left*/,
                           const Rational & /*right*/) {
          Expects(false);
        }

        Negative operator*(const Negative &left, std::uint64_t right) {
          return std::visit(
              [&right](const auto &value) { return -(value * right); },
              left.value);
        }

        Negative operator*(const Negative &left, Base right) {
          return left * right.value;
        }

        Negative operator*(const Negative &left, const Natural &right) {
          return std::visit(
              [&right](const auto &value) { return -(value * right); },
              left.value);
        }

        Negative operator*(const Negative & /*left*/,
                           const Positive & /*right*/) {
          Expects(false);
        }

        Positive operator*(const Negative &left, const Negative &right) {
          return std::visit(
              [](const auto &a, const auto &b) { return Positive(a * b); },
              left.value, right.value);
        }

        Integer operator*(const Negative & /*left*/,
                          const Integer & /*right*/) {
          Expects(false);
        }

        Rational operator*(const Negative &left, const Rational &right) {
          return right * left;
        }

        Integer operator*(const Integer & /*left*/, std::uint64_t /*right*/) {
          Expects(false);
        }

        Integer operator*(const Integer & /*left*/, Base /*right*/) {
          Expects(false);
        }

        Integer operator*(const Integer & /*left*/, const Natural & /*right*/) {
          Expects(false);
        }

        Integer operator*(const Integer & /*left*/,
                          const Positive & /*right*/) {
          Expects(false);
        }

        Integer operator*(const Integer & /*left*/,
                          const Negative & /*right*/) {
          Expects(false);
        }

        Integer operator*(const Integer & /*left*/, const Integer & /*right*/) {
          Expects(false);
        }

        Rational operator*(const Integer & /*left*/,
                           const Rational & /*right*/) {
          Expects(false);
        }

        Rational operator*(const Rational &left, std::uint64_t right) {
          return std::visit(
              [&right](const auto &lN, const auto &lD) {
                return Rational{lN * right, lD};
              },
              left.numerator, left.denominator);
        }

        Rational operator*(const Rational &left, Base right) {
          return left * right.value;
        }

        Rational operator*(const Rational &left, const Natural &right) {
          return std::visit(
              [&right](const auto &lN, const auto &lD) {
                return Rational{lN * right, lD};
              },
              left.numerator, left.denominator);
        }

        Base operator*(const Rational & /*left*/, const Positive & /*right*/) {
          Expects(false);
        }

        Rational operator*(const Rational &left, const Negative &right) {
          return std::visit(
              [&right](const auto &lN, const auto &lD) {
                return Rational{lN * right, lD};
              },
              left.numerator, left.denominator);
        }

        Rational operator*(const Rational & /*left*/,
                           const Integer & /*right*/) {
          Expects(false);
        }

        Rational operator*(const Rational &left, const Rational &right) {
          return std::visit(
              [](const auto &lN, const auto &lD, const auto &rN,
                 const auto &rD) {
                return Rational{lN * rN, lD * rD};
              },
              left.numerator, left.denominator, right.numerator,
              right.denominator);
        }
      } // namespace number
    }   // namespace object
  }     // namespace library
} // namespace chimera
