//! meta template to construct an atomic wrapper for a container

#pragma once

#include <memory>       // for make_unique, unique_ptr
#include <mutex>        // for unique_lock
#include <shared_mutex> // for shared_mutex, shared_lock
#include <utility>      // for forward

namespace chimera::library::container {
  template <typename Value>
  struct AtomicContainer {
    AtomicContainer() = default;
    template <typename... Args>
    explicit AtomicContainer(Args &&...args)
        : value(std::forward<Args>(args)...) {}
    AtomicContainer(const AtomicContainer &other) : value(other.read().value) {}
    AtomicContainer(AtomicContainer &&other) noexcept
        : value(std::move(other.write().value)) {}
    ~AtomicContainer() noexcept = default;
    auto operator=(const AtomicContainer &other) -> AtomicContainer & {
      if (this != &other) {
        write().value = other.read().value;
      }
      return *this;
    }
    auto operator=(AtomicContainer &&other) noexcept -> AtomicContainer & {
      if (this != &other) {
        write().value = std::move(other.write().value);
      }
      return *this;
    }
    // NOLINTBEGIN(cppcoreguidelines-avoid-const-or-ref-data-members)
    struct Read {
      const std::shared_lock<std::shared_mutex> lock;
      const Value &value;
    };
    struct Write {
      const std::unique_lock<std::shared_mutex> lock;
      Value &value;
    };
    // NOLINTEND(cppcoreguidelines-avoid-const-or-ref-data-members)
    [[nodiscard]] auto read() const -> Read {
      return Read{std::shared_lock<std::shared_mutex>(
                      // NOLINTNEXTLINE(cppcoreguidelines-pro-type-const-cast)
                      const_cast<std::shared_mutex &>(mutex)),
                  value};
    }
    [[nodiscard]] auto write() -> Write {
      return Write{std::unique_lock<std::shared_mutex>(mutex), value};
    }

  private:
    std::shared_mutex mutex;
    Value value;
  };
} // namespace chimera::library::container
