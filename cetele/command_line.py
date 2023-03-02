import sys
import logging

from .main import State, Cetele


def parse_args(args: list) -> list:
    if "--debug" in args:
        logging.basicConfig(level=logging.DEBUG)
        args.remove("--debug")
    if len(args) == 1:
        args.append("show")
    return args


def main():
    args = parse_args(sys.argv)
    state = State()
    match args[1]:
        case "show":
            cetele = Cetele(state)
            print(cetele)
        case "edit":
            state.edit()
        case "list":
            print(state)
        case _:
            exit("Unexpected argument!")
