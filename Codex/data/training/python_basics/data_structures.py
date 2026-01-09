"""Examples of basic data structure usage."""

from collections import Counter, defaultdict


def summarize_supplies(items: list[str]) -> dict[str, int]:
    """Count the occurrences of items and return a dict."""
    return dict(Counter(items))


def group_by_prefix(items: list[str]) -> dict[str, list[str]]:
    """Group items by their first letter."""
    groups: dict[str, list[str]] = defaultdict(list)
    for item in items:
        groups[item[0]].append(item)
    return dict(groups)


def unique_sorted(items: list[str]) -> list[str]:
    """Return sorted unique items."""
    return sorted(set(items))


def stack_operations(values: list[int]) -> list[int]:
    """Demonstrate stack push/pop with a list."""
    stack = values[:]
    stack.append(99)
    stack.pop()
    return stack


def main() -> None:
    cargo = ["water", "tools", "water", "medkit", "tools"]
    print("Summary:", summarize_supplies(cargo))
    print("Grouped:", group_by_prefix(cargo))
    print("Unique:", unique_sorted(cargo))
    print("Stack:", stack_operations([1, 2, 3]))


if __name__ == "__main__":
    main()
