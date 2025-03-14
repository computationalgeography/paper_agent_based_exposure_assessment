from datetime import datetime
import sqlite3


def exposure_per_activity(filename, props):
    source = sqlite3.connect(filename)

    conection = sqlite3.connect(":memory:")
    source.backup(conection)
    source.close()

    conection.execute("DROP TABLE IF EXISTS exp_act")
    conection.execute("DROP TABLE IF EXISTS exp_day")

    cols = ", ".join(map(str, [f"{key} REAL" for key in props]))

    conection.execute(f'''CREATE TABLE exp_act (
idx INTEGER PRIMARY KEY,
agent_id INTEGER NOT NULL,
act_idx INTEGER NOT NULL,
duration INTEGER NOT NULL,
activity_type INTEGER NOT NULL,
activity_description INTEGER,
commute_mode INTEGER,
{cols}
)
''')

    conection.execute(f'''CREATE TABLE exp_day (
agent_id INTEGER PRIMARY KEY,
{cols}
)
''')

    start_t = datetime.now()

    for agents in conection.execute("SELECT DISTINCT agent_id FROM file1"):
        agent_id = agents[0]

        a = ",".join(map(str, [f"{value}=?" for value in props]))
        b = [f"{value}" for value in props]
        c = ",".join(map(str, [f"{value}" for value in props]))
        d = ", ".join(map(str, ["?" for value in props]))

        act_cnt = 0

        day_value = {}
        for p in props:
            day_value[p] = 0

        for activities in conection.execute("SELECT time_start,time_end FROM file1 WHERE agent_id=?", (agent_id,)):
            agent_id = agents[0]

            act_start = activities[0]
            act_end = activities[1]
            act_delta = datetime.fromisoformat(act_end) - datetime.fromisoformat(act_start)
            act_delta_minutes = int(act_delta.total_seconds() / 60)
            query = f"SELECT time_start,time_end,activity_group,activity_index,activity_description,{c} FROM process WHERE agent_id=? AND time_start>=? AND time_end<=?"
            query_tuple = []
            query_tuple.append(agent_id)
            query_tuple.append(act_start)
            query_tuple.append(act_end)

            act_value = {}
            act_value["agent_id"] = agent_id
            act_value["act_idx"] = act_cnt
            act_cnt += 1
            act_value["duration"] = act_delta_minutes

            for p in props:
                act_value[p] = 0

            for split in conection.execute(query, tuple(query_tuple)):
                split_start = split[0]
                split_end = split[1]
                activity_group = split[2]
                activity_index = split[3]

                route_descr_val = None
                if activity_group == 3:
                    cur = conection.cursor()
                    cur.execute("SELECT travel_descr FROM route_activities WHERE activity_index=?", (activity_index,))
                    route_descr_val = cur.fetchone()[0]

                activity_description = split[4]
                act_value["type"] = activity_group
                act_value["descr"] = activity_description
                act_value["commute_mode"] = route_descr_val

                if activity_group == 3:

                    act_value["descr"] = route_descr_val
                    act_value["commute_mode"] = activity_description

                split_delta = datetime.fromisoformat(split_end) - datetime.fromisoformat(split_start)
                split_delta_minutes = int(split_delta.total_seconds() / 60)

                for idx, p in enumerate(props):
                    value = None
                    value = split[5 + idx]
                    if value is not None:
                        if act_value[p] is not None:
                            act_value[p] += value * split_delta_minutes
                        if day_value[p] is not None:
                            day_value[p] += value * split_delta_minutes
                    else:
                        act_value[p] = None
                        day_value[p] = None

            for p in props:
                if act_value[p] is not None:
                    act_value[p] /= act_delta_minutes

            insert_query = f"INSERT INTO exp_act(agent_id,act_idx,duration,activity_type,activity_description,commute_mode,{c}) VALUES (?, ?, ?, ?, ?, ?, {d})"
            insert_values = [act_value["agent_id"], act_value["act_idx"], act_value["duration"], act_value["type"], act_value["descr"], act_value["commute_mode"]]

            for p in props:
                insert_values.append(act_value[p])

            conection.execute(insert_query, insert_values)

        for p in props:
            if day_value[p] is not None:
                day_value[p] /= 1440

        insert_query = f"INSERT INTO exp_day(agent_id,{c}) VALUES (?, {d})"
        insert_values = [act_value["agent_id"]]

        for p in props:
            insert_values.append(day_value[p])

        conection.execute(insert_query, insert_values)

    conection.execute("CREATE INDEX exp_act_ixd ON exp_act (agent_id)")
    conection.execute("CREATE INDEX exp_day_ixd ON exp_day (agent_id)")
    conection.commit()

    dest = sqlite3.connect(filename)

    with dest:
        conection.backup(dest)
    dest.close()
    conection.close()
