"""Command-line argument parsing with argparse."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Greeter")
    parser.add_argument("name", help="Name to greet")
    parser.add_argument("--punctuation", default="!", help="Punctuation to use")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args(["Ada", "--punctuation", "!!!"])
    print(f"Hello, {args.name}{args.punctuation}")


if __name__ == "__main__":
    main()
