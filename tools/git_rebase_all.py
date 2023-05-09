# Copyright (c) 2023 Asa Katida <github@holomaplefeline.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""git_rebase_all.py."""

from asyncio import run
from itertools import combinations, repeat
from sys import argv

from asyncio_cmd import ProcessError, cmd, cmd_env, main, splitlines
from corpus_utils import c_tqdm
from structlog import get_logger


async def git_cmd(*args: object) -> bytes:
    return await cmd("git", *args, log=False, timeout=60)


async def set_upstream(*remote_branches: str) -> None:
    for remote_branch in remote_branches:
        if "origin/HEAD" in remote_branch or remote_branch.startswith(
            "origin/dependabot/"
        ):
            continue
        local_name = remote_branch.split("/", maxsplit=1)[1]
        try:
            await git_cmd("branch", "--set-upstream-to", remote_branch, local_name)
        except ProcessError:
            await git_cmd("branch", local_name, remote_branch)


async def report_branch_graph(
    remote_branches: list[str], local_branches: list[str], disable_bars: bool
) -> None:
    branch_graph: dict[str, list[str]] = dict()
    for left, right in c_tqdm(
        combinations(local_branches, 2), "Gather common branches", disable_bars
    ):
        if left in remote_branches and right in remote_branches:
            continue
        if not await git_cmd("diff", left, right):
            if left in branch_graph and right not in branch_graph:
                branch_graph.setdefault(left, [])
                branch_graph[left].append(right)
            elif right in remote_branches or right in branch_graph:
                branch_graph.setdefault(right, [])
                branch_graph[right].append(left)
            else:
                branch_graph.setdefault(left, [])
                branch_graph[left].append(right)
    for remote, local in c_tqdm(
        sorted(branch_graph.items()), "Sort branches", disable_bars
    ):
        if remote not in remote_branches and any(
            map(list.count, branch_graph.values(), repeat(remote))
        ):
            del branch_graph[remote]
            next(filter(lambda value: remote in value, branch_graph.values())).extend(
                local
            )
    for remote, local in branch_graph.items():
        get_logger().info(f"{remote} -> {' '.join(sorted(set(local)))}")


async def git_rebase_all(*args: str, disable_bars: bool) -> None:
    await git_cmd("fetch", "--all", "--prune")
    remote_branches = list(splitlines(await git_cmd("branch", "-r")))
    await set_upstream(*remote_branches)
    local_branches = list(
        map(
            lambda local_branch: (
                local_branch[1:].lstrip()
                if local_branch.startswith("* ")
                else local_branch
            ),
            splitlines(await git_cmd("branch")),
        )
    )
    for local_branch in local_branches:
        try:
            await cmd("git", "rebase", "origin/HEAD", local_branch)
            continue
        except ProcessError:
            pass
        await cmd("bash", "-c", *args)
        await git_cmd("add", "--update")
        await cmd_env("git", "rebase", "--continue", env={"EDITOR": "true"})
    remote_branches = list(
        map(
            lambda remote_branch: remote_branch.split("/", maxsplit=1)[1],
            remote_branches,
        )
    )
    await report_branch_graph(remote_branches, local_branches, disable_bars)


if __name__ == "__main__":
    with main():
        run(git_rebase_all(*argv[1:], disable_bars=False))
