"""Text processing patterns."""

from __future__ import annotations


def normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def word_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for word in normalize(text).split(" "):
        counts[word] = counts.get(word, 0) + 1
    return counts


def main() -> None:
    print(normalize("  Hello   WORLD "))
    print(word_counts("Hello hello world"))


if __name__ == "__main__":
    main()
