# Claude Code Instructions

## Git Identity

Before the first commit in any session, set the correct author:

```
git config user.email noreply@anthropic.com
git config user.name Claude
```

This is already set in `.git/config` for this repo, but run it at session start to be safe.

## Git Workflow

**Always push directly to `main`.** Never use feature branches. Every commit goes straight to `main`:

```
git push origin HEAD:main
```

Use `HEAD:main` explicitly — not `git push -u origin main` — to avoid non-fast-forward rejections when the local branch name differs from `main`.

If the push is rejected (diverged history), rebase first:

```
git fetch origin main && git rebase origin/main && git push origin HEAD:main
```

**NEVER force-push to `main` under any circumstances.** Force-pushing rewrites shared history and breaks pulls for everyone else. This includes `--force-with-lease`. There are no exceptions.

If the stop hook complains about unverified commits, fix the author with `git commit --amend --no-edit --reset-author` for the tip commit only, then do a normal `git push origin HEAD:main`. Do NOT rebase a chain of commits and force-push — create a new fixup commit instead if needed.
