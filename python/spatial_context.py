import math
import numpy as np

from osgeo import gdal, osr

import python.routing as mar

from python.actgen.config import CommuteType


gdal.UseExceptions()


class SpatialContext(object):
    def __init__(self, routing_engine, geotransform, epsg):
        self.round_digits = 4
        self.r = routing_engine

        self.epsg = epsg
        self.proj = osr.SpatialReference()
        self.proj.ImportFromEPSG(self.epsg)

        self.min_x = round(geotransform[0], self.round_digits)
        self.max_x = round(geotransform[2], self.round_digits)
        self.max_y = round(geotransform[1], self.round_digits)
        self.min_y = round(geotransform[3], self.round_digits)

        self.cellsize = round(geotransform[4], self.round_digits)
        self.cellsize_y = round(geotransform[5], self.round_digits)

        self.nr_rows = geotransform[6]
        self.nr_cols = geotransform[7]

        # options for reprojecting the WGS84 route to the target CRS
        self.vectortranslateoptions = gdal.VectorTranslateOptions(
            format="MEMORY",
            srcSRS="EPSG:4326",
            dstSRS=self.proj,
            reproject=True,
            layers="route"
        )

    def _coord_to_rc(self, xcoord, ycoord):
        assert xcoord >= self.min_x, f"{xcoord} / {self.min_x}"
        assert xcoord <= self.max_x, f"{xcoord} / {self.max_x}"
        assert ycoord >= self.min_y, f"{ycoord} / {self.min_y}"
        assert ycoord <= self.max_y, f"{ycoord} / {self.max_y}"

        row = int((ycoord - self.max_y) / -self.cellsize_y)
        col = int((xcoord - self.min_x) / self.cellsize)

        assert row >= 0, f"{row} / {self.nr_rows}"
        assert row < self.nr_rows, f"{row} / {self.nr_rows}"
        assert col >= 0, f"{col} / {self.nr_cols}"
        assert col < self.nr_cols, f"{col} / {self.nr_cols}"

        return row, col

    def _snap(self, minX, maxX, minY, maxY):
        """ Returns spatial extent matching to the base raster
        """

        assert self.min_x is not None
        row_min, col_min = self._coord_to_rc(minX, maxY)
        row_max, col_max = self._coord_to_rc(maxX, minY)

        new_nr_rows = max(1, abs(row_min - row_max))
        new_nr_cols = max(1, abs(col_max - col_min))

        new_min_x = round(self.min_x + self.cellsize * col_min, self.round_digits)
        new_max_x = round(self.min_x + self.cellsize * col_max + self.cellsize, self.round_digits)

        new_max_y = round(self.max_y - self.cellsize_y * row_min, self.round_digits)
        new_min_y = round(self.max_y - self.cellsize_y * row_max - self.cellsize_y, self.round_digits)

        new_nr_rows = max(1, abs(new_max_y - new_min_y) / self.cellsize_y)
        new_nr_cols = max(1, abs(new_max_x - new_min_x) / self.cellsize)

        assert new_min_x <= minX, f"{new_min_x} {minX}"
        assert new_max_x >= maxX, f"{new_max_x} {maxX}"
        assert new_max_y >= maxY, f"{new_max_y} {maxY}"
        assert new_min_y <= minY, f"{new_min_y} {minY}"
        assert new_nr_rows >= 0
        assert new_nr_cols >= 0
        assert new_nr_rows < self.nr_rows
        assert new_nr_cols < self.nr_cols
        assert new_min_x >= self.min_x
        assert new_max_x <= self.max_x
        assert new_min_y >= self.min_y
        assert new_max_y <= self.max_y

        return new_min_x, new_max_x, new_min_y, new_max_y, int(new_nr_rows), int(new_nr_cols)

    def point(self, xcoord, ycoord, crs=None):
        """ Spatial context of a point coordinate
        """
        if crs is not None:
            raise NotImplementedError

        return self.buffer(xcoord, ycoord, 0, crs)

    def buffer(self, xcoord, ycoord, buffer_size, crs=None):
        """ Returns spatial context and mask of a buffered coordinate
        """
        assert buffer_size >= 0

        if crs is not None:
            raise NotImplementedError

        bsize_cells = ""

        if buffer_size == 0:
            # Spatial context of a point coordinate (ie return raster cell)
            env_minX = xcoord - self.cellsize / 2.0
            env_maxX = xcoord + self.cellsize / 2.0
            env_minY = ycoord - self.cellsize / 2.0
            env_maxY = ycoord + self.cellsize / 2.0
            rows = 1
            cols = 1
            env_minX, env_maxX, env_minY, env_maxY, rows, cols = self._snap(xcoord, xcoord, ycoord, ycoord)
            assert rows == 1
            assert cols == 1
            array = np.ones((rows, cols), dtype=np.int32)
        else:
            # Spatial context of a buffer
            bsize, remainder = divmod(buffer_size, self.cellsize)
            env_minX, env_maxX, env_minY, env_maxY, rows, cols = self._snap(xcoord, xcoord, ycoord, ycoord)

            # Create buffer mask
            bsize_cells, remainder = divmod(math.fabs(buffer_size / self.cellsize), 1)
            bsize_cells = int(bsize_cells)

            assert rows == cols

            y, x = np.ogrid[-bsize_cells: bsize_cells + 1, -bsize_cells: bsize_cells + 1]
            mask = x * x + y * y <= bsize_cells * bsize_cells
            array = mask.astype(np.int32)

            # Correct extent
            rows, cols = array.shape
            multiplier = (rows - 1) / 2
            env_minX = env_minX - multiplier * self.cellsize
            env_maxX = env_maxX + multiplier * self.cellsize
            env_minY = env_minY - multiplier * self.cellsize
            env_maxY = env_maxY + multiplier * self.cellsize

        target_ds = gdal.GetDriverByName('MEM').Create('', xsize=cols, ysize=rows, bands=1, eType=gdal.GDT_Byte)
        target_ds.SetGeoTransform((env_minX, self.cellsize, 0, env_maxY, 0, -self.cellsize_y))
        target_ds.SetProjection(self.proj.ExportToWkt())

        target_band = target_ds.GetRasterBand(1)
        target_band.WriteArray(array, 0, 0)
        target_band.FlushCache()

        return target_ds

    def route(self, xcoord1, ycoord1, xcoord2, ycoord2, travel_mode, crs=None):
        """ Returns rasterised route, matched to a base grid
        """
        if crs is None:
            raise NotImplementedError
        else:
            assert crs == 4326

        if travel_mode == CommuteType.bike.value:
            travel_type = mar.Bike
        elif travel_mode == CommuteType.car.value:
            travel_type = mar.Car
        elif travel_mode == CommuteType.train.value:
            travel_type = mar.Train
        elif travel_mode == CommuteType.foot.value:
            travel_type = mar.Foot
        else:
            raise NotImplementedError

        points = self.r.route(xcoord1, ycoord1, xcoord2, ycoord2, travel_type)

        coordinates = str(points)
        coordinates = coordinates.replace("(", "[")
        coordinates = coordinates.replace(")", "]")

        # Make coordinate list suitable for GDAL
        content = \
            """{
"type": "FeatureCollection",
"name": "route",
"features": [
{ "type": "Feature", "properties": { }, "geometry":
{ "type": "LineString", "coordinates":""" +\
            "{}".format(coordinates) +\
            """ } }
]
}
"""

        # Route to GDAL dataset, route is in wgs84
        ds = gdal.OpenEx(content)
        assert ds is not None, 'Failed to open datasource'

        # Reproject route to the target CRS
        mem_ds = gdal.VectorTranslate("", ds, options=self.vectortranslateoptions)

        # Determine target raster extent, start with current extent
        dst_layer = mem_ds.GetLayer()
        source_feature = dst_layer.GetNextFeature()
        env = source_feature.GetGeometryRef().GetEnvelope()
        env_minX, env_maxX, env_minY, env_maxY, rows, cols = self._snap(env[0], env[1], env[2], env[3])

        # Burn route into the raster
        target_ds = gdal.GetDriverByName('MEM').Create('', xsize=cols, ysize=rows, bands=1, eType=gdal.GDT_Byte)
        target_ds.SetGeoTransform((env_minX, self.cellsize, 0, env_maxY, 0, -self.cellsize))
        target_ds.SetProjection(self.proj.ExportToWkt())

        gdal.RasterizeLayer(target_ds, [1], dst_layer, burn_values=[1], options=['ALL_TOUCHED=TRUE'])

        return target_ds
