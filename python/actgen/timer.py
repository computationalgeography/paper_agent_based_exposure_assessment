import datetime
import pathlib


class Schedule(object):
    def __init__(self, start_time, end_time, delta, agent_id):
        self.agenda_start_time = start_time
        self.agenda_end_time = end_time
        self.delta = delta

        self.current_time = self.agenda_start_time
        self._activities = []

        self.agent_id = agent_id

        self._act_count = 0

    def add_activity(self, activity):
        self._activities.append(activity)

    def generate(self):
        total_diff = self.agenda_end_time - self.agenda_start_time
        curr_diff = total_diff

        for act in self._activities:
            act._agenda_start = self.agenda_start_time
            act._agenda_end = self.agenda_end_time
            act._time_delta = self.delta

            act._position = self._act_count
            self._act_count += 1

            act.activity(self.current_time)
            assert act._activity_start
            assert act._activity_end

            self.current_time = act._activity_end

            act_diff = act._activity_end - act._activity_start
            curr_diff -= act_diff

        assert curr_diff == datetime.timedelta(
            0), f"activities do not add up to {total_diff}, difference is {curr_diff}"

    def write_schedule(self, output_dir):
        self.agent_id_int = int(self.agent_id)

        filename = pathlib.Path(
            output_dir, f"ws_iter_0_id_{self.agent_id_int}.csv")

        for act in self._activities:
            act._absolute_start = self.current_time
            act.activity(self.current_time)

            self.current_time = act._absolute_end + self.delta

            if self.current_time > self.end_time:
                act._absolute_end = self.end_time

        with open(filename, "w") as content:
            content.write(
                ",start_time,end_time,activity,activity_code,travel_mean,duration\n")
            a_idx = 0
            for act in self._activities:
                content.write(
                    f"{a_idx},{act._absolute_start},{act._absolute_end},{act.name},{act.activity_id},{act.mode},-1\n")
                a_idx += 1
