"""Illustrate simple file I/O patterns."""

from pathlib import Path


def write_report(path: Path, lines: list[str]) -> None:
    """Write a report file with one line per entry."""
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_report(path: Path) -> list[str]:
    """Read the report file back into a list of lines."""
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line]


def append_report(path: Path, line: str) -> None:
    """Append a single line to the report file."""
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def main() -> None:
    report_path = Path("sample_report.txt")
    write_report(report_path, ["calibration: ok", "status: nominal"])
    append_report(report_path, "notes: cleared")
    print(read_report(report_path))
    report_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
