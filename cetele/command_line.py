import sys
import logging
from . import read_the_state, display_the_cetele


def main():
    if len(sys.argv) == 1:
        state = read_the_state()
        display_the_cetele(state)
    else:
        match sys.argv[1]:
            case "--debug":
                sys.argv = [sys.argv[0]]
                logging.basicConfig(level=logging.DEBUG)
                main()
            case _:
                exit("Unexpected argument!")
