import argparse
import datetime

from numpy.random import default_rng

import config


def do_profile(realisation, od_matrix=None):

    run_start = datetime.datetime.now()
    seed = None
    rng = default_rng(seed)

    profile = Profile(rng, realisation, od_matrix)

    profile.log(f"Starting realisation {realisation} with seed {seed}")

    t_start = datetime.datetime(2020, 7, 1, hour=0, minute=0)
    t_end = datetime.datetime(2020, 7, 2, hour=0, minute=0)
    t_delta = datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=1, hours=0, weeks=0)

    profile.init_time(t_start, t_end, t_delta, None)

    profile.generate_schedules()
    profile.enrich_schedules(config.pollutant_db, profile.exposure_variables(), config.epsg)
    profile.aggregate(profile.exposure_variables())

    run_end = datetime.datetime.now()
    run_diff = run_end - run_start
    profile.log(f"Successful run {realisation} took {run_diff}; {profile.nr_home_locations} agents; {run_diff / profile.nr_home_locations} per agent")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("profile", type=str)
    parser.add_argument("realisations", type=int)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--min", type=int, default=1)
    parser.add_argument("--arg", type=int)

    args = parser.parse_args()

    assert args.min < args.realisations + 1

    if args.profile == "homemaker_buffer_workday":
        from profiles import HomemakerBufferWorkday as Profile
    elif args.profile == "homemaker_buffer_weekend":
        from profiles import HomemakerBufferWeekend as Profile
    elif args.profile == "commuter_workday":
        from profiles import CommuteWorkday as Profile
    else:
        raise NotImplementedError(args.profile)

    do_profile(args.realisations, args.arg)
