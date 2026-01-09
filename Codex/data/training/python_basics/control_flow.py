"""Control flow examples with conditions and loops."""


def classify_temperature(temp_c: float) -> str:
    if temp_c < 0:
        return "freezing"
    if temp_c < 18:
        return "cold"
    if temp_c < 26:
        return "comfortable"
    return "hot"


def countdown(start: int) -> list[int]:
    steps = []
    for value in range(start, 0, -1):
        steps.append(value)
    return steps


def find_first_even(values: list[int]) -> int | None:
    for value in values:
        if value % 2 == 0:
            return value
    return None


def main() -> None:
    print(classify_temperature(22.0))
    print(countdown(5))
    print(find_first_even([1, 3, 5, 8, 9]))


if __name__ == "__main__":
    main()
