from interface.app import run_interface
from main import run_core


def main() -> None:
    run_interface(core_target=run_core)


if __name__ == "__main__":
    main()
