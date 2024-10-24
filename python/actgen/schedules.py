import datetime
import pathlib
import sqlite3

import pandas as pd

from .config import ActivityType

import config


def progress(status, remaining, total):
    print(f'Copied {total - remaining} of {total} pages...')


class Schedules(object):
    def __init__(self, output_dir, t_start, t_end, t_delta, props):
        self.output_dir = output_dir

        self.all_schedules = []

        self.total_start = t_start
        self.total_end = t_end
        self.delta_t = t_delta

        self._init_db(output_dir, props)

        self._act_point_idx = 0
        self._act_buffer_idx = 0
        self._act_route_idx = 0

        self._f4_idx = 0
        self._f5_idx = 0

        ds_start_timesteps = pd.date_range('2020-07-01 00:00', periods=24, freq='h')
        ds_end_timesteps = pd.date_range('2020-07-01 01:00', periods=24, freq='h')

        ends = ds_end_timesteps.strftime("%Y-%m-%d %H:%M:%S").tolist()
        ends[23] = '2020-07-01 23:59:00'
        ends[23] = '2020-07-02 00:00:00'

        self.timesteps = pd.DataFrame({'ds_start_timesteps': ds_start_timesteps.strftime("%Y-%m-%d %H:%M:%S").tolist(),
                                       'ds_end_timesteps': ends})

    def _init_db(self, output_dir, props):
        if config.inmem_schedules:
            self.db_con = sqlite3.connect(":memory:")
            self.db_con.execute("pragma journal_mode=wal")
        else:
            path = pathlib.Path(config.output_dir, f"{self.output_dir}.sqlite3")
            path.unlink(missing_ok=True)
            self.db_con.execute("pragma journal_mode=wal")
            self.db_con = sqlite3.connect(path)

        self.db_con.execute('''CREATE TABLE file1 (
activity_id INTEGER PRIMARY KEY,
agent_id INTEGER NOT NULL,
act_idx INTEGER NOT NULL,
time_start timestep NOT NULL,
time_end timestep NOT NULL,
activity_group INTEGER NOT NULL,
activity_index INTEGER NOT NULL
)
''')

        self.db_con.execute('''CREATE TABLE buffer_activities (
activity_index INTEGER PRIMARY KEY,
activity_type INTEGER,
xcoord REAL,
ycoord REAL,
buffer_size REAL,
buffer_method INTEGER
)
''')

        cols = ", ".join(map(str, [f"{key} REAL" for key in props]))

        self.db_con.execute(f'''CREATE TABLE process (
activity_id INTEGER PRIMARY KEY,
agent_id INTEGER NOT NULL,
time_start timestep NOT NULL,
time_end timestep NOT NULL,
activity_group INTEGER NOT NULL,
activity_index INTEGER NOT NULL,
activity_description INTEGER,
{cols}
)
''')

        self.db_con.execute('''CREATE TABLE route_activities (
activity_index INTEGER PRIMARY KEY,
travel_type INTEGER NOT NULL,
travel_descr INTEGER NOT NULL,
xcoord1 REAL,
ycoord1 REAL,
xcoord2 REAL,
ycoord2 REAL
)
''')

        self.db_con.execute('''CREATE TABLE point_activities (
activity_index INTEGER PRIMARY KEY,
activity_type INTEGER,
xcoord REAL,
ycoord REAL
)
''')

    def append(self, stuff):
        self.all_schedules.append(stuff)

    def write(self):
        self.write2()
        self.write6()
        self.write7()
        self.write8()

        self.init_files()
        self.gen()
        self.write_files()

    def init_files(self):
        self.file1 = {}
        self.file4 = {}
        self.file5 = {}
        self.file3 = pd.DataFrame(columns=['activity_index', 'activity_type', 'xcoord', 'ycoord'])
        self.nr_agents = len(self.all_schedules)

    def write2(self):
        ofname = pathlib.Path(self.output_dir, 'file2.csv')

        with open(ofname, 'w') as content:
            content.write('''activity_group,activity_descr
0,unknown
1,point
2,buffer
3,travel''')

    def write6(self):
        ofname = pathlib.Path(self.output_dir, 'file6.csv')

        with open(ofname, 'w') as content:
            content.write('''activity_type,activity_descr,indoor_factor
1,home,0.7
2,work,0.7
3,free_time,0.7''')

    def write7(self):
        ofname = pathlib.Path(self.output_dir, 'file7.csv')

        with open(ofname, 'w') as content:
            content.write('''travel_type,travel_descr,indoor_factor
0,unknown
1,car,1.0
2,bicycle,1.0
3,foot,1.0
4,train,1.0''')

    def write8(self):
        ofname = pathlib.Path(self.output_dir, 'file8.csv')

        with open(ofname, 'w') as content:
            content.write('''buffer_type,buffer_descr
0,unknown
1,sum
2,mean
3,other''')

    def write_files(self):
        return

    def add(self, agent_agenda):
        agent = agent_agenda
        agent_id = agent.agent_id

        for activity in agent._activities:
            start = activity._activity_start
            end = activity._activity_end
            act_type = activity._activity_type

            if act_type == ActivityType.point:
                activity_type = activity.description.value
                values = (activity_type, activity.xcoord, activity.ycoord)
                self.db_con.execute("INSERT INTO point_activities(activity_type, xcoord, ycoord) VALUES (?, ?, ?)", values)
                self._act_point_idx += 1
                activity_group = ActivityType.point.value
                values = (agent_id, activity._position, start, end, activity_group, self._act_point_idx)
                self.db_con.execute("INSERT INTO file1(agent_id,act_idx,time_start,time_end,activity_group,activity_index) VALUES (?, ?, ?, ?, ?, ?)", values)
            elif act_type == ActivityType.buffer:
                activity_type = activity.description.value
                values = (activity_type, activity.xcoord, activity.ycoord, activity.buffersize, activity.buffer_method.value)
                self._act_buffer_idx += 1
                self.db_con.execute("INSERT INTO buffer_activities(activity_type,xcoord,ycoord,buffer_size,buffer_method) VALUES (?, ?, ?, ?, ?)", values)
                activity_group = ActivityType.buffer.value
                values = (agent_id, activity._position, start, end, activity_group, self._act_buffer_idx)
                self.db_con.execute("INSERT INTO file1(agent_id,act_idx,time_start,time_end,activity_group,activity_index) VALUES (?, ?, ?, ?, ?, ?)", values)
            elif act_type == ActivityType.route:
                values = (activity.travel_mode.value, activity.start_x, activity.start_y, activity.dest_x, activity.dest_y, activity._activity_description.value)
                self.db_con.execute("INSERT INTO route_activities(travel_type,xcoord1,ycoord1,xcoord2,ycoord2,travel_descr) VALUES (?, ?, ?, ?, ?, ?)", values)
                self._f5_idx += 1
                self._act_route_idx += 1
                values = (agent_id, activity._position, start, end, 3, self._act_route_idx)
                self.db_con.execute("INSERT INTO file1(agent_id,act_idx,time_start,time_end,activity_group,activity_index) VALUES (?, ?, ?, ?, ?, ?)", values)
            else:
                raise NotImplementedError

        agent_agenda = None

    def create_index(self):
        self.db_con.execute("CREATE INDEX file1_ixd ON file1 (agent_id)")

    def create_indices(self):
        self.db_con.execute("CREATE INDEX point1_ixd ON point_activities (activity_index)")
        self.db_con.execute("CREATE INDEX buffer1_ixd ON buffer_activities (activity_index)")
        self.db_con.execute("CREATE INDEX route1_ixd ON route_activities (activity_index)")
        self.db_con.execute("CREATE INDEX process1_ixd ON process (activity_id)")
        self.db_con.execute("CREATE INDEX process2_ixd ON process (time_start)")
        self.db_con.execute("CREATE INDEX process3_ixd ON process (agent_id)")

    def make(self, agent_id):
        timesteps = self.timesteps
        tmp_dataframe_data = {}
        tmp_dataframe_data_idx = 0
        activity_idx = 1

        df_1 = {}
        with self.db_con:
            f1_idx_0 = 0
            for row in self.db_con.execute("SELECT activity_id,agent_id,time_start,time_end,activity_group,activity_index,act_idx FROM file1 WHERE agent_id=?", (agent_id,)):
                item = {'activity_id': row[0], 'agent_id': row[1], 'time_start': row[2], 'time_end': row[3], 'activity_group': row[4], 'activity_index': row[5], 'act_idx': row[6]}
                df_1[f1_idx_0] = item
                f1_idx_0 += 1

        df_1 = pd.DataFrame.from_dict(df_1, "index")

        act_row_idx = 0
        agent_act = df_1

        row = agent_act.iloc[0]
        start = pd.Timestamp(row['time_start'])
        end = pd.Timestamp(row['time_end'])

        curr_id = row['agent_id']
        curr_group = row['activity_group']
        curr_index = row['activity_index']

        nr_to_test = len(timesteps['ds_start_timesteps']) - 1

        exp_ts_idx = 0
        exp_start = pd.Timestamp(timesteps['ds_start_timesteps'][exp_ts_idx])
        exp_end = pd.Timestamp(timesteps['ds_end_timesteps'][exp_ts_idx])

        last_ts = timesteps['ds_end_timesteps'][timesteps.shape[0] - 1]

        row = agent_act.iloc[act_row_idx]
        start = pd.Timestamp(row['time_start'])
        end = pd.Timestamp(row['time_end'])

        curr_id = row['agent_id']
        curr_group = row['activity_group']
        curr_index = row['activity_index']

        while exp_ts_idx <= nr_to_test:
            if end > exp_end:
                act_end = exp_end
                row = {'activity_id': activity_idx, 'agent_id': curr_id, 'time_start': start, 'time_end': act_end, 'activity_group': curr_group, 'activity_index': curr_index}

                tmp_dataframe_data[tmp_dataframe_data_idx] = row
                tmp_dataframe_data_idx += 1

                activity_idx += 1
                exp_ts_idx += 1

                exp_start = pd.Timestamp(timesteps['ds_start_timesteps'][exp_ts_idx])
                exp_end = pd.Timestamp(timesteps['ds_end_timesteps'][exp_ts_idx])

                start = act_end
            elif start >= exp_start and end < exp_end:
                act_end = end
                row = {'activity_id': activity_idx, 'agent_id': curr_id, 'time_start': start, 'time_end': end, 'activity_group': curr_group, 'activity_index': curr_index}
                tmp_dataframe_data[tmp_dataframe_data_idx] = row
                tmp_dataframe_data_idx += 1

                act_row_idx += 1
                row = agent_act.iloc[act_row_idx]
                start = act_end
                try:
                    end = pd.Timestamp(row['time_end'])
                except ValueError:
                    end = last_ts

                curr_id = row['agent_id']
                curr_group = row['activity_group']
                curr_index = row['activity_index']
                activity_idx += 1

                assert exp_start < exp_end
            elif start >= exp_start and end == exp_end:
                act_end = end
                row = {'activity_id': activity_idx, 'agent_id': curr_id, 'time_start': start, 'time_end': end, 'activity_group': curr_group, 'activity_index': curr_index}
                tmp_dataframe_data[tmp_dataframe_data_idx] = row
                tmp_dataframe_data_idx += 1
                exp_ts_idx += 1

                if exp_ts_idx <= nr_to_test:
                    exp_start = pd.Timestamp(timesteps['ds_start_timesteps'][exp_ts_idx])
                    exp_end = pd.Timestamp(timesteps['ds_end_timesteps'][exp_ts_idx])

                    act_row_idx += 1
                    row = agent_act.iloc[act_row_idx]
                    start = act_end
                    end = pd.Timestamp(row['time_end'])

                    curr_id = row['agent_id']
                    curr_group = row['activity_group']
                    curr_index = row['activity_index']

                    activity_idx += 1
            else:
                raise NotImplementedError

        df2 = pd.DataFrame.from_dict(tmp_dataframe_data, "index")

        total_diff = self.total_end - self.total_start
        curr_diff = total_diff

        values = []

        for idx, item in df2.iterrows():
            values.append((item.iloc[1], item.iloc[2].to_pydatetime(), item.iloc[3].to_pydatetime(), item.iloc[4], item.iloc[5]))
            act_diff = item.iloc[3] - item.iloc[2]
            curr_diff -= act_diff

        assert curr_diff == datetime.timedelta(0), f"activities do not add up to {total_diff}, difference is {curr_diff}\n{df_1}\n{df2}"

        self.db_con.executemany("INSERT INTO process(agent_id,time_start,time_end,activity_group,activity_index) VALUES (?, ?, ?, ?, ?)", values)
        self.db_con.commit()

    def commit(self):
        self.create_index()

        for row in self.db_con.execute("SELECT DISTINCT agent_id FROM file1"):
            home_egid = int(row[0])
            self.make(home_egid)

        self.create_indices()

        if config.inmem_schedules:
            path = pathlib.Path(config.output_dir, f"{self.output_dir}.sqlite3")
            path.unlink(missing_ok=True)

            bck = sqlite3.connect(path)
            with bck:
                self.db_con.backup(bck)
            bck.close()
            self.db_con.close()
        else:
            self.db_con.close()

    def to_csv(self):
        pathlib.Path(self.output_dir).mkdir(parents=False, exist_ok=True)

        self.write2()
        self.write6()
        self.write7()
        self.write8()

        with open(pathlib.Path(self.output_dir, 'file1.csv'), "w") as content:
            content.write("activity_id,agent_id,time_start,time_end,activity_group,activity_index\n")
            for row in self.db_con.execute('SELECT * FROM file1'):
                content.write(','.join(map(str, row)))
                content.write("\n")

        with open(pathlib.Path(self.output_dir, 'file4.csv'), "w") as content:
            content.write("activity_index,activity_type,xcoord,ycoord,buffer_size,buffer_method\n")
            for row in self.db_con.execute('SELECT * FROM buffer_activities'):
                content.write(','.join(map(str, row)))
                content.write("\n")

        with open(pathlib.Path(self.output_dir, 'file5.csv'), "w") as content:
            content.write("activity_index,travel_type,xcoord1,ycoord1,xcoord2,ycoord2\n")
            for row in self.db_con.execute('SELECT * FROM route_activities'):
                content.write(','.join(map(str, row)))
                content.write("\n")

        with open(pathlib.Path(self.output_dir, 'new_sched.csv'), "w") as content:
            content.write("activity_id,agent_id,time_start,time_end,activity_group,activity_index\n")
            for row in self.db_con.execute('SELECT * FROM process ORDER BY time_start'):
                content.write(','.join(map(str, row)))
                content.write("\n")

        q = "SELECT * FROM point_activities"
        df = pd.read_sql_query(q, self.db_con)
        df.to_csv(pathlib.Path(self.output_dir, 'file3point_activities.csv'), index=False)
