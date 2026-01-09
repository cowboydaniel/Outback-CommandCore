"""Tiny hello-world style examples."""


def greet(name: str, punctuation: str = "!") -> str:
    """Return a friendly greeting."""
    return f"Hello, {name}{punctuation}"


def build_message(names: list[str]) -> str:
    """Join greetings into a single message."""
    greetings = [greet(name) for name in names]
    return " ".join(greetings)


def main() -> None:
    names = ["Commander", "Navigator", "Engineer"]
    for name in names:
        print(greet(name))
    print(build_message(names))


if __name__ == "__main__":
    main()
