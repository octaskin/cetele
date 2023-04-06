import datetime
import logging
import json
from pathlib import Path
from pyfzf.pyfzf import FzfPrompt


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


class State:
    edit_actions = {"E": "edit", "D": "delete", "Q": "quit"}
    edit_prompt = "You want to [E]dit or [D]elete an entry, Q[uit]?: "
    config_dir = Path.home().joinpath(".config/cetele")

    def __init__(self):
        self.read_config()
        self.read()

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
        self.data[self.config["pocket_money_str"]] = leftover_pocket_money()

    def write(self):
        logging.debug("Writing to state file.")
        with open(self.fpath, "w") as file:
            json.dump(self.data, file, indent=2)

    def prompt(self):
        fzf_return = FzfPrompt().prompt(
            [f"{k}:{self.data[k]}" for k in self.children()]
        )
        logging.debug(f"fzf returned {fzf_return}")
        if not fzf_return:
            exit("Fzf returned nothing!")
        else:
            return fzf_return[0].split(":")[0]

    def edit(self):
        key = self.prompt()
        print(f"Editing -> {key} : {self.data[key]:.2f}")
        if self.key_is_parent(key):
            exit("This is a parent enrty, editing this is not implemented yet...")
        else:
            try:
                self.data[key] = float(input())
            except:
                print("Please provide proper input")
            # TODO assert input is float
            print(f"New value -> {key} : {self.data[key]:.2f}")
            self.write()

    def delete(self, idx):
        key = self.prompt()
        if input(f"Deleting -> {key} : {self.data[key]:.2f} [y\\n]: ") == "y":
            del self.data[key]
            for p in self.parents():
                if key in self.data[p]:
                    logging.debug(f"Removing child from: {p}")
                    self.data[p].remove(key)
            self.write()
        else:
            exit("Aborted.")

    def verify(self):
        flag = True
        logging.debug("Verifying state file.")
        all_children = [i for p in self.parents() for i in self.data[p]]
        for k in self.children():
            if k not in all_children + ["EUR2TRY"]:  # currency is an exception
                print(f"{k} is an orphan, please review or remove!")
                flag = False

        if flag:
            print("No problems have been encountered!")
        logging.debug("Verification done.")

    def key_is_parent(self, key) -> bool:
        return isinstance(self.data[key], list)

    def parents(self) -> list:
        if not hasattr(self, "parents_list"):
            logging.debug("Parent list have not been cached before, caching now.")
            self.parents_list = [k for k in self.data if self.key_is_parent(k)]
        return self.parents_list

    def children(self) -> list:
        if not hasattr(self, "children_list"):
            logging.debug("Children list have not been cached before, caching now.")
            self.children_list = [k for k in self.data if not self.key_is_parent(k)]
        return self.children_list

    def __str__(self):
        """Only the child items"""
        logging.debug("Listing the state file.")
        res = ""
        max_width = max(map(len, self.data))
        for i, key in enumerate(self.children()):
            res += f"|{i:>2}| {key:<{max_width}} : {self.data[key]:>8.2f}\n"
        return res[:-1]


class Cetele:
    def __init__(self, state: State):
        self.state = state

    def calculate(self, k: str) -> float:
        logging.debug(f'Querying value of "{k}"')
        v = self.state.data[k]

        if isinstance(v, list):
            logging.debug(f"\tCalc by summing {v}")
            sum = 0
            for c in v:
                sum += self.calculate(c)
            self.state.data[k] = sum
            v = sum

        # if it is in TRY, convert to EUR before returning
        if k[-5:] == "[try]":
            v /= self.state.data["EUR2TRY"]

        assert isinstance(v, float) or isinstance(v, int)
        return v

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
        line = "-" * 45 + "\n"
        msg = line
        for row in table:
            if row[0] == "cetele":
                msg += (
                    f"| {row[0]:<8} | {row[1]:>8} | {row[2]:>8} | {row[3]:>8} |\n"
                    + line
                )
            else:
                msg += f"| {row[0]:<8} | {row[1]:>8.2f} | {row[2]:>8.2f} | {row[3]:>8.2f} |\n"

                overall += row[3]

        msg += line
        msg += f"| {'overall':<8} | {'':<8} | {'':<8} | {overall:>8.2f} |\n"
        msg += line

        return msg[:-1]
