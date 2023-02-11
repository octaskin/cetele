from csv import reader
from pathlib import Path
import datetime
import logging


def last_day_of_month(any_day):
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return next_month - datetime.timedelta(days=next_month.day)


def leftover_spenditure():
    today = datetime.date.today()
    eomonth = last_day_of_month(today)
    days_left = eomonth - today
    days_left = days_left.days
    return days_left * 15.00


def read_the_state():
    with open(Path.cwd().joinpath("state.csv"), "r") as file:
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


def calculate_value(k: str) -> float:
    logging.debug(f'Querying value of "{k}"')
    v = state.get(k)

    if isinstance(v, list):
        logging.debug(f"\tCalc by summing {v}")
        sum = 0
        for c in v:
            sum += calculate_value(c)
        state[k] = sum
        v = sum

    if k[-5:] == "[try]":
        v /= state["EUR2TRY"]

    assert isinstance(v, float)

    return v


def display_the_cetele():
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
                        val = calculate_value(c)
                    case "goal":
                        val = calculate_value(f"{c}-{i}")
                    case "net":
                        val = col[-2] - col[-1]
                col.append(val)
        table.append(col)

    overall = 0
    for row in table:
        if row[0] == "cetele":
            print(f"| {row[0]:<8} | {row[1]:>8} | {row[2]:>8} | {row[3]:>8} |")
        else:
            print(f"| {row[0]:<8} | {row[1]:>8.2f} | {row[2]:>8.2f} | {row[3]:>8.2f} |")
            overall += row[3]
    print(f"{overall=:7.2f}")


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    state = read_the_state()
    display_the_cetele()
