import pathlib

import numpy as np

from python.profiles import Profile

import python.actgen as ag
from python.actgen.config import ActivityDescription as ad

import config


class HomemakerBufferWorkday(Profile):
    def __init__(self, rng, realisation, od_matrix=None):
        Profile.__init__(self, rng, realisation, od_matrix)

        self.init("homemaker_buffer_workday")

    def exposure_variables(self):
        return config.workday

    def construct(self):
        output_dir = pathlib.Path(f"{self.name_r}")
        schedules = ag.Schedules(output_dir, self.t_start, self.t_end, self.t_delta, self.exposure_variables())

        for row in self.building_connection.execute(self.home_query):
            xcoord = row["home_x"]
            ycoord = row["home_y"]

            schedule = ag.Schedule(self.t_start, self.t_end, self.t_delta, row["agent_id"])

            # 0-8
            # two hours between 8-23
            end_min = 8 * 60
            end_max = 21 * 60
            x = np.arange(end_min, end_max)
            act_end = self.rng.choice(x, size=1)[0] * self.t_delta

            home1 = ag.Buffer_Fixed(ad.home, xcoord, ycoord, act_end, 50)

            delta = 120 * self.t_delta
            leisure = ag.Buffer_Fixed(ad.leisure, xcoord, ycoord, delta, self.od_matrixid)

            home2 = ag.Buffer_Final(ad.home, xcoord, ycoord, act_end, 50)

            schedule.add_activity(home1)
            schedule.add_activity(leisure)
            schedule.add_activity(home2)
            schedule.generate()
            schedules.add(schedule)

        schedules.commit()
