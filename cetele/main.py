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


def leftover_spenditure():
    today = datetime.date.today()
    days_left = last_day_of_month(today) - today
    return days_left.days * 15.00


def row_is_numeric(row: list[str]) -> bool:
    try:
        float(row[1])
        return True
    except:
        return False


def read_state_file() -> list:
    logging.debug("Reading the state file.")
    with open(file_path, "r") as file:
        out = [r for r in reader(file, delimiter=",")]
    return out


def write_state_file(state: list):
    res = ""
    for row in state:
        res += ",".join(row) + "\n"

    with open(file_path, "w") as file:
        file.write(res)


def display_state_file(state: list):
    logging.debug("Listing the state file.")
    for i, row in enumerate(state):
        print(f"{i}: {','.join(row)}")


def edit_state_file():
    action = input(f"You want to [E]dit or [D]elete an entry, Q[uit]?: ")
    match action.capitalize():
        case "E":
            current = read_state_file()
            logging.debug("I see that you want to edit.")
            logging.debug("Here is the list...")
            display_state_file(current)
            idx = int(input("Which entry you want to work on?: "))
            print(f"Editing: {','.join(current[idx])}")
            if len(current[idx][1:]) > 1:
                exit("This is a parent enrty, editing this is not implemented yet...")
            else:
                current[idx][1] = f"{float(input()):.2f}"
                print(f"New value: {','.join(current[idx])}")
            write_state_file(current)
        case "D":
            current = read_state_file()
            logging.debug("I see that you want to edit.")
            logging.debug("Here is the list...")
            display_state_file(current)
            idx = int(input("Which entry you want to work on?: "))
            key = current[idx][0]
            if input(f"Deleting: {','.join(current[idx])} [y\\n]") == "y":
                del current[idx]
                for i, row in enumerate(current):
                    if len(row) > 2 and key in row:
                        logging.debug(f"Removing child from parent {current[i][0]}")
                        current[i].remove(key)
                write_state_file(current)
            else:
                exit("Aborted.")
        case "Q":
            exit("bye")
        case _:
            exit("Unexpected argument!")

    pass


def form_state(content: list) -> dict:
    state = {}
    for line in content:
        k = line[0]
        if row_is_numeric(line):
            state[k] = float(line[1])
        else:
            state[k] = line[1:]
        logging.debug(f"{k}->{state[k]}")

    state["dailies-goal"] = leftover_spenditure()
    return state


def calculate_value(state: dict, k: str) -> float:
    logging.debug(f'Querying value of "{k}"')
    v = state[k]

    if isinstance(v, list):
        logging.debug(f"\tCalc by summing {v}")
        sum = 0
        for c in v:
            sum += calculate_value(state, c)
        state[k] = sum
        v = sum

    if k[-5:] == "[try]":
        v /= state["EUR2TRY"]

    assert isinstance(v, float)
    return v


def display_the_cetele(state: dict):
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
                        val = calculate_value(state, c)
                    case "goal":
                        val = calculate_value(state, f"{c}-{i}")
                    case "net":
                        val = col[-2] - col[-1]
                col.append(val)
        table.append(col)

    overall = 0
    print("-" * 45)
    for row in table:
        if row[0] == "cetele":
            print(f"| {row[0]:<8} | {row[1]:>8} | {row[2]:>8} | {row[3]:>8} |")
            print("-" * 45)
        else:
            print(f"| {row[0]:<8} | {row[1]:>8.2f} | {row[2]:>8.2f} | {row[3]:>8.2f} |")
            overall += row[3]

    print("-" * 45)
    print(f"| {'overall':<8} | {'':<8} | {'':<8} | {overall:>8.2f} |")
    print("-" * 45)
