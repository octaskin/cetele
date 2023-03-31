import datetime
import logging
import json
from pathlib import Path


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
    # TODO: update these to the new features that are added
    edit_prompt = "You want to [E]dit or [D]elete an entry, Q[uit]?: "

    def __init__(self):
        self.read_config()
        self.read()

    def read_config(self):
        logging.debug("Reading config file.")
        config_file = Path.home().joinpath(".config/cetele/config.json")
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as file:
                self.config = json.load(file)
            self.fpath = Path.home().joinpath(self.config["new_path"])
        else:
            exit("Please define a path on the configuration file.")

    def read(self):
        logging.debug("Reading state file.")
        with open(self.fpath, "r") as file:
            self.content = json.load(file)
        self.content[self.config["pocket_money_str"]] = leftover_pocket_money()

    def write(self):
        logging.debug("Writing to state file.")
        with open(self.fpath.with_stem("output"), "w") as file:
            json.dump(self.content, file, indent=2)

    def edit(self, idx):
        key = list(self.content)[int(idx)]
        print(f"Editing -> {key} : {self.content[key]:.2f}")
        if self.is_parent(key):
            exit("This is a parent enrty, editing this is not implemented yet...")
        else:
            try:
                self.content[key] = float(input())
            except:
                print("Please provide proper input")
            # TODO assert input is float
            print(f"New value -> {key} : {self.content[key]:.2f}")
            self.write()

    def delete(self, idx):
        print("Temporarily disabled for json")
        return
        idx = int(idx)
        if input(f"Deleting: {','.join(self.content[idx])} [y\\n]") == "y":
            # First check where this entry occurs as child
            for i, row in enumerate(self.content):
                if len(row) > 2 and self.content[idx][0] in row:
                    print(row)
                    logging.debug(f"Removing child from parent {self.content[i][0]}")
                    self.content[i].remove(self.content[idx][0])
            del self.content[idx]
            # self.write()
        else:
            exit("Aborted.")

    def interactive(self):
        print("Temporarily disabled for json")
        return
        logging.debug("Editing state file.")
        print(self)
        action = self.edit_actions.get(input(self.edit_prompt).capitalize(), None)
        if not action:
            exit("Unexpected argument!")
        elif action == "quit":
            exit("bye...")
        logging.debug(f"You chose {action}.")
        match action:
            case "edit" | "delete":
                idx = int(input(f"Which entry you want to {action}: "))
                getattr(self, action)(idx)
            case "verify":
                self.verify()
        # self.write()

    def verify(self):
        print("Temporarily disabled for json")
        return
        flag = True
        logging.debug("Verifying state file.")
        # Currently unused
        for i, row in enumerate(self.content):
            if self.row_is_child(row):
                # Check whether it is an orphan
                rest = self.content[:i] + self.content[i + 1 :]
                whole = " ".join([" ".join(r) for r in rest])
                if row[0] not in whole + " EUR2TRY":  # currency is an exception
                    print(f"{row[0]} is an orphan, please review or remove!")
                    flag = False
                # Check the decimal part
                if row[1][-3] != "." and not row[1][-2:].isnumeric():
                    print(f"There is a problem with decimal at '{','.join(row)}'")
        if flag:
            print("No problems have been encountered!")
        logging.debug("Verification done.")

    def is_parent(self, key) -> bool:
        return isinstance(self.content[key], list)

    def __str__(self):
        """Only the child items"""
        logging.debug("Listing the state file.")
        res = ""
        max_width = max(map(len, self.content))
        for i, key in enumerate(self.content):
            if self.is_parent(key):
                continue
            res += f"|{i:>2}| {key:<{max_width}} : {self.content[key]:>8.2f}\n"
        return res[:-1]


class Cetele:
    def __init__(self, state: State):
        self.state = state
        self.vals = self.form_state()

    def form_state(self) -> dict:
        logging.debug("Forming state dictionary.")
        res = self.state.content
        return res

    def calculate(self, k: str) -> float:
        logging.debug(f'Querying value of "{k}"')
        v = self.vals[k]

        if isinstance(v, list):
            logging.debug(f"\tCalc by summing {v}")
            sum = 0
            for c in v:
                sum += self.calculate(c)
            self.vals[k] = sum
            v = sum

        # if it is in TRY, convert to EUR before returning
        if k[-5:] == "[try]":
            v /= self.vals["EUR2TRY"]

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
