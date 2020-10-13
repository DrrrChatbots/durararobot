import sys, json
from pprint import pprint
for fn in sys.argv[1:]:
    pprint(json.loads(open(fn).read()))
