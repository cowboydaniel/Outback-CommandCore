"""List, set, and dict comprehension examples."""

from __future__ import annotations


def squared(values: list[int]) -> list[int]:
    return [value ** 2 for value in values]


def unique_words(text: str) -> set[str]:
    return {word.lower() for word in text.split() if word.isalpha()}


def index_names(names: list[str]) -> dict[str, int]:
    return {name: index for index, name in enumerate(names, start=1)}


def main() -> None:
    print(squared([1, 2, 3]))
    print(unique_words("Signal strong Signal clear"))
    print(index_names(["Ada", "Linus", "Guido"]))


if __name__ == "__main__":
    main()
