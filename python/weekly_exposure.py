import copy
import csv
import sys
import math
import sqlite3
import pathlib

import numpy as np

import pandas as pd


class Weekly(object):
    def __init__(self, directory, filename, realisations, combine, output_path):

        self.directory = directory
        self.db_con = sqlite3.connect(":memory:")
        self.combine = combine

        self.out_path = pathlib.Path(output_path, f"{filename}.sqlite3")
        if self.out_path.exists():
            return

        self._init_db(realisations)

        for idx in range(1, realisations + 1):
            self.do_realisation(idx)

        self.stats("no2")
        self.stats("pm25")
        self.stats("noise")

        self.db_con.commit()

        dest = sqlite3.connect(self.out_path)

        with dest:
            self.db_con.backup(dest)
        dest.close()
        self.db_con.close()

    def _init_db(self, nr_realisations):

        realisations = range(1, nr_realisations + 1)
        columns = ",".join(map("R{} REAL".format, realisations))

        cmd = f"""CREATE TABLE no2 (
agent_id INTEGER PRIMARY KEY,
{columns},
mean REAL,
std REAL,
var REAL,
min REAL,
max REAL
)"""
        self.db_con.execute(cmd)

        in_path = pathlib.Path(self.directory, f"{self.combine[0][1]}_1.sqlite3")
        assert in_path.exists(), in_path

        agents = sqlite3.connect(in_path)

        for row in agents.execute('SELECT DISTINCT agent_id FROM file1'):
            self.db_con.execute("INSERT INTO no2(agent_id) VALUES (?)", row)

        self.db_con.execute("CREATE INDEX no2_agent_ixd ON no2 (agent_id)")

        cmd = f"""CREATE TABLE pm25 (
agent_id INTEGER PRIMARY KEY,
{columns},
mean REAL,
std REAL,
var REAL,
min REAL,
max REAL
)"""
        self.db_con.execute(cmd)

        agents = sqlite3.connect(in_path)

        for row in agents.execute('SELECT DISTINCT agent_id FROM file1'):
            self.db_con.execute("INSERT INTO pm25(agent_id) VALUES (?)", row)

        self.db_con.execute("CREATE INDEX pm25_agent_ixd ON pm25 (agent_id)")

        cmd = f"""CREATE TABLE noise (
agent_id INTEGER PRIMARY KEY,
{columns},
mean REAL,
std REAL,
var REAL,
min REAL,
max REAL
)"""
        self.db_con.execute(cmd)

        agents = sqlite3.connect(in_path)

        for row in agents.execute('SELECT DISTINCT agent_id FROM file1'):
            self.db_con.execute("INSERT INTO noise(agent_id) VALUES (?)", row)

        self.db_con.execute("CREATE INDEX no2_agent_ixd2 ON noise (agent_id)")

        self.db_con.commit()

    def to_db(self, val):
        return 10 * math.log10(val)

    def do_realisation(self, idx):

        databases = []

        for item in self.combine:
            if item[2]:
                fname = pathlib.Path(self.directory, f"{item[1]}_{idx:d}.sqlite3")
            else:
                fname = pathlib.Path(self.directory, f"{item[1]}_1.sqlite3")

            assert fname.exists(), fname

            source = sqlite3.connect(fname)

            tmp_conection = sqlite3.connect(":memory:")
            source.backup(tmp_conection)
            source.close()

            databases.append(tmp_conection)

        col_name = f"R{idx}"

        count = 1

        for row in self.db_con.execute('SELECT DISTINCT agent_id FROM no2'):

            count += 1

            agent_id = row[0]

            no2_value = 0
            pm25_value = 0
            noise_value = 0
            sum_factor = 0

            # get the agent values from the realisation databases
            for idx, item in enumerate(self.combine):
                factor = self.combine[idx][0]
                cur = databases[idx].cursor()
                cur.execute("SELECT * FROM exp_day WHERE agent_id=?", row)
                values = cur.fetchone()
                exp_1 = values[1]
                exp_2 = values[2]
                exp_3 = values[3]

                if no2_value is not None and exp_1 is not None:
                    no2_value += factor * exp_1
                else:
                    no2_value = None

                if pm25_value is not None and exp_2 is not None:
                    pm25_value += factor * exp_2
                else:
                    pm25_value = None

                if noise_value is not None and exp_3 is not None:
                    noise_value += factor * exp_3
                else:
                    noise_value = None

                sum_factor += factor

            if no2_value is not None:
                no2_value /= sum_factor
            else:
                no2_value = "NULL"

            if pm25_value is not None:
                pm25_value /= sum_factor
            else:
                pm25_value = "NULL"

            if noise_value is not None:
                noise_value /= sum_factor
                noise_value = self.to_db(noise_value)
            else:
                noise_value = "NULL"

            no2 = f"UPDATE no2 SET {col_name}={no2_value} WHERE agent_id={agent_id}"
            pm25 = f"UPDATE pm25 SET {col_name}={pm25_value} WHERE agent_id={agent_id}"
            noise = f"UPDATE noise SET {col_name}={noise_value} WHERE agent_id={agent_id}"

            self.db_con.execute(no2)
            self.db_con.execute(pm25)
            self.db_con.execute(noise)

        for d in databases:
            d.close()

    def stats(self, pollutant):

        for row in self.db_con.execute(f'SELECT * FROM {pollutant}'):
            agent_id = row[0]

            db_values = row[1:len(row) - 5]
            db_values = [np.nan if x == None else x for x in db_values]
            values = np.array(db_values)

            updates = (np.mean(values), np.std(values), np.var(values), np.min(values), np.max(values), agent_id)
            query = f"UPDATE {pollutant} SET mean=?,std=?,var=?,min=?,max=? WHERE agent_id=?"

            self.db_con.cursor().execute(query, updates)
