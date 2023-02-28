import sys
import logging

from .main import (
    form_state,
    display_the_cetele,
    edit_state_file,
    display_state_file,
    read_state_file,
)


def main():
    if len(sys.argv) == 1:
        state = form_state(read_state_file())
        display_the_cetele(state)
    else:
        if "--debug" in sys.argv:
            logging.basicConfig(level=logging.DEBUG)
            sys.argv.remove("--debug")
        match sys.argv[1]:
            case "edit":
                edit_state_file()
            case "list":
                display_state_file(read_state_file())
            case _:
                exit("Unexpected argument!")
