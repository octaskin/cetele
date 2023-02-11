import datetime
import logging
import json
from csv import reader
from pathlib import Path

config_file = Path.home().joinpath(".config/cetele/config.json")
if config_file.exists():
    with open(config_file, "r", encoding="utf-8") as file:
        data_dir = json.load(file)["data_dir"]
else:
    exit("Please define a data directory on the configuration file.")

data_path = Path.home().joinpath(data_dir)
# order_file = data_path.joinpath("shoppy_order.txt")
# store_file = data_path.joinpath("store-layout.txt")
# list_file = data_path.joinpath("shoppy_list.md")


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


def read_the_state():
    with open(data_path.joinpath("state.csv"), "r") as file:
        content = [r for r in reader(file, delimiter=",")]

    state = {}
    for line in content:
        k = line[0]
        try:
            state[k] = float(line[1])
        except:
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
