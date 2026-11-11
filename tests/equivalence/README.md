# Equivalence checks

Scripts used to compare a patched build of QGIS Server with the unpatched build of the same source.

| Script | What it does |
| --- | --- |
| `equiv_services.py` | Sends 59 kinds of requests to two running servers and compares the responses |
| `equiv_raster.py` | Renders 68 raster cases and prints a hash of the pixels of each; run it with both builds and compare the output |
| `time_server_request.py` | Times one request handled in-process; under callgrind it profiles the steady state only |

They run inside a container with the Python bindings of the build under test. `equiv_services.py` expects
both servers to serve the same project with PostGIS layers, two rasters, a cascaded WMS layer, published WFS,
WCS and WMTS and one print layout; `equiv_raster.py` uses the test data of the QGIS source tree. The stack
which provides the project, the data and the load tests is not published yet.
