import datetime
import logging
import json
from csv import reader
from pathlib import Path


class State:
    edit_actions = {"E": "edit", "D": "delete", "Q": "quit"}
    # TODO: update these to the new features that are added
    edit_prompt = "You want to [E]dit or [D]elete an entry, Q[uit]?: "

    def __init__(self):
        config = self.read_config()
        self.fpath = Path.home().joinpath(config["state_file_path"])
        self.pocket_str = config["pocket_money_string"]
        self.content = self.read()

    def read_config(self) -> dict:
        logging.debug("Reading config file.")
        config_file = Path.home().joinpath(".config/cetele/config.json")
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as file:
                return json.load(file)
        else:
            exit("Please define a path on the configuration file.")

    def read(self) -> list:
        logging.debug("Reading state file.")
        with open(self.fpath, "r") as file:
            out = [r for r in reader(file, delimiter=",")]
        return out

    def write(self):
        logging.debug("Writing to state file.")
        res = ""
        for row in self.content:
            res += ",".join(row) + "\n"
        with open(self.fpath, "w") as file:
            file.write(res)

    def edit(self, idx):
        idx = int(idx)
        print(f"Editing: {','.join(self.content[idx])}")
        if len(self.content[idx][1:]) > 1:
            exit("This is a parent enrty, editing this is not implemented yet...")
        else:
            self.content[idx][1] = f"{float(input()):.2f}"
            print(f"New value: {','.join(self.content[idx])}")
        self.write()

    def delete(self, idx):
        idx = int(idx)
        if input(f"Deleting: {','.join(self.content[idx])} [y\\n]") == "y":
            del self.content[idx]
            for i, row in enumerate(self.content):
                if len(row) > 2 and self.content[idx][0] in row:
                    logging.debug(f"Removing child from parent {self.content[i][0]}")
                    self.content[i].remove(self.content[idx][0])
        else:
            exit("Aborted.")

    def interactive(self):
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
        self.write()

    def verify(self):
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

    @staticmethod
    def row_is_child(row: list[str]) -> bool:
        try:
            float(row[1])
            return True
        except:
            return False

    def __str__(self):
        logging.debug("Listing the state file.")
        res = ""
        for i, row in enumerate(self.content):
            if not self.row_is_child(row):
                continue
            res += f"{i}: {','.join(row)}\n"
        return res[:-1]


class Cetele:
    def __init__(self, state: State):
        self.state = state
        self.vals = self.form_state()

    def form_state(self) -> dict:
        logging.debug("Forming state dictionary.")
        res = {}
        for line in self.state.content:
            k = line[0]
            if State.row_is_child(line):
                res[k] = float(line[1])
            else:
                res[k] = line[1:]
            logging.debug(f"{k}->{res[k]}")

        logging.debug(f"Calculating pocket money for entry {self.state.pocket_str}")
        res[self.state.pocket_str] = self.leftover_pocket_money()
        return res

    @staticmethod
    def last_day_of_month(any_day) -> datetime.date:
        # credit: https://stackoverflow.com/a/13565185/13426912
        # The day 28 exists in every month. 4 days later, it's always next month
        next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
        # subtracting the number of the current day brings us back one month
        return next_month - datetime.timedelta(days=next_month.day)

    @staticmethod
    def leftover_pocket_money() -> float:
        today = datetime.date.today()
        days_left = Cetele.last_day_of_month(today) - today
        return days_left.days * 15.00

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

        assert isinstance(v, float)
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
