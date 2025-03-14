import pathlib
import sqlite3

import pandas as pd


def to_csv(pollutant, in_path, exposures):

    for exposure in exposures:
        out_filename = pathlib.Path(f"{pollutant}_{exposure}.csv")

        if out_filename.exists():
            continue

        db_name = pathlib.Path(in_path, f"{exposure}.sqlite3")
        source = sqlite3.connect(db_name)

        selection = "agent_id,mean,std"
        query = f"SELECT {selection} FROM {pollutant}"
        data1 = pd.read_sql(query, source)

        data1.to_csv(out_filename, columns=["agent_id", "mean", "std"], float_format="%.2f", index=False)
