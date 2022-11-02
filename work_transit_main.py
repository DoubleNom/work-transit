import datetime
import os.path
import pickle
import googlemaps
import argparse
import json
import hashlib
import logging
from systemd.journal import JournalHandler


class ApiKeys:
    maps = ""

# Init logger
log = logging.getLogger("WorkTransit")
log.addHandler(JournalHandler())
log.setLevel(logging.INFO)

# Load parameters
parser = argparse.ArgumentParser()
parser.add_argument('--from', dest="dest", type=str, required=True)
parser.add_argument('--to', dest="src", type=str, required=True)
parser.add_argument('--start', type=str, required=True)
parser.add_argument('--stop', type=str, required=True)
parser.add_argument('--period', type=str, required=True)
parser.add_argument('--output-folder', type=str, required=True)
args = parser.parse_args()

# Check parameters
has_error = False
if len(args.dest) == 0:
    log.error(f"Invalid args, `from` is empty: {args.dest}")
    has_error = True
if len(args.src) == 0:
    log.error(f"Invalid args, `to` is empty: {args.src}")
    has_error = True

if has_error:
    exit(-1)


# Check if allowed to run
pickle_rawname = args.dest + args.src
pickle_filename = hashlib.sha1(pickle_rawname.encode("utf-8")).hexdigest()
now = datetime.datetime.now()
last = datetime.datetime.fromtimestamp(0)
if os.path.exists(pickle_filename):
    with open(pickle_filename, 'r') as f:
        last = pickle.load(f)

# if (last - now < args.period):
#     exit(0)


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
gmaps = googlemaps.Client(key=keys.maps)
route = gmaps.directions(origin=args.src, destination=args.dest, departure_time=datetime.datetime.now())
print(route)