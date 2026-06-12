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

Never force-push unless rebasing rewrote history that is already on main. If a force push is needed, use `--force-with-lease`:

```
git push origin HEAD:main --force-with-lease
```
