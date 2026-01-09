"""Threading basics with a shared counter."""

from __future__ import annotations

import threading


def increment(counter: list[int], lock: threading.Lock, times: int) -> None:
    for _ in range(times):
        with lock:
            counter[0] += 1


def main() -> None:
    counter = [0]
    lock = threading.Lock()
    threads = [threading.Thread(target=increment, args=(counter, lock, 1000)) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print(counter[0])


if __name__ == "__main__":
    main()
