"""More collections module patterns."""

from __future__ import annotations

from collections import deque, namedtuple


Point = namedtuple("Point", ["x", "y"])


def demo_deque(values: list[int]) -> list[int]:
    queue = deque(values)
    queue.appendleft(0)
    queue.append(99)
    queue.pop()
    return list(queue)


def main() -> None:
    point = Point(3, 4)
    print(point.x, point.y)
    print(demo_deque([1, 2, 3]))


if __name__ == "__main__":
    main()
