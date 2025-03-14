import datetime
import logging
import sqlite3
import pathlib
import subprocess
import shlex

from python.calc_model import ExposureCalculator
import python.routing as mar

from .group import exposure_per_activity

import config


class Profile(object):
    def __init__(self, rng, realisation, od_matrix=None):

        self.name = None
        self.name_r = None

        self.home_locations = None
        self.home_query = None
        self.work_locations = None
        self.nr_home_locations = None
        self.nr_work_locations = None

        self.t_start = None
        self.t_end = None
        self.t_delta = None
        self.t_cuts = None

        self.logger = None

        self.routing_engine = mar.Routing(config.osrm_car, config.osrm_bike, config.osrm_foot, config.osrm_train)

        self.rng = rng
        self.realisation = realisation

        self.od_matrixid = od_matrix

    def init(self, name):

        self.name = name
        od = f"_OD{self.od_matrixid:02d}" if self.od_matrixid else ""
        self.name_r = f"{self.name}{od}_{self.realisation}"  # :04d}"

        logpath = pathlib.Path(config.output_dir, "log")
        logpath.mkdir(parents=True, exist_ok=True)
        log_filename = pathlib.Path(logpath, f"{self.name_r}.log")
        self.log_handler = logging.FileHandler(log_filename, "w")
        fmt = logging.Formatter("{asctime} {message}", "%Y-%m-%d %H:%M:%S", style="{")
        self.log_handler.setFormatter(fmt)
        self.logger = logging.getLogger(f"{self.name_r}")
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.INFO)

        self.building_connection = None

        source = sqlite3.connect(config.building_db)
        self.building_connection = sqlite3.connect(":memory:")
        source.backup(self.building_connection)
        self.building_connection.row_factory = sqlite3.Row

        self._init_home_locations("building_locations")
        self._init_work_locations("building_locations")

        if self.od_matrixid:
            fname = pathlib.Path(config.input_dir, "od", f"OD_{self.od_matrixid:02d}")
            self.init_origin_destination(fname)

    def log(self, message):
        self.logger.info(message)

    def init_time(self, start, end, delta, cuts):

        self.t_start = start
        self.t_end = end
        self.t_delta = delta

        self.logger.info(f"Profile start {self.t_start}")
        self.logger.info(f"Profile end   {self.t_end}")
        self.logger.info(f"Profile delta {self.t_delta}")

    def _init_home_locations(self, building_locations):

        where = "" if config.query_home_where == "" else f" WHERE {config.query_home_where}"
        query = f"SELECT COUNT(*) FROM {config.query_home_table} {where}"

        res = self.building_connection.execute(query)
        self.nr_home_locations = res.fetchone()[0]

        self.home_query = f"SELECT {config.query_home_select} FROM {config.query_home_table} {where}"

        self.logger.info(f"Profile init_home_locations {self.home_query}")
        self.logger.info(f"Profile init_home_locations {self.nr_home_locations} entries")

    def _init_work_locations(self, building_locations):

        where = "" if config.query_work_where == "" else f" WHERE {config.query_work_where}"
        query = f"SELECT COUNT(*) FROM {config.query_work_table} {where}"

        res = self.building_connection.execute(query)
        self.nr_work_locations = res.fetchone()[0]

        self.work_query = f"SELECT {config.query_work_select} FROM {config.query_work_table} {where}"

        self.logger.info(f"Profile init_work_locations {self.work_query}")
        self.logger.info(f"Profile init_work_locations {self.nr_work_locations} entries")

    def init_origin_destination(self, filename):
        pass

    def generate_schedules(self):
        self.logger.info("")
        start = datetime.datetime.now()
        self.construct()

        # routing_engine
        self.routing_engine = mar.Routing(config.osrm_car, config.osrm_bike, config.osrm_foot, config.osrm_train)
        end = datetime.datetime.now()
        self.logger.info(f"generating schedules took:    {end - start}")

    def exposure_variables(self):
        pass

    def enrich_schedules(self, poll_filename, props, epsg):
        self.logger.info("")
        start = datetime.datetime.now()

        exp = ExposureCalculator(poll_filename, props, epsg, self.logger, self.routing_engine)

        exp.calc_schedule(f'{self.name_r}')
        self.routing_engine = mar.Routing(config.osrm_car, config.osrm_bike, config.osrm_foot, config.osrm_train)

        end = datetime.datetime.now()
        self.logger.info(f"enrich schedules took:        {end - start}")

    def aggregate(self, props):
        self.logger.info("")

        start = datetime.datetime.now()
        path = pathlib.Path(config.output_dir, f"{self.name_r}.sqlite3")

        exposure_per_activity(path, props)
        end = datetime.datetime.now()
        self.logger.info(f"exposure per activity took:   {end - start}")

        command = f"sqlite3 {path} 'VACUUM;'"
        subprocess.run(shlex.split(command), check=True)

    def commute_distance(self, start_ll_x, start_ll_y, end_ll_x, end_ll_y, osrm_mode):
        return self.routing_engine.distance(start_ll_x, start_ll_y, end_ll_x, end_ll_y, osrm_mode)
