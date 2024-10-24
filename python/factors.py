import numpy as np
import pandas as pd

import lue.data_model as ldm
import campo


class EnvFactors(object):
    def __init__(self, filename, phenomenon, property_set, prop, regular=True):
        """ Initialise with LUE dataset """
        self.filename = filename
        self.phenomenon = phenomenon
        self.property_set = property_set
        self.prop = prop
        self.regular = regular

        assert len(self.prop) > 0

        if not regular:
            raise NotImplementedError

        self.dataset = ldm.open_dataset(filename)

        if self.regular:
            dataframe = campo.dataframe.select(self.dataset.concentration, property_names=prop)
            self.area_agent = dataframe[phenomenon][property_set][self.prop[0]][0]
            self.area_propertyset = dataframe[phenomenon][property_set]

            self.cellsize_x = self.area_agent.xcoord.data[1] - self.area_agent.xcoord.data[0]
            self.cellsize_y = self.area_agent.ycoord.data[1] - self.area_agent.ycoord.data[0]

            # Upper left coordinates of the entire are
            self.xul = round(self.area_agent.xcoord.data[0], 4)
            self.yul = round(self.area_agent.ycoord.data[-1] + self.cellsize_y, 4)

            self.xlr = round(self.area_agent.xcoord.data[0] + self.cellsize_x * len(self.area_agent.xcoord), 4)
            self.ylr = round(self.area_agent.ycoord.data[0], 4)

            self.xul = self.area_agent.xcoord.data[0]
            self.yul = self.area_agent.ycoord.data[-1] + self.cellsize_y

            self.xlr = self.area_agent.xcoord.data[0] + self.cellsize_x * len(self.area_agent.xcoord)
            self.ylr = self.area_agent.ycoord.data[0]

            self.ds_timesteps = pd.DatetimeIndex(self.area_agent.time.data)

            self.nr_timesteps = self.area_agent.shape[0]
            self.nr_rows = self.area_agent.shape[1]
            self.nr_cols = self.area_agent.shape[2]

    def nr_timeboxes(self):
        """ Returns number fof time boxes in dataset """
        pass

    def timebox_interval(self, index):
        """ Returns timebox for specific index """
        pass

    def timebox_resolution(self):
        """ Returns """
        pass

    def timesteps(self):
        """ Returns list of all timesteps in the dataset """
        return self.ds_timesteps

    def _nearest_timestep(self, timestep):
        # First round down to the nearest hour
        timestep = timestep.replace(second=0, minute=0)

        # Then find the nearest previous timestep
        # Not super efficient, but should work as first version
        min_val = 1e31
        old_min = 1e31
        ts_val = None
        for t in self.ds_timesteps:
            diff = (timestep - t).total_seconds()
            if diff >= 0:
                min_val = diff
                if min_val < old_min:
                    ts_val = t

        return ts_val

    def data(self, timestep, spatial_context, prop):
        """ Returns spatial dataset for the specific timestep. Currently works for resolutions of hours """
        area_ts = self.area_propertyset[prop][0].loc[timestep].data

        # Get extent from the spatial context
        geoTransform = spatial_context.GetGeoTransform()

        min_x = geoTransform[0]
        max_y = geoTransform[3]

        mask = spatial_context.ReadAsArray()

        nr_cols = int(spatial_context.RasterXSize)
        nr_rows = int(spatial_context.RasterYSize)
        row_idx = round((self.yul - max_y) / self.cellsize_y)
        col_idx = round((min_x - self.xul) / self.cellsize_x)
        values = area_ts[row_idx: row_idx + nr_rows, col_idx: col_idx + nr_cols]
        res = np.where(mask == 1, values, np.nan)

        shape_x, shape_y = res.shape

        assert shape_x == spatial_context.RasterYSize, f"{shape_x} {shape_y} {spatial_context.RasterXSize} {spatial_context.RasterYSize}"
        assert shape_y == spatial_context.RasterXSize, f"{shape_x} {shape_y} {spatial_context.RasterXSize} {spatial_context.RasterYSize}"
        assert shape_x > 0
        assert shape_y > 0

        return res

    def epsg(self):
        """ Returns epsg code of the dataset"""
        pass

    def extent(self):
        """ Returns spatial extent """
        return self.xul, self.yul, self.xlr, self.ylr, self.cellsize_x, self.cellsize_y, self.nr_rows, self.nr_cols

    def _discretization(self):
        """ Returns spatial discretization """
        pass

    def _timestep_to_timebox_index(self, timestep):
        """ Returns the timebox index for specific time step """
        pass
