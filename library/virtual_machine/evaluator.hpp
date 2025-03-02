//! handles statements and dispatches to other evaluators

#pragma once

#include "asdl/asdl.hpp"
#include "virtual_machine/bin_evaluator.hpp"
#include "virtual_machine/bool_evaluator.hpp"
#include "virtual_machine/call_evaluator.hpp"
#include "virtual_machine/push_stack.hpp"
#include "virtual_machine/thread_context.hpp"
#include "virtual_machine/to_bool_evaluator.hpp"
#include "virtual_machine/tuple_evaluator.hpp"
#include "virtual_machine/unary_evaluator.hpp"

#include <functional>
#include <stack>
#include <variant>

namespace chimera::library::virtual_machine {
  struct Evaluator;
  struct Scopes {
    explicit operator bool() const;
    [[nodiscard]] auto self() -> object::Object &;
    void enter_scope(const object::Object &main);
    void enter();
    void exit();
    void exit_scope();
    template <typename Instruction>
    void push(Instruction &&instruction) {
      scopes.top().bodies.top().steps.push(
          std::forward<Instruction>(instruction));
    }
    template <typename Visitor>
    void visit(Visitor &&visitor) {
      if (scopes.empty()) {
        return;
      }
      if (scopes.top().bodies.empty()) {
        exit_scope();
        return;
      }
      if (scopes.top().bodies.top().steps.empty()) {
        exit();
        return;
      }
      auto top = std::move(scopes.top().bodies.top().steps.top());
      scopes.top().bodies.top().steps.pop();
      std::visit(std::forward<Visitor>(visitor), std::move(top));
    }

  private:
    struct Scope {
      object::Object self;
      struct Body {
        using Step = std::variant<
            BinAddEvaluator, BinSubEvaluator, BinMultEvaluator,
            BinMatMultEvaluator, BinDivEvaluator, BinModEvaluator,
            BinPowEvaluator, BinLShiftEvaluator, BinRShiftEvaluator,
            BinBitOrEvaluator, BinBitXorEvaluator, BinBitAndEvaluator,
            BinFloorDivEvaluator, BoolAndEvaluator, BoolOrEvaluator,
            CallEvaluator, PushStack, ToBoolEvaluator, TupleEvaluator,
            UnaryBitNotEvaluator, UnaryNotEvaluator, UnaryAddEvaluator,
            UnarySubEvaluator, std::function<void(Evaluator *)>>;
        std::stack<Step> steps{};
      };
      std::stack<Body> bodies{};
    };
    std::stack<Scope> scopes{};
  };
  struct Evaluator {
    explicit Evaluator(ThreadContext &thread_context) noexcept;
    Evaluator(const Evaluator &) = delete;
    Evaluator(Evaluator &&) noexcept = delete;
    ~Evaluator() noexcept;
    auto operator=(const Evaluator &) -> Evaluator & = delete;
    auto operator=(Evaluator &&) noexcept -> Evaluator & = delete;
    [[nodiscard]] auto builtins() const -> const object::Object &;
    void enter_scope(const object::Object &object);
    void enter();
    void exit_scope();
    void exit();
    void extend(const std::vector<asdl::ExprImpl> &instructions);
    void extend(const std::vector<asdl::StmtImpl> &instructions);
    void get_attribute(const object::Object &object, const std::string &name);
    template <typename Instruction>
    void push(Instruction &&instruction) {
      scope.push(std::forward<Instruction>(instruction));
    }
    [[nodiscard]] auto return_value() const -> object::Object;
    [[nodiscard]] auto self() -> object::Object &;
    void stack_pop();
    void stack_push(const object::Object &object);
    [[nodiscard]] auto stack_remove() -> object::Object;
    [[nodiscard]] auto stack_size() const -> std::size_t;
    [[nodiscard]] auto stack_top() const -> const object::Object &;
    void stack_top_update(const object::Object &object);
    // Evaluators
    void evaluate_del(const asdl::ExprImpl &expr);
    void evaluate_get(const asdl::ExprImpl &expr);
    void evaluate_set(const asdl::ExprImpl &expr);
    void evaluate();
    void evaluate(const asdl::AnnAssign &annAssign);
    void evaluate(const asdl::Assert &assert);
    void evaluate(const asdl::Assign &assign);
    void evaluate(const asdl::AsyncFor &asyncFor);
    void evaluate(const asdl::AsyncFunctionDef &asyncFunctionDef);
    void evaluate(const asdl::AsyncWith &asyncWith);
    void evaluate(const asdl::AugAssign &augAssign);
    void evaluate(const asdl::Break &asdlBreak);
    void evaluate(const asdl::ClassDef &classDef);
    void evaluate(const asdl::Continue &asdlContinue);
    void evaluate(const asdl::Delete &asdlDelete);
    void evaluate(const asdl::Expr &expr);
    void evaluate(const asdl::Expression &expression);
    void evaluate(const asdl::For &asdlFor);
    void evaluate(const asdl::FunctionDef &functionDef);
    void evaluate(const asdl::Global &global);
    void evaluate(const asdl::If &asdlIf);
    void evaluate(const asdl::Import &import);
    void evaluate(const asdl::ImportFrom &importFrom);
    void evaluate(const asdl::Interactive &interactive);
    void evaluate(const asdl::Module &module);
    void evaluate(const asdl::Nonlocal &nonlocal);
    void evaluate(const asdl::Raise &raise);
    void evaluate(const asdl::Return &asdlReturn);
    void evaluate(const asdl::StmtImpl &stmt);
    void evaluate(const asdl::Try &asdlTry);
    void evaluate(const asdl::While &asdlWhile);
    void evaluate(const asdl::With &with);

  private:
    [[nodiscard]] auto
    do_try(const std::vector<asdl::StmtImpl> &body,
           const std::optional<object::BaseException> &context)
        -> std::optional<object::BaseException>;
    void get_attr(const object::Object &object, const std::string &name);
    void get_attribute(const object::Object &object,
                       const object::Object &getAttribute,
                       const std::string &name);
    ThreadContext thread_context;
    Scopes scope{};
    std::stack<object::Object> stack{};
  };
} // namespace chimera::library::virtual_machine
