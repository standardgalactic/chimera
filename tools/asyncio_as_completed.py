from asyncio import FIRST_COMPLETED, Task, TaskGroup, wait
from os import cpu_count
from typing import Coroutine, Iterable, Iterator, TypeVar

T = TypeVar("T")

DEFAULT_LIMIT = max(cpu_count() or 1, 1) * 3


async def _next(background_tasks: set[Task[T]], coroutine: Task[T]) -> T:
    done, pending = background_tasks, {coroutine}
    try:
        done, pending = await wait(done | pending, return_when=FIRST_COMPLETED)
        return await done.pop()
    finally:
        background_tasks.clear()
        background_tasks |= done | pending


async def _schedule_tasks(
    coroutines: Iterator[Task[T]],
    limit: int = DEFAULT_LIMIT,
) -> list[T]:
    background_tasks = {coroutine for coroutine, _ in zip(coroutines, range(limit - 1))}
    try:
        return [
            await _next(background_tasks, coroutine) for coroutine in coroutines
        ] + [await task for task in background_tasks]
    finally:
        list(coroutines)


async def as_completed(
    coroutines: Iterable[Coroutine[object, object, T]],
    limit: int = DEFAULT_LIMIT,
) -> list[T]:
    async with TaskGroup() as group:
        return await _schedule_tasks(
            (group.create_task(coroutine) for coroutine in coroutines), limit=limit
        )
