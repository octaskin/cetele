from csv import reader
from pathlib import Path

with open(Path.home().joinpath("downloads", "cetele.csv"), "r") as file:
    for r in reader(file, delimiter=","):
        print(r)
