import datetime
import os.path
import pickle
import sys

import googlemaps
import argparse
import json
import hashlib
import logging


class ApiKeys:
    maps = ""


# Init logger
logger = logging.getLogger("WorkTransit")
logger.setLevel(logging.DEBUG)
logSh = logging.StreamHandler(stream=sys.stdout)
logSh.setLevel(logging.ERROR)
logger.addHandler(logSh)

# Load parameters
parser = argparse.ArgumentParser()
parser.add_argument('--from', dest="dest", type=str, required=True)
parser.add_argument('--to', dest="src", type=str, required=True)
parser.add_argument('--start', type=str)
parser.add_argument('--stop', type=str)
parser.add_argument('--period', type=str)
parser.add_argument('--output-folder', dest="output_path", type=str)
args = parser.parse_args()

# Handle output-folder immediately
default_output_folder = "output"
output_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), default_output_folder)
if args.output_path and len(args.output_path) != 0:
    output_path = os.path.abspath(args.output_path)

os.makedirs(output_path, exist_ok=True)
logFmt = logging.Formatter(fmt="%(asctime)s - [%(levelname)s] : %(message)s", datefmt="%Y/%m/%d %H:%M:%S")
logFh = logging.FileHandler(os.path.join(output_path, "logs.txt"))
logFh.setFormatter(logFmt)
logFh.setLevel(logging.DEBUG)
logger.addHandler(logFh)

logger.info(f"Parameters {args}")

# Check parameters
has_error = False
if len(args.dest) == 0:
    logger.error(f"Invalid args, `from` is empty: {args.dest}")
    has_error = True
if len(args.src) == 0:
    logger.error(f"Invalid args, `to` is empty: {args.src}")
    has_error = True

time_format = "%H:%M"
time_now = datetime.datetime.now()
if args.start:
    start = datetime.datetime.strptime(args.start, time_format)
    time_start = datetime.datetime(time_now.year, time_now.month, time_now.day, start.hour, start.minute)
    if time_start > time_now:
        logger.debug(f"Outside working hours, exiting")
        exit(0)

if args.stop:
    start = datetime.datetime.strptime(args.stop, time_format)
    time_stop = datetime.datetime(time_now.year, time_now.month, time_now.day, start.hour, start.minute)
    if time_stop < time_now:
        logger.debug(f"Outside working hours, exiting")
        exit(0)

pickle_rawname = args.dest + args.src
pickle_filename = f"{hashlib.sha1(pickle_rawname.encode('utf-8')).hexdigest()}.pkl"
pickle_path = os.path.abspath(os.path.join(os.curdir, pickle_filename))
if args.period:
    period = datetime.datetime.strptime(args.period, '%M:%S')
    time_last = datetime.datetime.fromtimestamp(0)
    if os.path.exists(pickle_path):
        with open(pickle_path, 'rb') as f:
            time_last = pickle.load(f)
    time_span = time_now - time_last
    exhausted = time_span < datetime.timedelta(seconds=period.second, minutes=period.minute)
    if exhausted:
        logger.debug(f"Still in processed period, exiting")
        exit(0)

if has_error:
    exit(-1)

# Load API Keys
keys = ApiKeys()
with open('keys.json', 'r') as f:
    jsonObj = json.load(f)
    keys.maps = jsonObj["google-maps"]
    if not isinstance(keys.maps, str):
        exit(-1)
    if len(keys.maps) == 0:
        exit(-1)

# Run maps
try:
    gmaps = googlemaps.Client(key=keys.maps)
except ValueError as e:
    logger.error(e)
    exit(-1)

output_rawname = args.dest + args.src + str(time_now)
output_filename = hashlib.sha1(output_rawname.encode("utf-8")).hexdigest()
output_file_path = os.path.join(output_path, f"{output_filename}.json")
with open(output_file_path, "w") as output:
    routes = dict()
    traffic_models = ["best_guess", "optimistic", "pessimistic"]
    for traffic_model in traffic_models:
        routes[traffic_model] = gmaps.directions(origin=args.src, destination=args.dest,
                                                 departure_time=datetime.datetime.now(),
                                                 traffic_model=traffic_model)
    output.write(str(routes))

with open(pickle_path, 'wb+') as f:
    pickle.dump(datetime.datetime.now(), f)

logger.info("Success, exiting")
