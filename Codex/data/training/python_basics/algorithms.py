"""Small algorithm examples: search and sort."""

from __future__ import annotations


def linear_search(values: list[int], target: int) -> int | None:
    for index, value in enumerate(values):
        if value == target:
            return index
    return None


def bubble_sort(values: list[int]) -> list[int]:
    result = values[:]
    for pass_index in range(len(result)):
        for index in range(0, len(result) - pass_index - 1):
            if result[index] > result[index + 1]:
                result[index], result[index + 1] = result[index + 1], result[index]
    return result


def main() -> None:
    data = [5, 2, 9, 1]
    print(linear_search(data, 9))
    print(bubble_sort(data))


if __name__ == "__main__":
    main()
