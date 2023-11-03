a simple script to ditch gsheets for budgeting

accepts data from a json file. place each account into a `<category>` and the
script will calculate the current status wrt `<category>-goal`

can calculate conversion if the currency provided. you can specify if that
entry is in that currency via `[usd]`, or if it is a negative entry via `[-]`

Example data file:

```json
{
  "EUR2USD": 1.25,
  "overall": {
    "dailies": {
      "bank0": 10.0,
      "cash": 15.0,
      "savings": 70.0
    },
    "dailies-goal": {
      "expenses": 270.0
    },
    "flexible": {
      "stash": 100,
      "trBank[usd]": 1600,
      "trDebt[-]": 1608
    },
    "flex-goal": {
      "pending": {
        "pending-expense": {
          "plumber": 15
        },
        "pending-income[-]": {
          "debt-collection": 200
        }
      }
    }
  }
}
```

you can specify data file path via a config file, refer to the script for more.

further steps:

- parent editing with a prompt of children
