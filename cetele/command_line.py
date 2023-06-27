import sys
import logging
import os

from .main import Cetele

short_cmds = {
    "s": "show",
    "e": "edit",
    "rm": "delete",
    "i": "interactive",
    "ls": "list",
    "q": "query",
    "t": "transfer",
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
    cetele = Cetele()

    match args[1]:
        case "show":
            print(cetele)
        case "edit" | "delete":
            getattr(cetele, args[1])()
        case "list":
            cetele.list_children()
        case "query":
            cetele.query()
        case "edit-raw":
            os.system(f"$EDITOR {cetele.fpath}")
        case "transfer":
            cetele.transfer()
        case _:
            exit("Unexpected argument!")
