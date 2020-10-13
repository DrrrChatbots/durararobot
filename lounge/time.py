import re, os, sys, json
from pprint import pprint

def isTarget(u, name, tripcode):
    utrip = str(u.get('tripcode'))
    if name: return name == u['name']
    if utrip and tripcode in utrip: return tripcode in utrip
    if name: return re.match(re.compile(name, re.IGNORECASE), u['name'])
    if utrip and tripcode: return re.match(re.compile(tripcode, re.IGNORECASE), utrip)

users = set()
times = list()

if len(sys.argv) <= 1:
    print('Usage: python {} [name | #tripcode]'.format(sys.argv[0]))
    print('tripcodes: #NinTend0 | #^Moon')
    exit(0)

files = [f for f in os.listdir('.') if os.path.isfile(f) and '.json' in f]
for fn in files:
    rooms = json.loads(open(fn).read())
    for room in rooms:
        for u in room['users']:
            for p in sys.argv[1:]:
                if p.startswith('#') and isTarget(u, None, p[1:]):
                    times.append(fn)
                    users.add((u['name'], u.get('tripcode', '')))
                elif isTarget(u, p, None):
                    times.append(fn)
                    users.add((u['name'], u.get('tripcode', '')))

times.sort()
for t in times: print(t)
for u in users: print(u)
