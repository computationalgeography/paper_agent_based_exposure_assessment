import sys
import pickle
import numpy as np

from osgeo import ogr, gdal

import python.actgen as ag
import python.routing as mar
from python import ODMatrixSelect

from python.profiles import Profile

import datetime
import configparser

import config
from python.actgen.config import ActivityDescription as ad
from python.actgen.config import BufferCalculation as bd
from python.actgen.config import CommuteType as ct

gdal.UseExceptions()


class CommuteWorkday(Profile):
    def __init__(self, rng, realisation, od_matrix=None):
        Profile.__init__(self, rng, realisation, od_matrix)

        self._rng = rng
        self.od_matrix = ODMatrixSelect(rng)

        self.init("commute_workday")

        self.r = mar.Routing(config.osrm_car, config.osrm_bike, config.osrm_foot, config.osrm_train)

        self.max_eucl = 180000
        self.min_eucl = 25

        self.od_matrix_id = od_matrix

    def exposure_variables(self):
        return config.workday

    def init_origin_destination(self, filename):
        self.logger.info(f"init_origin_destination: {filename}")
        self.od_matrix.init(filename)

    def distance(self, x1, y1, x2, y2):

        wkt = f"POINT ({x1} {y1})"
        point1 = ogr.CreateGeometryFromWkt(wkt)

        wkt = f"POINT ({x2} {y2})"
        point2 = ogr.CreateGeometryFromWkt(wkt)

        dis = point1.Distance(point2)

        return dis

    def pot_work_location(self, area_id):
        query = f"SELECT idx,postcode,rd_x,rd_y,wgs_x,wgs_y FROM work WHERE postcode2={area_id}"
        sql = self.building_connection.execute(query)
        res = sql.fetchall()
        nr_pot_work_locations = len(res)

        pot_work_idx = self._rng.choice(nr_pot_work_locations, 1)[0]
        row = res[pot_work_idx]

        pot_work_x = round(row["rd_x"], 6)
        pot_work_y = round(row["rd_y"], 6)
        pot_work_ll_x = round(row["wgs_x"], 6)
        pot_work_ll_y = round(row["wgs_y"], 6)

        return pot_work_x, pot_work_y, pot_work_ll_x, pot_work_ll_y

    def commute_mode_probs(self, distance):
        assert distance >= 0

        probs = None

        dist1 = 1000
        dist2 = 10000

        if distance < dist1:
            probs = [0.5, 0.5, 0, 0]
        if distance >= dist1 and distance < dist2:
            probs = [0, 0.5, 0.5, 0]
        if distance >= dist2:
            probs = [0, 0, 0.5, 0.5]

        assert sum(probs) == 1.0

        osrm = [mar.Foot, mar.Bike, mar.Car, mar.Train]
        act = [ct.foot, ct.bike, ct.car, ct.train]
        x = np.arange(4)
        mode_idx = self.rng.choice(x, size=1, p=probs)[0]

        return osrm[mode_idx], act[mode_idx]

    def construct(self):
        self.logger.info("")
        self.logger.info(f"OD1 generate_schedules")
        output_dir = f"{self.name_r}"

        schedules = ag.Schedules(output_dir, self.t_start, self.t_end, self.t_delta, self.exposure_variables())

        # in minutes
        min_commute_time = 5
        max_commute_time = 150

        self.logger.info(f"OD1 generate_schedules commute min/max: {min_commute_time} {max_commute_time}")

        count_agents = 0
        count_exceed = 0
        count_home_mun = 0
        count_limited_work_loc = 0

        cnt = 1
        for row in self.building_connection.execute(self.home_query):
            agent_id = int(row["agent_id"])
            home_x = row["home_x"]
            home_y = row["home_y"]
            home_ll_x = row["wgs_x"]
            home_ll_y = row["wgs_y"]

            work_x = None
            work_y = None
            work_ll_x = None
            work_ll_y = None

            duration_car = None
            duration_bike = None
            duration_train = None
            duration_foot = None

            home_municipality = int(row["postcode"])

            if cnt % 250 == 0:
                self.logger.info(f"OD1 generate_schedules {cnt}")

            suitable_workloc = False

            redraw = 0
            redraw_max = 20
            exceeds_redraw = False

            while not suitable_workloc:
                distance = None
                duration = None
                dest_work_municipality = None

                dest_work_municipality = self.od_matrix.obtain(home_municipality)
                if dest_work_municipality < 0:
                    dest_work_municipality = home_municipality
                    self.logger.info(f"   used home municipality due to no OD ({home_municipality})")

                if redraw > redraw_max:
                    dest_work_municipality = home_municipality
                    self.logger.info(f"   used home municipality due to exceedance ({home_municipality})")

                if dest_work_municipality > 0:
                    work_x, work_y, work_ll_x, work_ll_y = self.pot_work_location(dest_work_municipality)

                    work_distance = self.distance(home_x, home_y, work_x, work_y)
                    if work_distance > self.min_eucl and work_distance < self.max_eucl:
                        # get commute mode based on distance
                        osrm_mode, act_mode = self.commute_mode_probs(work_distance)
                        distance, duration = self.r.distance(home_ll_x, home_ll_y, work_ll_x, work_ll_y, osrm_mode)
                        if duration > 0 and duration < max_commute_time:
                            suitable_workloc = True
                            assert duration > 0, f"{home_ll_x}, {home_ll_y}, {work_ll_x}, {work_ll_y}, {osrm_mode}, {distance}, {duration}"
                            assert distance > 0, f"{home_ll_x}, {home_ll_y}, {work_ll_x}, {work_ll_y}, {osrm_mode}, {distance}, {duration}"
                else:
                    raise NotImplementedError

                redraw += 1

            assert distance > 0
            assert duration > 0
            cnt += 1

            end_min = 6 * 60 + 30
            end_max = 7 * 60 + 30
            x = np.arange(end_min, end_max)
            act_end = self.rng.choice(x, size=1)[0] * self.t_delta

            home_1 = ag.Buffer_Fixed(ad.home, home_x, home_y, act_end, 50)

            route_1 = ag.Commute(ad.commute_home_to_work, home_ll_x, home_ll_y, work_ll_x, work_ll_y, act_mode, duration)

            delta = 8 * 60 * self.t_delta
            work = ag.Buffer_Fixed(ad.work, work_x, work_y, delta, 50)

            route_2 = ag.Commute(ad.commute_work_to_home, work_ll_x, work_ll_y, home_ll_x, home_ll_y, act_mode, duration)

            home_2 = ag.Buffer_Final(ad.home, home_x, home_y, act_end, 50)

            schedule = ag.Schedule(self.t_start, self.t_end, self.t_delta, agent_id)
            schedule.add_activity(home_1)
            schedule.add_activity(route_1)
            schedule.add_activity(work)
            schedule.add_activity(route_2)
            schedule.add_activity(home_2)
            schedule.generate()
            schedules.add(schedule)

        schedules.commit()
