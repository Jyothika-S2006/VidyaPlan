import urllib.request, json
from urllib.error import HTTPError

req = urllib.request.Request(
    'http://localhost:8000/api/copilot',
    json.dumps({'instruction': 'what if budget drops 30 percent', 'budget': 5000000}).encode(),
    {'Content-Type': 'application/json'}
)
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print("OK:", r.read().decode())
except HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode())
