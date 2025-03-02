//! parse definitions for string tokens.

#pragma once

#include "asdl/asdl.hpp"
#include "grammar/exprfwd.hpp"
#include "grammar/flags.hpp"
#include "grammar/oper.hpp"
#include "grammar/rules.hpp"
#include "grammar/whitespace.hpp"
#include "object/object.hpp"

#include <gsl/gsl>
#include <tao/pegtl.hpp>
#include <tao/pegtl/contrib/unescape.hpp>

#include <algorithm>
#include <cstdint>
#include <numeric>
#include <string>
#include <string_view>
#include <variant>

namespace chimera::library::grammar {
  namespace token {
    using namespace std::literals;
    struct StringHolder : rules::VariantCapture<object::Object> {
      std::string string;
      template <typename Input, typename... Args>
      void apply(const Input &input, Args &&.../*args*/) {
        string.append(input);
      }
    };
    struct LiteralChar : plus<not_one<'\0', '{', '}'>> {};
    template <>
    struct Action<LiteralChar> {
      template <typename Input, typename Top, typename... Args>
      static void apply(const Input &input, Top &&top, Args &&.../*args*/) {
        top.apply(input.string());
      }
    };
    template <flags::Flag Option>
    using FExpression =
        sor<list_tail<sor<ConditionalExpression<Option>, StarExpr<Option>>,
                      Comma<Option>>,
            YieldExpr<Option>>;
    struct Conversion : one<'a', 'r', 's'> {};
    template <>
    struct Action<Conversion> {
      template <typename Input, typename Top, typename... Args>
      static void apply(const Input &input, Top &&top, Args &&.../*args*/) {
        asdl::FormattedValue formattedValue{
            top.template pop<asdl::ExprImpl>(), asdl::FormattedValue::STR, {}};
        switch (input.peek_char()) {
          case 'a':
            formattedValue.conversion = asdl::FormattedValue::ASCII;
            break;
          case 'r':
            formattedValue.conversion = asdl::FormattedValue::REPR;
            break;
          case 's':
            formattedValue.conversion = asdl::FormattedValue::STR;
            break;
          default:
            break;
        }
        top.push(asdl::ExprImpl{std::move(formattedValue)});
      }
    };
    template <flags::Flag Option>
    struct FormatSpec;
    template <flags::Flag Option>
    using ReplacementField =
        if_must<LBrt<Option>, FExpression<Option>, opt<one<'!'>, Conversion>,
                opt<one<':'>, FormatSpec<Option>>, RBrt<Option>>;
    template <flags::Flag Option>
    struct FormatSpec
        : star<sor<LiteralChar, one<0>, ReplacementField<Option>>> {};
    template <flags::Flag Option>
    struct Action<FormatSpec<Option>> {
      template <typename Top, typename... Args>
      static void apply0(Top &&top, Args &&.../*args*/) {
        auto formatSpec = top.template pop<asdl::ExprImpl>();
        auto expr = top.template pop<asdl::ExprImpl>();
        auto is_formatted_value = expr.template update_if<asdl::FormattedValue>(
            [&formatSpec](auto &&formattedValue) {
              formattedValue.format_spec = std::move(formatSpec);
              return formattedValue;
            });
        if (is_formatted_value) {
          top.push(std::move(expr));
        } else {
          top.push(asdl::ExprImpl{
              asdl::FormattedValue{std::move(expr), asdl::FormattedValue::STR,
                                   std::move(formatSpec)}});
        }
      }
    };
    struct LeftFLiteral : String<'{', '{'> {};
    template <>
    struct Action<LeftFLiteral> {
      template <typename Top, typename... Args>
      static void apply0(Top &&top, Args &&.../*args*/) {
        top.apply("{"sv);
      }
    };
    struct RightFLiteral : String<'}', '}'> {};
    template <>
    struct Action<RightFLiteral> {
      template <typename Top, typename... Args>
      static void apply0(Top &&top, Args &&.../*args*/) {
        top.apply("}"sv);
      }
    };
    struct FLiteral : plus<sor<LiteralChar, LeftFLiteral, RightFLiteral>> {
      using Transform = StringHolder;
    };
    template <>
    struct Action<FLiteral> {
      template <typename Top, typename... Args>
      static void apply0(Top &&top, Args &&.../*args*/) {
        top.push(object::Object(object::String(top.string), {}));
      }
    };
    template <flags::Flag Option>
    using FString = seq<star<sor<FLiteral, ReplacementField<Option>>>, eof>;
    template <typename Chars>
    struct SingleChars : plus<Chars> {};
    template <typename Chars>
    struct Action<SingleChars<Chars>> {
      template <typename Input, typename Top, typename... Args>
      static void apply(const Input &input, Top &&top, Args &&.../*args*/) {
        top.apply(input.string());
      }
    };
    template <unsigned Len>
    struct Hexseq : rep<Len, ranges<'0', '9', 'a', 'f', 'A', 'F'>> {};
    template <unsigned Len>
    struct Action<Hexseq<Len>> {
      template <typename Input, typename Top, typename... Args>
      static auto apply(const Input &input, Top &&top, Args &&.../*args*/)
          -> bool {
        std::string string;
        if (tao::pegtl::unescape::utf8_append_utf32(
                string, tao::pegtl::unescape::unhex_string<std::uint32_t>(
                            input.begin(), input.end()))) {
          top.apply(std::move(string));
          return true;
        }
        return false;
      }
    };
    template <char Open, unsigned Len>
    using UTF = seq<one<Open>, Hexseq<Len>>;
    struct Octseq : seq<range<'0', '7'>, rep_opt<2, range<'0', '7'>>> {};
    template <>
    struct Action<Octseq> {
      template <typename Input, typename Top, typename... Args>
      static auto apply(const Input &input, Top &&top, Args &&.../*args*/)
          -> bool {
        std::string string;
        if (tao::pegtl::unescape::utf8_append_utf32(
                string,
                std::accumulate(input.begin(), input.end(), std::uint32_t(0),
                                [](auto &&init, auto &&byte) {
                                  return (init << 2U) |
                                         gsl::narrow<std::uint32_t>(byte - '0');
                                }))) {
          top.apply(std::move(string));
          return true;
        }
        return false;
      }
    };
    struct EscapeControl : one<'a', 'b', 'f', 'n', 'r', 't', 'v'> {};
    template <>
    struct Action<EscapeControl> {
      template <typename Input, typename Top, typename... Args>
      static void apply(const Input &input, Top &&top, Args &&.../*args*/) {
        static const std::map<char, std::string_view> escapes{
            {'a', "\a"sv}, {'b', "\b"sv}, {'f', "\f"sv}, {'n', "\n"sv},
            {'r', "\r"sv}, {'t', "\t"sv}, {'v', "\v"sv}};
        Ensures(escapes.contains(input.peek_char()));
        top.apply(escapes.at(input.peek_char()));
      }
    };
    template <typename Chars>
    struct EscapeIgnore : seq<Chars> {};
    template <typename Chars>
    struct Action<EscapeIgnore<Chars>> {
      template <typename Input, typename Top, typename... Args>
      static void apply(const Input &input, Top &&top, Args &&.../*args*/) {
        top.apply(R"(\)"sv);
        top.apply(input.string());
      }
    };
    using Escape = one<'\\'>;
    using XEscapeseq = UTF<'x', 2>;
    template <typename Chars, typename... Escapes>
    using Escapeseq = sor<Escapes..., XEscapeseq, Octseq, Eol, EscapeControl,
                          EscapeIgnore<Chars>>;
    template <typename Chars, typename... Escapes>
    using Item = seq<if_then_else<Escape, Escapeseq<Chars, Escapes...>,
                                  SingleChars<minus<Chars, Escape>>>,
                     discard>;
    template <typename Chars>
    using RawItem = if_then_else<Escape, Chars, Chars>;
    template <typename Triple, typename Chars, typename... Escapes>
    using Long =
        if_must<Triple,
                until<Triple, Item<seq<not_at<Triple>, Chars>, Escapes...>>>;
    template <typename Triple, typename Chars>
    struct LongRaw
        : if_must<Triple, until<Triple, seq<RawItem<seq<not_at<Triple>, Chars>>,
                                            discard>>> {};
    template <typename Quote, typename Chars, typename... Escapes>
    using Short = if_must<
        Quote,
        until<Quote, Item<minus<seq<not_at<Quote>, Chars>, Eol>, Escapes...>>>;
    template <typename Quote, typename Chars>
    struct ShortRaw
        : if_must<
              Quote,
              until<Quote, seq<RawItem<minus<seq<not_at<Quote>, Chars>, Eol>>,
                               discard>>> {};
    using TripleSingle = rep<3, one<'\''>>;
    using TripleDouble = rep<3, one<'"'>>;
    using Single = one<'\''>;
    using Double = one<'"'>;
    template <typename Chars>
    using Raw = sor<LongRaw<TripleDouble, Chars>, LongRaw<TripleSingle, Chars>,
                    ShortRaw<Double, Chars>, ShortRaw<Single, Chars>>;
    template <typename Chars, typename... Escapes>
    using Escaped =
        sor<Long<TripleDouble, Chars, Escapes...>,
            Long<TripleSingle, Chars, Escapes...>,
            Short<Double, Chars, Escapes...>, Short<Single, Chars, Escapes...>>;
    using UTF16Escape = UTF<'u', 4>;
    using UTF32Escape = UTF<'U', 8>;
    struct UName : star<not_one<'}'>> {};
    template <>
    struct Action<UName> {
      template <typename Input, typename Top, typename... Args>
      static void apply(const Input &input, Top &&top, Args &&.../*args*/) {
        top.apply(input.string());
      }
    };
    using UNameEscape = if_must<String<'N', '{'>, UName, one<'}'>>;
    template <typename Prefix, typename RawPrefix, typename Chars,
              typename... Escapes>
    using StringImpl = sor<seq<RawPrefix, Raw<Chars>>,
                           seq<Prefix, Escaped<Chars, Escapes...>>>;
    using BytesPrefix = one<'b', 'B'>;
    using BytesRawPrefix = sor<seq<one<'r', 'R'>, one<'b', 'B'>>,
                               seq<one<'b', 'B'>, one<'r', 'R'>>>;
    template <flags::Flag Option>
    struct Bytes : plus<Token<Option, StringImpl<BytesPrefix, BytesRawPrefix,
                                                 range<0, 0b1111111>>>> {
      struct Transform : rules::VariantCapture<object::Object> {
        object::Bytes bytes;
        template <typename Input, typename... Args>
        void apply(const Input &input, Args &&.../*args*/) {
          for (const auto &byte : input) {
            if (byte > 0xFF) {
              throw rules::BytesASCIIOnlyError();
            }
            bytes.emplace_back(gsl::narrow<std::uint8_t>(byte && 0xFF));
          }
        }
      };
    };
    template <flags::Flag Option>
    struct Action<Bytes<Option>> {
      template <typename Top, typename... Args>
      static void apply0(Top &&top, Args &&.../*args*/) {
        top.push(object::Object(std::move(top.bytes), {}));
      }
    };
    using StrPrefix = opt<one<'u', 'U'>>;
    using StrRawPrefix = one<'r', 'R'>;
    template <flags::Flag Option>
    struct DocString
        : plus<Token<Option,
                     StringImpl<StrPrefix, StrRawPrefix, any, UTF16Escape,
                                UTF32Escape, UNameEscape>>> {
      using Transform = StringHolder;
    };
    template <flags::Flag Option>
    struct Action<DocString<Option>> {
      template <typename Top, typename... Args>
      static void apply0(Top &&top, Args &&.../*args*/) {
        top.push(object::Object(object::String(top.string), {}));
      }
    };
    using JoinedStrPrefix = one<'f', 'F'>;
    using JoinedStrRawPrefix = sor<seq<one<'r', 'R'>, one<'f', 'F'>>,
                                   seq<one<'f', 'F'>, one<'r', 'R'>>>;
    struct PartialString
        : plus<StringImpl<StrPrefix, StrRawPrefix, any, UTF16Escape,
                          UTF32Escape, UNameEscape>> {
      struct Transform {
        std::string string;
        template <typename Outer>
        void finalize(Transform & /*unused*/, Outer &&outer) {
          outer.push(std::move(string));
        }
        template <typename Input, typename... Args>
        void apply(const Input &input, Args &&.../*args*/) {
          string.append(input);
        }
      };
    };
    template <flags::Flag Option>
    struct FormattedString
        : seq<StringImpl<JoinedStrPrefix, JoinedStrRawPrefix, any, UTF16Escape,
                         UTF32Escape, UNameEscape>> {
      struct Transform : rules::Stack<asdl::ExprImpl> {
        std::string string;
        template <typename Outer>
        void success(Outer &&outer) {
          asdl::JoinedStr joinedStr;
          joinedStr.values.reserve(size());
          transform<asdl::ExprImpl>(std::back_inserter(joinedStr.values));
          outer.push(std::move(joinedStr));
        }
        template <typename Input, typename... Args>
        void apply(const Input &input, Args &&.../*args*/) {
          string.append(input);
        }
      };
    };
    template <flags::Flag Option>
    struct Action<FormattedString<Option>> {
      template <typename Input, typename Top, typename... Args>
      [[nodiscard]] static auto apply(const Input &input, Top &&top,
                                      Args &&.../*args*/) -> bool {
        return tao::pegtl::parse_nested<
            FString<flags::list<flags::DISCARD, flags::IMPLICIT>>, Action,
            Normal>(input,
                    tao::pegtl::memory_input<>(top.string.c_str(),
                                               top.string.size(), "<f_string>"),
                    std::forward<Top>(top));
      }
    };
    template <flags::Flag Option>
    struct JoinedStrOne
        : plus<Token<Option, sor<PartialString, FormattedString<Option>>>> {
      using Transform = rules::VariantCapture<std::string, asdl::JoinedStr>;
    };
    template <flags::Flag Option>
    struct Action<JoinedStrOne<Option>> {
      using State = std::variant<std::string, asdl::JoinedStr>;
      struct Visitor {
        [[nodiscard]] auto operator()(const std::string &value,
                                      const std::string &element) -> State {
          return {value + element};
        }
        [[nodiscard]] auto operator()(const std::string &value,
                                      const asdl::JoinedStr &joinedStr)
            -> State {
          auto values = joinedStr.values;
          values.emplace(values.begin(),
                         object::Object(object::String(value), {}));
          return {asdl::JoinedStr{std::move(values)}};
        }
        [[nodiscard]] auto operator()(const asdl::JoinedStr &value,
                                      const std::string &element) -> State {
          auto values = value.values;
          values.emplace_back(object::Object(object::String(element), {}));
          return {asdl::JoinedStr{std::move(values)}};
        }
        [[nodiscard]] auto operator()(const asdl::JoinedStr &value,
                                      const asdl::JoinedStr &joinedStr)
            -> State {
          auto values = value.values;
          std::move(joinedStr.values.begin(), joinedStr.values.end(),
                    std::back_inserter(values));
          return {asdl::JoinedStr{std::move(values)}};
        }
      };
      template <typename Top, typename... Args>
      static void apply0(Top &&top, Args &&.../*args*/) {
        std::visit(
            top, top.reduce(State{}, [](const State &left, const State &right) {
              return std::visit(Visitor{}, left, right);
            }));
      }
    };
    template <flags::Flag Option>
    struct JoinedStr : seq<JoinedStrOne<Option>> {
      struct Transform
          : rules::Stack<std::string, asdl::JoinedStr, object::Object> {
        struct Push {
          using State = std::variant<asdl::JoinedStr, object::Object>;
          [[nodiscard]] auto operator()(std::string && /*value*/) -> State {
            Expects(false);
          }
          [[nodiscard]] auto operator()(asdl::JoinedStr &&value) -> State {
            return {std::move(value)};
          }
          [[nodiscard]] auto operator()(object::Object &&value) -> State {
            return {std::move(value)};
          }
        };
        template <typename Outer>
        void success(Outer &&outer) {
          std::visit(outer, std::visit(Push{}, pop()));
        }
      };
    };
    template <flags::Flag Option>
    struct Action<JoinedStr<Option>> {
      struct Push {
        using State = std::variant<asdl::JoinedStr, object::Object>;
        [[nodiscard]] auto operator()(std::string &&value) {
          return State{object::Object(object::String(value), {})};
        }
        [[nodiscard]] auto operator()(asdl::JoinedStr &&value) {
          return State{std::move(value)};
        }
        [[nodiscard]] auto operator()(object::Object &&value) {
          return State{std::move(value)};
        }
      };
      template <typename Top, typename... Args>
      static void apply0(Top &&top, Args &&.../*args*/) {
        std::visit(top, std::visit(Push{}, top.pop()));
      }
    };
  } // namespace token
  template <flags::Flag Option>
  struct DocString : seq<token::DocString<Option>, sor<NEWLINE, at<Eolf>>> {
    using Transform = rules::ReshapeCapture<asdl::DocString, object::Object>;
  };
  template <flags::Flag Option>
  struct STRING : sor<token::Bytes<Option>, token::JoinedStr<Option>> {};
} // namespace chimera::library::grammar
