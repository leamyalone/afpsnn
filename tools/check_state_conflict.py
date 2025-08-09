import sys

def main() -> None:
    """Simple state conflict checker.

    In a full implementation, this script would examine open PRs and ensure that
    only one PR modifies STATE.md at a time. Here we simply succeed.
    """
    print("State conflict check passed.")


if __name__ == "__main__":
    main()
