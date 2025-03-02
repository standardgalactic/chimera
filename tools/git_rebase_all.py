"""git_rebase_all.py."""

from asyncio import run
from asyncio.subprocess import PIPE
from itertools import combinations
from re import match
from sys import argv
from typing import Sequence

from asyncio_cmd import ProcessError, cmd, cmd_env, git_cmd, main, splitlines
from corpus_utils import c_tqdm
from structlog import get_logger


async def git_diff(*args: str) -> bool:
    try:
        await git_cmd("diff", "--exit-code", "--quiet", *args)
    except ProcessError:
        return False
    return True


async def git_log_one(branch: str, format: str) -> str:
    try:
        log_out = await git_cmd(
            "log", f"--format={format}", "--max-count=1", f"origin/{branch}", out=PIPE
        )
    except ProcessError:
        log_out = await git_cmd(
            "log", f"--format={format}", "--max-count=1", branch, out=PIPE
        )
    return log_out.splitlines()[0].strip().decode()


async def git_no_edit(branch: str, *args: str) -> None:
    git_author_email = await git_log_one(branch, "%aE")
    git_author_name = await git_log_one(branch, "%aN")
    git_committer_email = await git_log_one(branch, "%cE")
    git_committer_name = await git_log_one(branch, "%cN")
    await cmd_env(
        "git",
        *args,
        env={
            "EDITOR": "true",
            "GIT_AUTHOR_EMAIL": git_author_email,
            "GIT_AUTHOR_NAME": git_author_name,
            "GIT_COMMITTER_EMAIL": git_committer_email,
            "GIT_COMMITTER_NAME": git_committer_name,
        },
        err=None,
        log=False,
    )


async def git_gather_branches() -> tuple[list[str], list[str]]:
    remote_branches = [
        branch
        for branch in splitlines(await git_cmd("branch", "-r", out=PIPE))
        if not branch.startswith("origin/HEAD -> ")
    ]
    await set_upstream(*remote_branches)
    return [
        (local_branch[1:].lstrip() if local_branch.startswith("* ") else local_branch)
        for local_branch in splitlines(await git_cmd("branch", out=PIPE))
    ], remote_branches


async def git_rev_list(*args: str) -> bytes:
    return await git_cmd("rev-list", "--cherry-pick", "--count", *args, out=PIPE)


async def remove_branches(
    branch_graph: dict[str, set[str]], remote_branches: Sequence[str]
) -> None:
    await git_cmd("switch", "stable")
    branches = branch_graph.pop("stable", set())
    for remote in branches.intersection(branch_graph.keys()):
        del branch_graph[remote]
    for branch in sorted(branch_graph.keys()):
        if branch not in branch_graph:
            continue
        next_branches = branch_graph.pop(branch)
        branches |= next_branches
        for remote in next_branches.intersection(branch_graph.keys()):
            del branch_graph[remote]
    if branches:
        await git_cmd("branch", "--delete", "--force", *branches)
    if del_remote_branches := set(remote_branches).intersection(branches):
        await git_cmd("push", "--delete", "origin", *del_remote_branches)


async def report_branch_graph(
    remote_branches: Sequence[str],
    local_branches: Sequence[str],
    disable_bars: bool | None,
) -> None:
    branch_graph: dict[str, set[str]] = {}
    for left, right in c_tqdm(
        combinations(local_branches, 2),
        "Gather common branches",
        disable_bars,
        len(local_branches) * (len(local_branches) - 1) // 2,
    ):
        if not await git_diff(left, right):
            continue
        branch_graph.setdefault(left, set())
        branch_graph.setdefault(right, set())
        branch_graph[left].add(right)
        branch_graph[right].add(left)
    for remote in sorted(
        {branch for branch in branch_graph.keys()}.intersection(remote_branches)
    ):
        for local in sorted(
            {branch for branch in branch_graph.get(remote, [])}
            .difference(remote_branches)
            .difference(["origin/HEAD"])
        ):
            if local in branch_graph:
                branch_graph[remote] |= branch_graph[local]
                del branch_graph[local]
            for branches in branch_graph.values():
                if local in branches:
                    branches |= branch_graph[remote]
                if remote in branches:
                    branches.remove(remote)
    await remove_branches(branch_graph, remote_branches)
    for remote, branches in branch_graph.items():
        await get_logger().ainfo(f"{remote} -> {' '.join(sorted(branches))}")


async def set_upstream(*remote_branches: str) -> None:
    for remote_branch in remote_branches:
        if remote_branch.startswith("origin/dependabot/"):
            continue
        local_name = remote_branch.split("/", maxsplit=1)[1]
        try:
            await git_cmd("branch", "--set-upstream-to", remote_branch, local_name)
        except ProcessError:
            await git_cmd("branch", local_name, remote_branch)


async def git_cherry_pick_one(local_branch: str, *args: str) -> None:
    await git_cmd("switch", "--detach", "origin/HEAD")
    try:
        await git_cmd("cherry-pick", local_branch)
    except ProcessError:
        await cmd("sh", "-c", *args, log=False)
        await git_cmd("add", "--update", ".")
        await git_no_edit(local_branch, "cherry-pick", "--continue")
    finally:
        await git_cmd("switch", "-C", local_branch)


async def git_rebase_one(local_branch: str, execute: str, *args: str) -> None:
    if match(r"corpus-\d+-", local_branch) and 1 < int(
        await git_rev_list("--left-only", f"{local_branch}...origin/stable")
    ):
        await git_cherry_pick_one(local_branch, *args)
        return
    if await git_rev_list("--right-only", f"{local_branch}...origin/stable") == b"0":
        return
    try:
        await git_cmd("rebase", "--exec", execute, "origin/stable", local_branch)
        return
    except ProcessError:
        pass
    await git_cmd("submodule", "update", "--init", "--recursive")
    while True:
        await cmd("sh", "-c", *args, log=False)
        await git_cmd("add", "--update")
        try:
            await git_no_edit(local_branch, "rebase", "--continue")
        except ProcessError:
            continue
        break


async def git_rebase_all(execute: str, *args: str, disable_bars: bool | None) -> None:
    local_branches, remote_branches = await git_gather_branches()
    for local_branch in c_tqdm(local_branches, "Rebase branches", disable_bars):
        await git_rebase_one(local_branch, execute, *args)
    await report_branch_graph(
        [remote_branch.split("/", maxsplit=1)[1] for remote_branch in remote_branches]
        + ["origin/HEAD"],
        local_branches,
        disable_bars,
    )


if __name__ == "__main__":
    with main():
        run(git_rebase_all(*argv[1:], disable_bars=None))
