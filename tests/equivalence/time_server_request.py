"""Time (or profile under callgrind) one request handled in-process by QgsServer.

Usage: python3 time_server_request.py <project> <warm up count> <count> <query string>
Prints the handling time of the repetitions after the warm up.
With CALLGRIND=1 the instrumentation is switched on after the warm up (run valgrind with --instr-atstart=no),
so the profile holds <count> steady state requests and nothing else.
"""

import os
import subprocess
import sys
import time

from qgis.core import QgsApplication, QgsProject
from qgis.server import QgsBufferServerRequest, QgsBufferServerResponse, QgsServer

app = QgsApplication([], False)
app.initQgis()
server = QgsServer()
project = QgsProject()
assert project.read(sys.argv[1])
warm, count, query = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
url = "http://localhost/" + (query[1:] if query.startswith("/") else "?" + query)


def handle():
    response = QgsBufferServerResponse()
    t = time.perf_counter()
    server.handleRequest(QgsBufferServerRequest(url), response, project)
    return time.perf_counter() - t, response


for _ in range(warm):
    handle()
if os.environ.get("CALLGRIND"):
    subprocess.run(["callgrind_control", "-i", "on", str(os.getpid())], check=True, stdout=subprocess.DEVNULL)
times = []
for _ in range(count):
    t, response = handle()
    times.append(t)
print(response.statusCode(), len(response.body()), "bytes; ms:", " ".join("%.1f" % (x * 1000) for x in times))
