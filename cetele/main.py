import datetime
import logging
import json
from pathlib import Path
from pyfzf.pyfzf import FzfPrompt
from termcolor import colored


def last_day_of_month(any_day) -> datetime.date:
    # credit: https://stackoverflow.com/a/13565185/13426912
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return next_month - datetime.timedelta(days=next_month.day)


def leftover_pocket_money() -> float:
    today = datetime.date.today()
    days_left = last_day_of_month(today) - today
    return days_left.days * 15.00


def flatten_keys(inp: dict):
    result = []
    for k, v in inp.items():
        result += [k]
        if isinstance(v, dict):
            result += [f"{k}/{i}" for i in flatten_keys(v)]
    return result


class Cetele:
    config_dir = Path.home().joinpath(".config/cetele")

    def __init__(self):
        self.read_config()
        self.read()
        self.create_addresbook()
        self.update_pocket_money()

    def read_config(self):
        logging.debug("Reading config file.")
        config_file = self.config_dir.joinpath("config.json")
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as file:
                self.config = json.load(file)
            self.fpath = Path.home().joinpath(self.config["cetele_path"])
        else:
            exit("Please define a path on the configuration file.")

    def read(self):
        logging.debug("Reading state file.")
        with open(self.fpath, "r") as file:
            self.data = json.load(file)

    def write(self):
        logging.debug("Writing to state file.")
        with open(self.fpath, "w") as file:
            json.dump(self.data, file, indent=2)

    def create_addresbook(self):
        self.abook = {}
        for k in flatten_keys(self.data):
            self.abook[k.split("/")[-1]] = k

    def update_pocket_money(self):
        self.set(self.config["pocket_money_str"], leftover_pocket_money())
        self.write()

    def get(self, chi) -> int | float | dict:
        v = self.data
        for k in self.abook[chi].split("/"):
            v = v[k]
        return v

    def set(self, chi, val):
        d = self.data
        keys = self.abook[chi].split("/")
        for k in keys[:-1]:
            d = d[k]
        d[keys[-1]] = val

    def key_is_parent(self, key) -> bool:
        return isinstance(self.get(key), dict)

    def parents(self) -> list:
        if not hasattr(self, "parents_list"):
            logging.debug("Parent list have not been cached before, caching now.")
            self.parents_list = [k for k in self.abook.keys() if self.key_is_parent(k)]
        return self.parents_list

    def children(self) -> list:
        if not hasattr(self, "children_list"):
            logging.debug("Children list have not been cached before, caching now.")
            self.children_list = [
                k for k in self.abook.keys() if not self.key_is_parent(k)
            ]
        return self.children_list

    def prompt(self, prompt_list=None):
        if not prompt_list:
            prompt_list = self.children()
        fzf_return = FzfPrompt().prompt(prompt_list)
        logging.debug(f"fzf returned {fzf_return}")
        if not fzf_return:
            exit("Fzf returned nothing!")
        else:
            return fzf_return[0]

    def query(self):
        fzf_return = self.prompt(self.children() + self.parents())
        print(f"{fzf_return} : {self.calculate(fzf_return):.2f}")

    def edit(self):
        key = self.prompt()
        print(f"Editing -> {key} : {self.get(key):.2f}")
        if self.key_is_parent(key):
            exit("This is a parent enrty, editing this is not implemented yet...")
        else:
            try:
                self.set(key, float(input()))
            except ValueError:
                print("Please provide proper input")
            # TODO assert input is float
            print(f"New value -> {key} : {self.get(key):.2f}")
            self.write()

    def delete(self):
        key = self.prompt()
        if input(f"Deleting -> {key} : {self.get(key):.2f} [y\\n]: ") == "y":
            d = self.data
            keys = self.abook[key].split("/")
            for k in keys[:-1]:
                d = d[k]
            del d[keys[-1]]
            self.write()
        else:
            exit("Aborted.")

    def transfer(self):
        # TODO: newly implemented, quite dirty
        key_src = self.prompt()
        key_dst = self.prompt()
        print(f"Transfering {key_src}->{key_dst}. How much?")
        try:
            val = float(input())
        except ValueError:
            exit("Please provide proper input!")
        self.set(key_src, self.get(key_src) - val)
        self.set(key_dst, self.get(key_dst) + val)
        print(f"New value -> {key_src} : {self.get(key_src):.2f}")
        print(f"New value -> {key_dst} : {self.get(key_dst):.2f}")
        self.write()

    def calculate(self, k: str) -> float:
        logging.debug(f'Querying value of "{k}"')

        if self.key_is_parent(k):
            v = self.get(k)
            assert isinstance(v, dict)
            logging.debug(f"\tCalc by summing {v}")
            sum = 0
            for c in v:
                sum += self.calculate(c)
            v = sum
        else:
            v = self.get(k)

        assert isinstance(v, float) or isinstance(v, int)

        # if it is in TRY, convert to EUR before returning
        if "[try]" in k:
            v /= self.get("EUR2TRY")  # pyright: ignore , we asserted already
            k = k.replace("[try]", "")

        if "[-]" in k:
            v *= -1
            k = k.replace("[-]", "")

        return v

    def list_children(self):
        """Only the child items"""
        logging.debug("Listing the state file.")
        res = ""
        max_width = max(map(len, self.children()))
        for i, key in enumerate(self.children()):
            res += f"|{i:>2}| {key:<{max_width}} : {self.get(key):>8.2f}\n"
        print(res[:-1])

    def __str__(self) -> str:
        logging.debug("Printing the cetele table")
        cols = ["cetele", "savings", "flex", "dailies"]
        idx = ["status", "goal", "net"]

        table = []
        for c in cols:
            logging.debug(f"Forming the {c} column")
            col = []
            if c == "cetele":
                col.append(c)
                col += idx
            else:
                col.append(c)
                for i in idx:
                    val = 0.0
                    match i:
                        case "status":
                            val = self.calculate(c)
                        case "goal":
                            val = self.calculate(f"{c}-{i}")
                        case "net":
                            val = col[-2] - col[-1]
                    col.append(val)
            table.append(col)

        overall = 0
        hline = colored("-" * 45, "light_grey") + "\n"
        vline = colored("|", "light_grey")
        msg = hline
        for row in table:
            if row[0] == "cetele":
                msg += (
                    f"{vline} {colored(f'{row[0]:<8}', 'cyan')} "
                    f"{vline} {colored(f'{row[1]:>8}','cyan')} "
                    f"{vline} {colored(f'{row[2]:>8}','cyan')} "
                    f"{vline} {colored(f'{row[3]:>8}','cyan')} {vline}\n" + hline
                )
            else:
                color = "green"
                if row[3] < 0:
                    color = "red"
                msg += (
                    f"{vline} {colored(f'{row[0]:<8}','yellow')} "
                    f"{vline} {colored(f'{row[1]:>8.2f}', 'light_grey')} "
                    f"{vline} {colored(f'{row[2]:>8.2f}', 'light_grey')} "
                    f"{vline} {colored(f'{row[3]:>8.2f}', color)} {vline}\n"
                )

                overall += row[3]

        msg += hline
        titel = "overall"
        color = "green"
        if overall < 0:
            color = "red"
        msg += (
            f"{vline} {colored(f'{titel:<8}','cyan')} "
            f"{vline} {'':<8} "
            f"{vline} {'':<8} "
            f"{vline} {colored(f'{overall:>8.2f}', color)} {vline}\n"
        )
        msg += hline

        return msg[:-1]
