import datetime
import logging
import json
from csv import reader
from pathlib import Path

config_file = Path.home().joinpath(".config/cetele/config.json")
if config_file.exists():
    with open(config_file, "r", encoding="utf-8") as file:
        state_file_path = json.load(file)["state_file_path"]
else:
    exit("Please define a path on the configuration file.")

file_path = Path.home().joinpath(state_file_path)


def last_day_of_month(any_day):
    # credit: https://stackoverflow.com/a/13565185/13426912
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return next_month - datetime.timedelta(days=next_month.day)


class State:
    edit_actions = {"E": "edit", "D": "delete", "Q": "quit"}

    def __init__(self):
        self.fpath = self.read_config()
        self.state = self.read()

    def read_config(self):
        config_file = Path.home().joinpath(".config/cetele/config.json")
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as file:
                state_file_path = json.load(file)["state_file_path"]
        else:
            exit("Please define a path on the configuration file.")

        return Path.home().joinpath(state_file_path)

    def read(self):
        logging.debug("Reading the state file.")
        with open(self.fpath, "r") as file:
            out = [r for r in reader(file, delimiter=",")]
        return out

    def write(self):
        res = ""
        for row in self.state:
            res += ",".join(row) + "\n"

        with open(self.fpath, "w") as file:
            file.write(res)

    def edit(self):
        print(self)
        action = self.edit_actions.get(
            input(f"You want to [E]dit or [D]elete an entry, Q[uit]?: ").capitalize(),
            None,
        )
        if not action:
            exit("Unexpected argument!")
        elif action == "Q":
            exit("bye...")
        logging.debug(f"You chose {action}.")
        idx = int(input(f"Which entry you want to {action}: "))
        print(f"{action}ing: {','.join(self.state[idx])}")
        match action:
            case "edit":
                if len(self.state[idx][1:]) > 1:
                    exit(
                        "This is a parent enrty, editing this is not implemented yet..."
                    )
                else:
                    self.state[idx][1] = f"{float(input()):.2f}"
                    print(f"New value: {','.join(self.state[idx])}")
            case "delete":
                if input(f"Deleting: {','.join(self.state[idx])} [y\\n]") == "y":
                    del self.state[idx]
                    for i, row in enumerate(self.state):
                        if len(row) > 2 and self.state[idx][0] in row:
                            logging.debug(
                                f"Removing child from parent {self.state[i][0]}"
                            )
                            self.state[i].remove(self.state[idx][0])
                else:
                    exit("Aborted.")
        self.write()

    def verify(self):
        # currently unused
        for i, row in enumerate(self.state):
            if row_is_numeric(row):
                rest = self.state[:i] + self.state[i + 1 :]
                whole = " ".join([" ".join(r) for r in rest])
                if row[0] not in whole + " EUR2TRY":  # currency is an exception
                    print(f"{row[0]} is an orphan, please review or remove!")

    @staticmethod
    def row_is_numeric(row: list[str]) -> bool:
        try:
            float(row[1])
            return True
        except:
            return False

    def __str__(self):
        # TODO: test this, I'm not sure to print or return string
        logging.debug("Listing the state file.")
        res = ""
        for i, row in enumerate(self.state):
            if not row_is_numeric(row):
                continue
            res += f"{i}: {','.join(row)}\n"
        return res[:-1]


class Cetele:
    def __init__(self, state: State):
        self.vals = self.form_state(state.state)
        self.state = state

    @staticmethod
    def form_state(content: list) -> dict:
        res = {}
        for line in content:
            k = line[0]
            if row_is_numeric(line):
                res[k] = float(line[1])
            else:
                res[k] = line[1:]
            logging.debug(f"{k}->{res[k]}")

        res["dailies-goal"] = Cetele.leftover_spenditure()
        return res

    @staticmethod
    def leftover_spenditure():
        today = datetime.date.today()
        days_left = last_day_of_month(today) - today
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

        if k[-5:] == "[try]":
            v /= self.vals["EUR2TRY"]

        assert isinstance(v, float)
        return v

    def __str__(self):
        cols = ["cetele", "savings", "flex", "dailies"]
        idx = ["status", "goal", "net"]

        table = []
        for c in cols:
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
