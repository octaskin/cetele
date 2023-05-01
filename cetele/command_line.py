import sys
import logging
import os

from .main import State, Cetele

short_cmds = {
    "s": "show",
    "e": "edit",
    "rm": "delete",
    "i": "interactive",
    "ls": "list",
    "v": "verify",
    "q": "query",
}


def parse_args(args: list) -> list:
    if "--debug" in args:
        logging.basicConfig(level=logging.DEBUG)
        args.remove("--debug")
    if len(args) == 1:
        args.append("show")
    if long_version := short_cmds.get(args[1]):
        args[1] = long_version
    return args


def main(args=sys.argv):
    args = parse_args(args)
    logging.debug(f"Received args from shell {args}")
    state = State()

    match args[1]:
        case "show":
            cetele = Cetele(state)
            print(cetele)
        case "edit" | "delete":
            getattr(state, args[1])()
        case "list":
            print(state)
        case "verify":
            state.verify()
        case "query":
            Cetele(state).query_value()
        case "edit-raw":
            os.system(f"$EDITOR {state.fpath}")
        case _:
            exit("Unexpected argument!")
