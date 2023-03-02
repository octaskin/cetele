import sys
import logging

from .main import State, Cetele


def main():
    state = State()
    if len(sys.argv) == 1:
        cetele = Cetele(state)
        print(cetele)
    else:
        if "--debug" in sys.argv:
            logging.basicConfig(level=logging.DEBUG)
            sys.argv.remove("--debug")
        match sys.argv[1]:
            case "edit":
                state.edit()
            case "list":
                print(state)
            case _:
                exit("Unexpected argument!")
