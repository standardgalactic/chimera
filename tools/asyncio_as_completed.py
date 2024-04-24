from asyncio import FIRST_COMPLETED, CancelledError, Task, TaskGroup, wait
from os import cpu_count
from sys import exc_info
from typing import Coroutine, Iterable, Iterator, TypeVar

T = TypeVar("T")

DEFAULT_LIMIT = max(cpu_count() or 0, 1) * 3


async def _list(iter: Iterator[Task[T]], return_exceptions: bool) -> list[T]:
    cancelled: CancelledError | None = None
    try:
        return [await task for task in iter]
    except Exception:
        if not return_exceptions:
            raise
        return []
    finally:
        if isinstance(exc_info()[1], KeyboardInterrupt):
            raise
        for task in iter:
            try:
                if not task.done():
                    task.cancel()
            except AttributeError:
                pass
            try:
                await task
            except KeyboardInterrupt:
                raise
            except CancelledError as error:
                cancelled = error
            except Exception:
                pass
        if exc_info()[1] is None and cancelled:
            raise cancelled


async def _next(
    group: TaskGroup,
    background_tasks: set[Task[T]],
    coroutine: Coroutine[object, object, T],
) -> T:
    done, pending = background_tasks, {group.create_task(coroutine)}
    try:
        done, pending = await wait(done | pending, return_when=FIRST_COMPLETED)
        return await done.pop()
    finally:
        background_tasks.clear()
        background_tasks |= done | pending


def _schedule_tasks(
    group: TaskGroup, coroutines: Iterable[Coroutine[object, object, T]], limit: int
) -> Iterator[Task[T]]:
    background_tasks = {
        group.create_task(coroutine)
        for coroutine, _ in zip(coroutines, range(limit - 1))
    }
    yield from (
        group.create_task(_next(group, background_tasks, coroutine))
        for coroutine in coroutines
    )
    yield from background_tasks


async def as_completed(
    coroutines: Iterable[Coroutine[object, object, T]],
    limit: int = DEFAULT_LIMIT,
    return_exceptions: bool = False,
) -> list[T]:
    async with TaskGroup() as group:
        return await _list(
            _schedule_tasks(group, coroutines, limit),
            return_exceptions=return_exceptions,
        )
