import argparse

from python.weekly_exposure import Weekly
from python.csv_export import to_csv
import config


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("realisations", type=int)
    args = parser.parse_args()

    realisations = args.realisations

    Weekly(config.output_dir, "weekly_homemaker", realisations, [[5, f"homemaker_buffer_workday_OD10000", True], [2, f"homemaker_buffer_weekend_OD10000", True]], config.output_dir)
    Weekly(config.output_dir, "weekly_commuter", realisations, [[5, f"commute_workday_OD01", True], [2, f"homemaker_buffer_weekend_OD10000", True]], config.output_dir)

    to_csv("no2", config.output_dir, ["weekly_homemaker", "weekly_commuter"])
    to_csv("pm25", config.output_dir, ["weekly_homemaker", "weekly_commuter"])
    to_csv("noise", config.output_dir, ["weekly_homemaker", "weekly_commuter"])
