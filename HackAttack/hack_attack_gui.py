"""Legacy launcher for HackAttack GUI (delegates to app.main)."""

from HackAttack.app.main import HackAttackGUI, main

__all__ = ["HackAttackGUI", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
