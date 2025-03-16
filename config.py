import pathlib


work_dir = pathlib.Path().cwd()


# Path to the output directory
output_dir = pathlib.Path(work_dir, "results")

# Path to the input directory
input_dir = pathlib.Path(work_dir, "input_data")

# Routing
osrm_car = str(pathlib.Path(input_dir, "osm", "nl_car.osrm"))
osrm_bike = str(pathlib.Path(input_dir, "osm", "nl_bicycle.osrm"))
osrm_foot = str(pathlib.Path(input_dir, "osm", "nl_foot.osrm"))
osrm_train = str(pathlib.Path(input_dir, "osm", "nl_train.osrm"))

building_db = str(pathlib.Path(input_dir, "utrecht_province.sqlite3"))
pollutant_db = str(pathlib.Path(input_dir, "nl_ap_noise.lue"))

workday = ["NO2_hour_weekday", "PM25_hour_weekday", "noise"]
weekend = ["NO2_hour_weekend", "PM25_hour_weekend", "noise"]

epsg = 28992
inmem_schedules = True

query_work_table = "work"
query_work_select = "idx AS agent_id,postcode2 as postcode,rd_x AS work_x,rd_y as work_y,wgs_x,wgs_y"
query_work_where = ""

query_home_table = "home"
query_home_select = "idx AS agent_id,postcode2 AS postcode,rd_x AS home_x,rd_y AS home_y,wgs_x,wgs_y"
query_home_where = ""
# Comment or modify if you want to run more agents
query_home_where = "idx<1000"
