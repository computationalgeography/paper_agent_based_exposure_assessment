import pathlib
import sqlite3
import numpy as np

from osgeo import gdal
import pandas as pd
import datetime

from .spatial_context import SpatialContext
from .factors import EnvFactors
from .actgen.config import ActivityType, BufferCalculation

import config


gdal.UseExceptions()


class ExposureCalculator(object):
    def __init__(self, filename, props, epsg, logger, routing_engine):

        self.logger = logger
        self.epsg = epsg
        self.props = props

        phen_name = "concentration"
        pset_name = "area"

        self._exposure = EnvFactors(filename, phen_name, pset_name, self.props)
        self._spatial_context = SpatialContext(routing_engine, self._exposure.extent(), self.epsg)

    def calc_schedule(self, data_dir):
        self.data_dir = data_dir
        path = pathlib.Path(config.output_dir, f"{self.data_dir}.sqlite3")
        source = sqlite3.connect(path)
        self.conn = sqlite3.connect(":memory:")
        source.backup(self.conn)
        source.close()

        self.conn.row_factory = sqlite3.Row
        self.conn.execute("pragma journal_mode=wal")

        self.calc()

        dest = sqlite3.connect(path)

        with dest:
            self.conn.backup(dest)
        dest.close()
        self.conn.close()

    def travel_type(self, t_type):
        act = self._travel_type.loc[self._travel_type['travel_type'] == t_type]
        v = act['travel_descr']
        assert len(v) == 1

        return v.values[0]

    def buffer_method(self, buff_method):
        act = self._buffer_method.loc[self._buffer_method['buffer_type'] == buff_method]

        return act['buffer_descr'].values[0]

    def calc(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM process")
        all_activities = cur.fetchone()[0]
        # all_activities

        count = 0

        t_start = datetime.datetime.now()
        self.logger.info(f"activity {count:8d}/{all_activities} {t_start}")
        for row in self.conn.execute('SELECT activity_id,agent_id,time_start,activity_group,activity_index FROM process ORDER BY time_start'):
            count += 1

            activity_id = row[0]
            activity_start = row[2]
            activity_group = int(row[3])
            activity_index = int(row[4])

            if count % 25000 == 0:
                t_end = datetime.datetime.now()
                self.logger.info(f"activity {count:8d}/{all_activities} {100 * count / all_activities:.1f} {datetime.datetime.now()} {t_end - t_start} schedule at: {activity_start}")
                t_start = t_end

            # get exposure timestep nearest to current activity
            activity_start = self._exposure._nearest_timestep(pd.to_datetime(activity_start))

            if activity_group == ActivityType.point.value:
                # Query current activity
                cur = self.conn.cursor()
                cur.execute("SELECT activity_type,xcoord,ycoord FROM point_activities WHERE activity_index=?", (activity_index,))
                p_idx = cur.fetchone()

                activity_type = p_idx[0]
                xcoord = p_idx[1]
                ycoord = p_idx[2]

                # Get spatial context
                scontext = self._spatial_context.point(xcoord, ycoord)
                assert scontext

                updates = {}

                for prop in self.props:
                    scontext_values = self._exposure.data(activity_start, scontext, prop)

                    shape_x, shape_y = scontext_values.shape
                    assert shape_x == 1
                    assert shape_y == 1

                    point_value = scontext_values[0][0]

                    if np.isnan(point_value):
                        point_value = None
                    elif point_value < -10:
                        point_value = None
                    else:
                        point_value = float(np.maximum(0.0, point_value))

                    updates[prop] = point_value

                a = ",".join(map(str, [f"{key}=?" for key, value in updates.items()]))
                sql_tup = [(v) for k, v in updates.items()]
                sql_tup.append(activity_type)
                sql_tup.append(activity_id)

                query = f"UPDATE process SET {a},activity_description=? WHERE activity_id=?"
                self.conn.execute(query, tuple(sql_tup))

            elif activity_group == ActivityType.buffer.value:
                # Query current activity
                cur = self.conn.cursor()
                cur.execute("SELECT activity_type,xcoord,ycoord,buffer_size,buffer_method FROM buffer_activities WHERE activity_index=?", (activity_index,))
                b_idx = cur.fetchone()

                activity_type = b_idx[0]
                xcoord = b_idx[1]
                ycoord = b_idx[2]

                buffer_size = b_idx[3]
                buff_method = b_idx[4]

                scontext = self._spatial_context.buffer(xcoord, ycoord, buffer_size)
                assert scontext

                updates = {}

                for prop in self.props:

                    scontext_raster = self._exposure.data(activity_start, scontext, prop)
                    # correct for broken no_data values
                    scontext_raster = np.where(scontext_raster < -10, np.nan, scontext_raster)
                    # correct for some exposure values below 0
                    scontext_raster = np.maximum(0.0, scontext_raster)

                    shape_x, shape_y = scontext_raster.shape
                    assert shape_x == shape_y

                    buffer_value = None

                    if buff_method == BufferCalculation.mean.value:
                        buffer_value = float(np.nanmean(scontext_raster))
                    elif buff_method == BufferCalculation.unknown.value:
                        raise RuntimeError
                    elif buff_method == BufferCalculation.sum.value:
                        buffer_value = float(np.nansum(scontext_raster))
                    else:
                        raise NotImplementedError

                    updates[prop] = buffer_value

                a = ",".join(map(str, [f"{key}=?" for key, value in updates.items()]))
                sql_tup = [(v) for k, v in updates.items()]
                sql_tup.append(activity_type)
                sql_tup.append(activity_id)

                query = f"UPDATE process SET {a},activity_description=? WHERE activity_id=?"
                self.conn.execute(query, tuple(sql_tup))
            elif activity_group == ActivityType.route.value:
                # Query current activity
                cur = self.conn.cursor()
                cur.execute("SELECT travel_type,xcoord1,ycoord1,xcoord2,ycoord2 FROM route_activities WHERE activity_index=?", (activity_index,))
                r_idx = cur.fetchone()

                t_type = r_idx[0]

                xcoord1 = r_idx[1]
                ycoord1 = r_idx[2]

                xcoord2 = r_idx[3]
                ycoord2 = r_idx[4]

                scontext = None

                if t_type >= 0:
                    scontext = self._spatial_context.route(xcoord1, ycoord1, xcoord2, ycoord2, t_type, 4326)

                assert scontext

                for prop in self.props:
                    if t_type >= 0:
                        scontext_raster = self._exposure.data(activity_start, scontext, prop)
                        scontext_raster = np.where(scontext_raster < -10, np.nan, scontext_raster)
                        scontext_values = np.maximum(0.0, scontext_raster)
                        shape_x, shape_y = scontext_values.shape
                        route_value = -9

                        if np.isnan(scontext_values).all():
                            route_value = None
                        else:
                            route_value = float(np.nanmean(scontext_values))

                        updates[prop] = route_value
                    else:
                        updates[prop] = -7

                a = ",".join(map(str, [f"{key}=?" for key, value in updates.items()]))
                sql_tup = [(v) for k, v in updates.items()]
                sql_tup.append(t_type)
                sql_tup.append(activity_id)

                query = f"UPDATE process SET {a},activity_description=? WHERE activity_id=?"
                self.conn.execute(query, tuple(sql_tup))
            else:
                raise NotImplementedError

        self.conn.commit()
