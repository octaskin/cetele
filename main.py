from csv import reader
from pathlib import Path

with open(Path.cwd().joinpath("state.csv"), "r") as file:
    content = [r for r in reader(file, delimiter=",")]

state = {}
tree = {}
for k, v in content:
    print(f"{k}->{v}")
    state[k] = float(v)

with open(Path.cwd().joinpath("tree.csv"), "r") as file:
    content = [r for r in reader(file, delimiter=",")]

for r in content:
    tree[r[0]] = r[1:]
    print(f"{r[0]}->{tree[r[0]]}")


def calculate_value(k: str) -> float:
    print(f"querying val of {k}")
    val = state.get(k)
    if val is None:
        print(f"\tcalc by summing {tree[k]}")
        val = 0
        for child in tree[k]:
            val += calculate_value(child)
        state[k] = val
    else:
        print(f"\tval of {k} is already known")
    return val


a = calculate_value("flex")
print(a)
## printing the result table

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
            match i:
                case "status":
                    col.append(calculate_value(c))
                case "goal":
                    col.append(calculate_value(f"{c}-{i}"))
                case "net":
                    col.append(col[-2] - col[-1])
    table.append(col)

for row in table:
    print("| {:1} | {:^4} | {:>4} | {:<3} |".format(*row))
